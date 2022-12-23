# _*_ coding: utf-8 _*_
import datetime
import decimal
import re
from email.utils import formataddr, parseaddr
from typing import TYPE_CHECKING, Any, Dict, Optional, Pattern, Union
from uuid import UUID

from pydantic import AnyUrl
from pydantic.errors import ConfigError, DateError, DateTimeError, TimeError
from pydantic.main import load_str_bytes
from pydantic.networks import validate_email
from pydantic.types import (
    ConstrainedBytes,
    ConstrainedDecimal,
    ConstrainedInt,
    ConstrainedStr,
)
from pydantic.validators import bool_validator, parse_date, parse_datetime, parse_time

from fhir.resources.core.fhirabstractmodel import FHIRAbstractModel

from .fhirtypesvalidators import run_validator_for_fhir_type

if TYPE_CHECKING:
    from pydantic.types import CallableGenerator
    from pydantic.fields import ModelField
    from pydantic import BaseConfig

__author__ = "Md Nazrul Islam<email2nazrul@gmail.com>"

FHIR_DATE_PARTS = re.compile(r"(?P<year>\d{4})(-(?P<month>\d{2}))?(-(?P<day>\d{2}))?$")
FHIR_PRIMITIVES = [
    "boolean",
    "string",
    "base64Binary",
    "code",
    "id",
    "decimal",
    "integer",
    "unsignedInt",
    "positiveInt",
    "uri",
    "oid",
    "uuid",
    "canonical",
    "url",
    "markdown",
    "xhtml",
    "date",
    "dateTime",
    "instant",
    "time",
]


class Primitive:
    """FHIR Primitive Data Type Base Class"""

    __fhir_release__: str = "R4B"
    __visit_name__: Optional[str] = None
    regex: Optional[Pattern[str]] = None

    @classmethod
    def is_primitive(cls) -> bool:
        """ """
        return True

    @classmethod
    def fhir_type_name(cls) -> Optional[str]:
        """ """
        return cls.__visit_name__


if TYPE_CHECKING:
    Boolean = bool
else:

    class Boolean(int, Primitive):
        """true | false"""

        regex = re.compile("true|false")
        __visit_name__ = "boolean"

        @classmethod
        def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
            field_schema.update(type="boolean")

        @classmethod
        def __get_validators__(cls) -> "CallableGenerator":
            yield bool_validator

        @classmethod
        def to_string(cls, value):
            """ """
            assert isinstance(value, bool)
            return value is True and "true" or "false"


class String(ConstrainedStr, Primitive):
    """A sequence of Unicode characters
    Note that strings SHALL NOT exceed 1MB (1024*1024 characters) in size.
    Strings SHOULD not contain Unicode character points below 32, except for
    u0009 (horizontal tab), u0010 (carriage return) and u0013 (line feed).
    Leading and Trailing whitespace is allowed, but SHOULD be removed when using
    the XML format. Note: This means that a string that consists only of whitespace
    could be trimmed to nothing, which would be treated as an invalid element value.
    Therefore strings SHOULD always contain non-whitespace content"""

    regex = re.compile(r"[ \r\n\t\S]+")
    allow_empty_str = False
    __visit_name__ = "string"

    @classmethod
    def configure_empty_str(cls, allow: bool = None):
        """About empty string
        1. https://bit.ly/3woGnFG
        2. https://github.com/nazrulworld/fhir.resources/issues/65#issuecomment-856693256
        There are a lot of valid discussion about accept empty string as String value but
        it is cleared for us that according to FHIR Specification, empty string is not valid!
        However in real use cases, we see empty string is coming other (when the task is related
        to query data from other system)

        It is in your hand now, if you would like to allow empty string! by default empty string is not
        accepted.
        """
        if isinstance(allow, bool):
            cls.allow_empty_str = allow

    @classmethod
    def validate(cls, value: Union[str]) -> Union[str]:
        if cls.allow_empty_str is True and value in ("", ""):
            return value
        # do the default things
        return ConstrainedStr.validate.__func__(cls, value)

    @classmethod
    def to_string(cls, value):
        """ """
        if isinstance(value, bytes):
            value = value.decode()
        elif value is None:
            value = ""
        assert isinstance(value, str)
        return value


