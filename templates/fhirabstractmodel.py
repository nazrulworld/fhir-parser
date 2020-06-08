# -*- coding: utf-8 -*-
"""Base class for all FHIR elements. """
import abc
import inspect
import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

from pydantic import BaseModel
from pydantic.errors import ConfigError

if TYPE_CHECKING:
    from pydantic.typing import AbstractSetIntStr, MappingIntStrAny, DictStrAny

__author__ = "Md Nazrul Islam<email2nazrul@gmail.com>"

logger = logging.getLogger(__name__)


class FHIRAbstractModel(BaseModel, abc.ABC):
    """ Abstract base model class for all FHIR elements.
    """

    resource_type: str = ...  # type: ignore

    def __init__(__pydantic_self__, **data: Any) -> None:
        """ """
        if "resource_type" in data:
            del data["resource_type"]

        if (
            "resourceType" in data
            and "resourceType" not in __pydantic_self__.__fields__
        ):
            if __pydantic_self__.__class__.__name__ not in ("Resource", "Element"):
                del data["resourceType"]

        BaseModel.__init__(__pydantic_self__, **data)

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
        if pre:
            if validator not in cls.__pre_root_validators__:
                if index == -1:
                    cls.__pre_root_validators__.append(validator)
                else:
                    cls.__pre_root_validators__.insert(index, validator)
            return
        if validator in map(lambda x: x[1], cls.__post_root_validators__):
            return
        if index == -1:
            cls.__post_root_validators__.append((skip_on_failure, validator))
        else:
            cls.__post_root_validators__.insert(index, (skip_on_failure, validator))

    @classmethod
    @lru_cache(maxsize=None, typed=True)
    def has_resource_base(cls) -> bool:
        """ """
        # xxx: calculate metrics, other than cache it!
        for cl in inspect.getmro(cls)[:-4]:
            if cl.__name__ == "Resource":
                return True
        return False

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
            exclude_none = True

        exclude_ = {"resource_type"}
        if isinstance(exclude, (list, tuple, set)):
            exclude_ = exclude_.union(exclude)

        result = BaseModel.dict(
            self,
            include=include,
            exclude=exclude_,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
        if self.__class__.has_resource_base():
            result["resourceType"] = self.resource_type
        return result

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
        if by_alias is None:
            by_alias = True

        if exclude_none is None:
            exclude_none = True

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
