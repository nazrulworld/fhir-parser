# _*_ coding: utf-8 _*_
from __future__ import annotations
from .fhirabstractmodel import FHIRAbstractModel
from pydantic.main import load_str_bytes
from pydantic.types import ConstrainedBytes
from pydantic.types import ConstrainedStr
from pydantic import AnyUrl
from pydantic.errors import StrRegexError
from pydantic.types import ConstrainedDecimal
from pydantic.types import ConstrainedInt
from pydantic.typing import AnyCallable
from typing import Union
from typing import List
from pydantic.class_validators import make_generic_validator
from typing import TYPE_CHECKING
from uuid import UUID
import datetime
from typing import Dict
from typing import Any
from pydantic.validators import bool_validator

import re

__author__ = "Md Nazrul Islam<email2nazrul@gmail.com>"

_CUSTOM_TYPE_VALIDATORS: Dict[str, List[AnyCallable]] = dict()


if TYPE_CHECKING:
    Boolean = bool
else:

    class Boolean(int):
        """true | false"""

        regex: str = "true|false"
        __visit_name__ = "boolean"

        @classmethod
        def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
            field_schema.update(type="boolean")

        @classmethod
        def __get_validators__(cls) -> "CallableGenerator":
            yield bool_validator


class String(ConstrainedStr):
    """A sequence of Unicode characters
    Note that strings SHALL NOT exceed 1MB (1024*1024 characters) in size.
    Strings SHOULD not contain Unicode character points below 32, except for
    u0009 (horizontal tab), u0010 (carriage return) and u0013 (line feed).
    Leading and Trailing whitespace is allowed, but SHOULD be removed when using
    the XML format. Note: This means that a string that consists only of whitespace
    could be trimmed to nothing, which would be treated as an invalid element value.
    Therefore strings SHOULD always contain non-whitespace conten"""

    regex = re.compile("[ \r\n\t\S]+")
    __visit_name__ = "string"


class Base64Binary(ConstrainedBytes):
    """A stream of bytes, base64 encoded (RFC 4648 )"""

    regex = re.compile(b"(\s*([0-9a-zA-Z\+\=]){4}\s*)+")
    __visit_name__ = "base64Binary"

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield from ConstrainedBytes.__get_validators__()
        yield cls.validate

    @classmethod
    def validate(cls, value: bytes) -> bytes:
        if cls.regex.match(value):
            return value
        raise StrRegexError(pattern=cls.regex.pattern)


class Code(ConstrainedStr):
    """Indicates that the value is taken from a set of controlled
    strings defined elsewhere (see Using codes for further discussion).
    Technically, a code is restricted to a string which has at least one
    character and no leading or trailing whitespace, and where there is
    no whitespace other than single spaces in the contents"""

    regex = re.compile("[^\s]+(\s[^\s]+)*")
    __visit_name__ = "code"


class Id(ConstrainedStr):
    """Any combination of upper- or lower-case ASCII letters
    ('A'..'Z', and 'a'..'z', numerals ('0'..'9'), '-' and '.', with a length limit of 64 characters.
    (This might be an integer, an un-prefixed OID, UUID or any other identifier
    pattern that meets these constraints.)
    """

    regex = re.compile("[A-Za-z0-9\-\.]{1,64}")
    min_length = 1
    max_length = 64
    __visit_name__ = "id"


class Decimal(ConstrainedDecimal):
    """Rational numbers that have a decimal representation.
    See below about the precision of the number"""

    regex = re.compile("-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?")
    __visit_name__ = "decimal"


class Integer(ConstrainedInt):
    """A signed integer in the range −2,147,483,648..2,147,483,647 (32-bit;
    for larger values, use decimal)"""

    regex = re.compile("[0]|[-+]?[1-9][0-9]*")
    __visit_name__ = "integer"


class UnsignedInt(ConstrainedInt):
    """Any non-negative integer in the range 0..2,147,483,647"""

    regex = re.compile("[0]|([1-9][0-9]*)")
    __visit_name__ = "unsignedInt"
    ge = 0


class PositiveInt(ConstrainedInt):
    """Any positive integer in the range 1..2,147,483,647"""

    regex = re.compile("\+?[1-9][0-9]*")
    __visit_name__ = "positiveInt"
    gt = 0


class Uri(ConstrainedStr):
    __visit_name__ = "uri"
    regex = re.compile("\S*")


class Oid(ConstrainedStr):
    __visit_name__ = "oid"
    regex = re.compile("urn:oid:[0-2](\.(0|[1-9][0-9]*))+")


class Uuid(UUID):
    """A UUID (aka GUID) represented as a URI (RFC 4122 );
    e.g. urn:uuid:c757873d-ec9a-4326-a141-556f43239520"""

    __visit_name__ = "uuid"
    regex = None


class Canonical(Uri):
    __visit_name__ = "canonical"


class Url(AnyUrl):
    regex = None
    __visit_name__ = "url"


class Markdown(ConstrainedStr):
    """A FHIR string (see above) that may contain markdown syntax for optional processing
    by a markdown presentation engine, in the GFM extension of CommonMark format (see below)"""

    __visit_name__ = "markdown"
    regex = re.compile("\s*(\S|\s)*")


class Xhtml(ConstrainedStr):
    regex = None
    __visit_name__ = "xhtml"


class Date(datetime.date):
    """A date, or partial date (e.g. just year or year + month)
    as used in human communication. The format is YYYY, YYYY-MM, or YYYY-MM-DD,
    e.g. 2018, 1973-06, or 1905-08-23.
    There SHALL be no time zone. Dates SHALL be valid dates"""

    regex = re.compile(
        "([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|"
        "[1-9]000)(-(0[1-9]|1[0-2])(-(0[1-9]|[1-2]"
        "[0-9]|3[0-1]))?)?"
    )
    __visit_name__ = "date"