class Base64Binary(ConstrainedBytes, Primitive):
    """A stream of bytes, base64 encoded (RFC 4648 )"""

    regex = re.compile(r"^(\s*([0-9a-zA-Z+=]){4}\s*)+$")
    __visit_name__ = "base64Binary"

    @classmethod
    def to_string(cls, value):
        """ """
        assert isinstance(value, bytes)
        return value.decode()


class Code(ConstrainedStr, Primitive):
    """Indicates that the value is taken from a set of controlled
    strings defined elsewhere (see Using codes for further discussion).
    Technically, a code is restricted to a string which has at least one
    character and no leading or trailing whitespace, and where there is
    no whitespace other than single spaces in the contents"""

    regex = re.compile(r"^[^\s]+(\s[^\s]+)*$")
    __visit_name__ = "code"

    @classmethod
    def to_string(cls, value):
        """ """
        if isinstance(value, bytes):
            value = value.decode()
        assert isinstance(value, str)
        return value


class Id(ConstrainedStr, Primitive):
    """Any combination of upper- or lower-case ASCII letters
    ('A'..'Z', and 'a'..'z', numerals ('0'..'9'), '-' and '.',
    with a length limit of 64 characters.
    (This might be an integer, an un-prefixed OID, UUID or any other identifier
    pattern that meets these constraints.)

    But it is possible to change the default behaviour by using configure_constraints()
    method!
    """

    regex = re.compile(r"^[A-Za-z0-9\-.]+$")
    min_length = 1
    max_length = 64
    __visit_name__ = "id"

    @classmethod
    def configure_constraints(
        cls, min_length: int = None, max_length: int = None, regex: Pattern = None
    ):
        """There are a lots of discussion about ``Resource.Id`` length of value.
            1. https://bit.ly/360HksL
            2. https://bit.ly/3o1fZgl
        We see there is some agreement and disagreement, because of that we decide to make
        it more flexible. Now it is possible configure three types of constraints.
        """
        if min_length is not None:
            if min_length < 1:
                raise ConfigError("Minimum length must be more than 0.")
            _max_check = max_length or cls.max_length
            if min_length > _max_check:
                raise ConfigError(
                    "Minimum length value cannot be greater than maximum value."
                )
            cls.min_length = min_length

        if max_length is not None:
            if max_length < 1:
                raise ConfigError("Maximum length must be more than 0.")
            _min_check = min_length or cls.min_length
            if max_length < _min_check:
                raise ConfigError(
                    "Maximum length value cannot be less than minimum value."
                )
            cls.max_length = max_length

        if regex is not None:
            cls.regex = regex

    @classmethod
    def to_string(cls, value):
        """ """
        if isinstance(value, bytes):
            value = value.decode()
        assert isinstance(value, str)
        return value


