# -*- coding: utf-8 -*-
"""Base class for all FHIR elements. """
import abc
import logging
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

from pydantic import BaseModel
from pydantic.class_validators import make_generic_validator
from pydantic.errors import ConfigError

if TYPE_CHECKING:
    from pydantic.typing import AbstractSetIntStr, MappingIntStrAny, DictStrAny

__author__ = "Md Nazrul Islam<email2nazrul@gmail.com>"

logger = logging.getLogger(__name__)


class FHIRAbstractModel(BaseModel, abc.ABC):
    """ Abstract base model class for all FHIR elements.
    """
    resourceType: str = ...

    @classmethod
    def add_root_validator(
        cls,
        validator: Callable,
        *,
        pre: bool = False,
        skip_on_failure: bool = False,
        index: int = -1,
    ):
        """ """
        from inspect import signature
        from inspect import isfunction

        if not isfunction(validator):
            raise ConfigError(
                f"'{validator.__qualname__}' must be function not method from class."
            )
        sig = signature(validator)
        args = list(sig.parameters.keys())
        if args[0] != "cls":
            raise ConfigError(
                f"Invalid signature for root validator {validator.__qualname__}: {sig}, "
                f'"args[0]" not permitted as first argument, '
                f"should be: (cls, values)."
            )
        if len(args) != 2:
            raise ConfigError(
                f"Invalid signature for root validator {validator.__qualname__}: {sig}, "
                "should be: (cls, values)."
            )
        validator_ = make_generic_validator(validator)
        if pre:
            if validator_ not in cls.__pre_root_validators__:
                if index == -1:
                    cls.__pre_root_validators__.append(validator_)
                else:
                    cls.__pre_root_validators__.insert(index, validator_)
            return
        if validator_ in map(lambda x: x[1], cls.__post_root_validators__):
            return
        if index == -1:
            cls.__post_root_validators__.append((skip_on_failure, validator_))
        else:
            cls.__pre_root_validators__.insert(index, (skip_on_failure, validator_))

    def dict(
        self,
        *,
        include: Union["AbstractSetIntStr", "MappingIntStrAny"] = None,
        exclude: Union["AbstractSetIntStr", "MappingIntStrAny"] = None,
        by_alias: bool = None,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = None,
    ) -> "DictStrAny":
        """ """
        # xxx: do validation? if object changed
        if by_alias is None:
            by_alias = True

        if exclude_none is None:
            exclude_none = False

        return BaseModel.dict(
            self,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

    def json(
        self,
        *,
        include: Union["AbstractSetIntStr", "MappingIntStrAny"] = None,
        exclude: Union["AbstractSetIntStr", "MappingIntStrAny"] = None,
        by_alias: bool = None,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = None,
        encoder: Optional[Callable[[Any], Any]] = None,
        **dumps_kwargs: Any,
    ) -> str:
        """ """
        return BaseModel.json(
            self,
            include=include,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            encoder=encoder,
            **dumps_kwargs,
        )

    class Config:
        validate_assignment = True
        allow_population_by_field_name = True