class DateTime(datetime.datetime):
    """A date, date-time or partial date (e.g. just year or year + month) as used
    in human communication. The format is YYYY, YYYY-MM, YYYY-MM-DD or
    YYYY-MM-DDThh:mm:ss+zz:zz, e.g. 2018, 1973-06, 1905-08-23,
    2015-02-07T13:28:17-05:00 or 2017-01-01T00:00:00.000Z.
    If hours and minutes are specified, a time zone SHALL be populated.
    Seconds must be provided due to schema type constraints but may be
    zero-filled and may be ignored at receiver discretion.
    Dates SHALL be valid dates. The time "24:00" is not allowed.
    Leap Seconds are allowed - see below"""

    regex = re.compile(
        "([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|"
        "[1-9]000)(-(0[1-9]|1[0-2])(-(0[1-9]|[1-2][0-9]|"
        "3[0-1])(T([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|"
        "60)(\.[0-9]+)?(Z|(\+|-)((0[0-9]|"
        "1[0-3]):[0-5][0-9]|14:00)))?)?)?"
    )
    __visit_name__ = "dateTime"


class Instant(datetime.datetime):
    """An instant in time in the format YYYY-MM-DDThh:mm:ss.sss+zz:zz
    (e.g. 2015-02-07T13:28:17.239+02:00 or 2017-01-01T00:00:00Z).
    The time SHALL specified at least to the second and SHALL include a time zone.
    Note: This is intended for when precisely observed times are required
    (typically system logs etc.), and not human-reported times - for those,
    use date or dateTime (which can be as precise as instant,
    but is not required to be). instant is a more constrained dateTime

    Note: This type is for system times, not human times (see date and dateTime below)."""

    regex = re.compile(
        "([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|"
        "[1-9]000)-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|"
        "3[0-1])T([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]"
        "|60)(\.[0-9]+)?(Z|(\+|-)((0[0-9]|"
        "1[0-3]):[0-5][0-9]|14:00))"
    )
    __visit_name__ = "instant"


class Time(datetime.time):
    """A time during the day, in the format hh:mm:ss.
    There is no date specified. Seconds must be provided due
    to schema type constraints but may be zero-filled and may
    be ignored at receiver discretion.
    The time "24:00" SHALL NOT be used. A time zone SHALL NOT be present.
    Times can be converted to a Duration since midnight."""

    regex = re.compile("([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]+)?")
    __visit_name__ = "time"


def add_validator_for_fhir_type(
    type_name_or_model_name: str, validator: AnyCallable, index: int = -1
):
    """ """
    global _CUSTOM_TYPE_VALIDATORS
    try:
        cls = globals()[type_name_or_model_name]
    except KeyError:
        cls = get_fhir_type_class(type_name_or_model_name)

    if cls.__name__ not in _CUSTOM_TYPE_VALIDATORS:
        _CUSTOM_TYPE_VALIDATORS[cls.__name__] = list()

    if validator in _CUSTOM_TYPE_VALIDATORS[cls.__name__]:
        return
    if index == -1:
        _CUSTOM_TYPE_VALIDATORS[cls.__name__].append(validator)
    else:
        _CUSTOM_TYPE_VALIDATORS[cls.__name__].insert(index, validator)


def get_validator_for_fhir_type(
    type_name_or_model_name: str, default: Union[None, list] = None
):
    global _CUSTOM_TYPE_VALIDATORS
    try:
        cls = globals()[type_name_or_model_name]
    except KeyError:
        cls = get_fhir_type_class(type_name_or_model_name)
    return _CUSTOM_TYPE_VALIDATORS.get(cls.__name__, default)


def get_fhir_type_class(model_name):
    try:
        return globals()[model_name + "Type"]
    except KeyError:
        raise LookupError(f"'{__name__}.{model_name}Type' doesnt found.")


def run_validator_for_fhir_type(type_name, v):
    """ """
    cls = get_fhir_type_class(type_name)
    for validator in cls.__get_validators__:
        func = make_generic_validator(validator)
        v = func(v)
    return v


class AbstractType(dict):
    """ """

    __resource_type__ = ...

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(type=cls.__resource_type__)

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        from . import fhirtypesvalidators

        yield getattr(fhirtypesvalidators, cls.__resource_type__.lower() + "_validator")
        if get_validator_for_fhir_type(cls.__name__, None):
            yield from get_validator_for_fhir_type(cls.__name__)


class AbstractBaseType(dict):
    """ """

    __resource_type__ = ...

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(type=cls.__resource_type__)

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield AbstractBaseType.validate

    @classmethod
    def validate(cls, v):
        """ """
        if isinstance(v, (bytes, str)):
            input_data = load_str_bytes(v)
            resource_type = input_data.get("resourceType", None)
        elif isinstance(v, FHIRAbstractModel):
            resource_type = v.resourceType
        else:
            resource_type = v.get("resourceType", None)

        if resource_type is None:
            raise ValueError(
                "'resourceType' is required, when generic ElementType is used"
            )
        if resource_type == cls.__resource_type__:
            from . import fhirtypesvalidators

            v = getattr(
                fhirtypesvalidators, cls.__resource_type__.lower() + "_validator"
            )(v)
            return v
        v = run_validator_for_fhir_type(resource_type, v)
        return v


class ElementType(AbstractBaseType):
    __resource_type__ = "Element"


class ResourceType(AbstractBaseType):
    __resource_type__ = "Resource"


# ****************** Generated FHIR Model Types *********************