class Decimal(ConstrainedDecimal, Primitive):
    """Rational numbers that have a decimal representation.
    See below about the precision of the number"""

    regex = re.compile(r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?$")
    __visit_name__ = "decimal"

    @classmethod
    def to_string(cls, value):
        """ """
        assert isinstance(value, decimal.Decimal)
        return str(float(value))


class Integer(ConstrainedInt, Primitive):
    """A signed integer in the range −2,147,483,648..2,147,483,647 (32-bit;
    for larger values, use decimal)"""

    regex = re.compile(r"^[0]|[-+]?[1-9][0-9]*$")
    __visit_name__ = "integer"

    @classmethod
    def to_string(cls, value):
        """ """
        assert isinstance(value, int)
        return str(value)


class UnsignedInt(ConstrainedInt, Primitive):
    """Any non-negative integer in the range 0..2,147,483,647"""

    regex = re.compile(r"^[0]|([1-9][0-9]*)$")
    __visit_name__ = "unsignedInt"
    ge = 0

    @classmethod
    def to_string(cls, value):
        """ """
        assert isinstance(value, int)
        return str(value)


class PositiveInt(ConstrainedInt, Primitive):
    """Any positive integer in the range 1..2,147,483,647"""

    regex = re.compile(r"^\+?[1-9][0-9]*$")
    __visit_name__ = "positiveInt"
    gt = 0

    @classmethod
    def to_string(cls, value):
        """ """
        assert isinstance(value, int)
        return str(value)


class Uri(ConstrainedStr, Primitive):
    """A Uniform Resource Identifier Reference (RFC 3986 ).
    Note: URIs are case sensitive.
    For UUID (urn:uuid:53fefa32-fcbb-4ff8-8a92-55ee120877b7)
    use all lowercase xs:anyURI A JSON string - a URI
    Regex: \\S* (This regex is very permissive, but URIs must be valid.
    Implementers are welcome to use more specific regex statements
    for a URI in specific contexts)
    URIs can be absolute or relative, and may have an optional fragment identifier
    This data type can be bound to a ValueSet"""

    __visit_name__ = "uri"
    regex = re.compile(r"\S*")

    @classmethod
    def to_string(cls, value):
        """ """
        if isinstance(value, bytes):
            value = value.decode()
        assert isinstance(value, str)
        return value


class Oid(ConstrainedStr, Primitive):
    """An OID represented as a URI (RFC 3001 ); e.g. urn:oid:1.2.3.4.5"""

    __visit_name__ = "oid"
    regex = re.compile(r"^urn:oid:[0-2](\.(0|[1-9][0-9]*))+$")

    @classmethod
    def to_string(cls, value):
        """ """
        if isinstance(value, bytes):
            value = value.decode()
        assert isinstance(value, str)
        return value


class Uuid(UUID, Primitive):
    """A UUID (aka GUID) represented as a URI (RFC 4122 );
    e.g. urn:uuid:c757873d-ec9a-4326-a141-556f43239520"""

    __visit_name__ = "uuid"
    regex = None

    @classmethod
    def to_string(cls, value):
        """ """
        if isinstance(value, UUID):
            value = f"urn:uuid:{value}"
        assert isinstance(value, str)
        return value


class Canonical(Uri):
    """A URI that refers to a resource by its canonical URL (resources with a url property).
    The canonical type differs from a uri in that it has special meaning in this specification,
    and in that it may have a version appended, separated by a vertical bar (|).
    Note that the type canonical is not used for the actual canonical URLs that are
    the target of these references, but for the URIs that refer to them, and may have
    the version suffix in them. Like other URIs, elements of type canonical may also have
    #fragment references"""

    __visit_name__ = "canonical"

    @classmethod
    def to_string(cls, value):
        """ """
        if isinstance(value, bytes):
            value = value.decode()
        assert isinstance(value, str)
        return value


class Url(AnyUrl, Primitive):
    """A Uniform Resource Locator (RFC 1738 ).
    Note URLs are accessed directly using the specified protocol.
    Common URL protocols are http{s}:, ftp:, mailto: and mllp:,
    though many others are defined"""
    path_regex = re.compile(r'^/(?P<resourceType>[^\s?/]+)(/[^\s?/]+)*')
    __visit_name__ = "url"

    @classmethod
    def validate(  # type: ignore
        cls, value: str, field: "ModelField", config: "BaseConfig"
    ) -> Union["AnyUrl", str]:
        """ """
        if value.startswith("mailto:"):
            schema = value[0:7]
            email = value[7:]
            realname = parseaddr(email)[0]
            name, email = validate_email(email)
            if realname:
                email = formataddr((name, email))
            return schema + email
        elif value.startswith("mllp:") or value.startswith("llp:"):
            # xxx: find validation
            return value
        elif value in FHIR_PRIMITIVES:
            # Extensions may contain a valueUrl for a primitive FHIR type
            return value

        # we are allowing relative path
        matched = cls.path_regex.match(value)
        if matched is not None:
            # @ToDo: required resource type validation?
            # fx: resource type = matched.groupdict().get("resourceType")
            return value

        return AnyUrl.validate(value, field, config)

    @classmethod
    def to_string(cls, value):
        """ """
        if isinstance(value, bytes):
            value = value.decode()
        assert isinstance(value, str)
        return value


class Markdown(ConstrainedStr, Primitive):
    """A FHIR string (see above) that may contain markdown syntax for optional processing
    by a markdown presentation engine, in the GFM extension of CommonMark format (see below)"""

    __visit_name__ = "markdown"
    regex = re.compile(r"\s*(\S|\s)*")

    @classmethod
    def to_string(cls, value):
        """ """
        if isinstance(value, bytes):
            value = value.decode()
        assert isinstance(value, str)
        return value


class Xhtml(ConstrainedStr, Primitive):
    __visit_name__ = "xhtml"

    @classmethod
    def to_string(cls, value):
        """ """
        if isinstance(value, bytes):
            value = value.decode()
        assert isinstance(value, str)
        return value


class Date(datetime.date, Primitive):
    """A date, or partial date (e.g. just year or year + month)
    as used in human communication. The format is YYYY, YYYY-MM, or YYYY-MM-DD,
    e.g. 2018, 1973-06, or 1905-08-23.
    There SHALL be no time zone. Dates SHALL be valid dates"""

    regex = re.compile(
        r"([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|"
        r"[1-9]000)(-(0[1-9]|1[0-2])(-(0[1-9]|[1-2]"
        r"[0-9]|3[0-1]))?)?"
    )
    __visit_name__ = "date"

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":

        yield cls.validate

    @classmethod
    def validate(
        cls, value: Union[datetime.date, str, bytes, int, float]
    ) -> Union[datetime.date, str]:
        """ """
        if not isinstance(value, str):
            # default handler
            return parse_date(value)

        match = FHIR_DATE_PARTS.match(value)

        if not match:
            if not cls.regex.match(value):
                raise DateError()
        elif not match.groupdict().get("day"):
            if match.groupdict().get("month") and int(match.groupdict()["month"]) > 12:
                raise DateError()
            # we keep original
            return value
        return parse_date(value)

    @classmethod
    def to_string(cls, value):
        """ """
        if isinstance(value, (datetime.date, datetime.time, datetime.datetime)):
            value = value.isoformat()
        assert isinstance(value, str)
        return value


class DateTime(datetime.datetime, Primitive):
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
        r"([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|"
        r"[1-9]000)(-(0[1-9]|1[0-2])(-(0[1-9]|[1-2][0-9]|"
        r"3[0-1])(T([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|"
        r"60)(\.[0-9]+)?(Z|([+\-])((0[0-9]|"
        r"1[0-3]):[0-5][0-9]|14:00)))?)?)?"
    )
    __visit_name__ = "dateTime"

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":

        yield cls.validate

    @classmethod
    def validate(
        cls, value: Union[datetime.date, datetime.datetime, str, bytes, int, float]
    ) -> Union[datetime.datetime, datetime.date, str]:
        """ """
        if isinstance(value, datetime.date):
            return value

        if not isinstance(value, str):
            # default handler
            return parse_datetime(value)
        match = FHIR_DATE_PARTS.match(value)
        if match:
            if (
                match.groupdict().get("year")
                and match.groupdict().get("month")
                and match.groupdict().get("day")
            ):
                return parse_date(value)
            elif match.groupdict().get("year") and match.groupdict().get("month"):
                if int(match.groupdict()["month"]) > 12:
                    raise DateError()
            # we don't want to loose actual information, so keep as string
            return value
        if not cls.regex.match(value):
            raise DateTimeError()

        return parse_datetime(value)

    @classmethod
    def to_string(cls, value):
        """ """
        if isinstance(value, (datetime.date, datetime.time, datetime.datetime)):
            value = value.isoformat()
        assert isinstance(value, str)
        return value


