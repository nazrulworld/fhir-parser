# _*_ coding: utf-8 _*_
"""Validators for ``pydantic`` Custom DataType"""
import importlib
from pathlib import Path
from typing import Union
from pydantic.types import StrBytes
from .fhirabstractmodel import FHIRAbstractModel

__author__ = "Md Nazrul Islam<email2nazrul@gmail.com>"
model_classes = {}


def get_fhir_model_class(model_name: str) -> FHIRAbstractModel:
    """
    """
    klass, module_name = model_classes[model_name]
    if klass is not None:
        return klass
    module = importlib.import_module(module_name, package=__package__)
    klass = getattr(module, model_name)
    model_classes[model_name] = (klass, module_name)
    return klass


def fhir_model_validator(model_name: str, v: Union[StrBytes, dict, FHIRAbstractModel]):
    """ """
    model_class = get_fhir_model_class(model_name)
    if isinstance(v, (str, bytes)):
        v = model_class.parse_raw(v)
    elif isinstance(v, Path):
        v = model_class.parse_file(v)
    elif isinstance(v, dict):
        v = model_class.parse_obj(v)
    if not isinstance(v, FHIRAbstractModel):
        raise ValueError()
    if model_class.resourceType != v.resourceType:
        raise ValueError
    return v