class Instant(datetime.datetime, Primitive):
    """An instant in time in the format YYYY-MM-DDThh:mm:ss.sss+zz:zz
    (e.g. 2015-02-07T13:28:17.239+02:00 or 2017-01-01T00:00:00Z).
    The time SHALL specified at least to the second and SHALL include a time zone.
    Note: This is intended for when precisely observed times are required
    (typically system logs etc.), and not human-reported times - for those,
    use date or dateTime (which can be as precise as instant,
    but is not required to be). instant is a more constrained dateTime

    Note: This type is for system times, not human times (see date and dateTime below)."""

    regex = re.compile(
        r"([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|"
        r"[1-9]000)-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|"
        r"3[0-1])T([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]"
        r"|60)(\.[0-9]+)?(Z|([+\-])((0[0-9]|"
        r"1[0-3]):[0-5][0-9]|14:00))"
    )
    __visit_name__ = "instant"

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":

        yield cls.validate

    @classmethod
    def validate(cls, value):
        """ """
        if isinstance(value, str):
            if not cls.regex.match(value):
                raise DateTimeError()
        return parse_datetime(value)

    @classmethod
    def to_string(cls, value):
        """ """
        if isinstance(value, (datetime.date, datetime.time, datetime.datetime)):
            value = value.isoformat()
        assert isinstance(value, str)
        return value


class Time(datetime.time, Primitive):
    """A time during the day, in the format hh:mm:ss.
    There is no date specified. Seconds must be provided due
    to schema type constraints but may be zero-filled and may
    be ignored at receiver discretion.
    The time "24:00" SHALL NOT be used. A time zone SHALL NOT be present.
    Times can be converted to a Duration since midnight."""

    regex = re.compile(r"([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]+)?")
    __visit_name__ = "time"

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":

        yield cls.validate

    @classmethod
    def validate(cls, value):
        """ """
        if isinstance(value, str):
            if not cls.regex.match(value):
                raise TimeError()

        return parse_time(value)

    @classmethod
    def to_string(cls, value):
        """ """
        if isinstance(value, (datetime.date, datetime.time, datetime.datetime)):
            value = value.isoformat()
        assert isinstance(value, str)
        return value


def get_fhir_type_class(model_name):
    try:
        return globals()[model_name + "Type"]
    except KeyError:
        raise LookupError(f"'{__name__}.{model_name}Type' doesnt found.")


class AbstractType(dict):
    """ """

    __fhir_release__: str = "{{release_name}}"
    __resource_type__: str = ...  # type: ignore

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(type=cls.__resource_type__)

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        from . import fhirtypesvalidators

        yield getattr(fhirtypesvalidators, cls.__resource_type__.lower() + "_validator")

    @classmethod
    def is_primitive(cls) -> bool:
        """ """
        return False

    @classmethod
    def fhir_type_name(cls) -> str:
        """ """
        return cls.__resource_type__


class FHIRPrimitiveExtensionType(AbstractType):
    """ """

    __resource_type__ = "FHIRPrimitiveExtension"


class AbstractBaseType(dict):
    """ """

    __fhir_release__: str = "{{release_name}}"
    __resource_type__: str = ...  # type: ignore

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(type=cls.__resource_type__)

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield cls.validate

    @classmethod
    def validate(cls, v, values, config, field):
        """ """
        if isinstance(v, (bytes, str)):
            input_data = load_str_bytes(v)
            resource_type = input_data.get("resourceType", None)
        elif isinstance(v, FHIRAbstractModel):
            resource_type = v.resource_type
        else:
            resource_type = v.get("resourceType", None)

        if resource_type is None or resource_type == cls.__resource_type__:
            from . import fhirtypesvalidators

            v = getattr(
                fhirtypesvalidators, cls.__resource_type__.lower() + "_validator"
            )(v)
            return v

        type_class = get_fhir_type_class(resource_type)
        v = run_validator_for_fhir_type(type_class, v, values, config, field)
        return v

    @classmethod
    def is_primitive(cls) -> bool:
        """ """
        return False

    @classmethod
    def fhir_type_name(cls) -> str:
        """ """
        return cls.__resource_type__


class ElementType(AbstractBaseType):
    """ """

    __resource_type__ = "Element"


class ResourceType(AbstractBaseType):
    """ """

    __resource_type__ = "Resource"
