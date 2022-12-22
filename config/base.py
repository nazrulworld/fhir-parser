import os
import pathlib

"""Variable Start Here """
BASE_PATH = pathlib.Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_PATH = "downloads"
# classmap
CLASS_MAP = {
    "Any": "Resource",
    # to avoid Practinioner.role and PractitionerRole generating the same class
    "Practitioner.role": "PractRole",
    "boolean": "bool",
    #    "integer": "int",
    #    "positiveInt": "int",
    #    "unsignedInt": "int",
    #    "date": "FHIRDate",
    #    "dateTime": "FHIRDate",
    #    "instant": "FHIRDate",
    #    "time": "FHIRDate",
    #    "decimal": "float",
    #    "string": "str",
    #    "markdown": "str",
    #    "id": "str",
    #    "code": "str",  # for now we're not generating enums for these
    #    "uri": "str",
    #    "url": "str",
    #    "canonical": "str",
    #    "oid": "str",
    #    "uuid": "str",
    #
    #    "xhtml": "str",
    #    "base64Binary": "str",
}

# replacemap
# Classes to be replaced with different ones at resource rendering time
REPLACE_MAP = {
    #    "Reference": "FHIRReference"  # `FHIRReference` adds differencing capabilities
}
# natives
# Which class names are native to the language (or can be treated this way)
NATIVES = ["bool", "int", "float", "str", "dict"]

# jsonmap
# Which classes are to be expected from JSON decoding
JSON_MAP = {"str": "str", "int": "int", "bool": "bool", "float": "float"}
# jsonmap_default
JSON_MAP_DEFAULT = "dict"

# reservedmap
# Properties that need to be renamed because of language keyword conflicts
RESERVED_MAP = {
    "for": "for_fhir",
    "from": "from_fhir",
    "class": "class_fhir",
    "import": "import_fhir",
    "global": "global_fhir",
    "assert": "assert_fhir",
    "except": "except_fhir",
}

# enum_map
# For enum codes where a computer just cannot generate reasonable names
ENUM_MAP = {"=": "eq", "<": "lt", "<=": "lte", ">": "gt", ">=": "gte", "*": "max"}

# enum_namemap
# If you want to give specific names to enums based on their URI
ENUM_NAME_MAP = {
    "http://hl7.org/fhir/contracttermsubtypecodes": "ContractTermSubtypeCodes",
    "http://hl7.org/fhir/coverage-exception": "CoverageExceptionCodes",
    "http://hl7.org/fhir/resource-type-link": "ResourceTypeLink",
}
# base_url
FHIR_BASE_URL = "http://hl7.org/fhir"

# CURRENT_VERSION
CURRENT_RELEASE_NAME = "R4B"
# PREVIOUS_VERSIONS
PREVIOUS_RELEASES = {"STU3"}

# specification_url
SPECIFICATION_URL = "/".join([FHIR_BASE_URL, CURRENT_RELEASE_NAME])

# tpl_base
# In which directory to find the templates.
# See below for settings that start with `tpl_`: these are the template names.
TEMPLATE_DIRECTORY = "templates"

# write_resources
# Whether and where to put the generated class models
WRITE_RESOURCES = True

# tpl_resource_target
# target directory to write the generated class files to
RESOURCE_TARGET_DIRECTORY = "../fhir/resources"

# tpl_resource_target_ptrn
# target class file name pattern, with one placeholder (`{}`) for the class name
RESOURCE_FILE_NAME_PATTERN = "{}.py"

# tpl_resource_source
# the template to use as source when writing resource implementations for profiles
RESOURCE_SOURCE_TEMPLATE = "template-resource.jinja2"

# tpl_codesystems_source
# the template to use as source when writing enums for CodeSystems; can be `None`
CODE_SYSTEMS_SOURCE_TEMPLATE = None

# tpl_codesystems_target_name
# the filename to use for the generated code systems and
# value sets (in `RESOURCE_TARGET_DIRECTORY`)
CODE_SYSTEMS_TARGET_NAME = "codesystems.py"

# write_factory
# Whether and where to put the factory methods and the dependency graph
WRITE_FACTORY = True

# tpl_factory_source
# the template to use for factory generation
FACTORY_SOURCE_TEMPLATE = "template-elementfactory.jinja2"

# tpl_factory_target
# where to write the generated factory to
FACTORY_TARGET_NAME = "../tmp/fhir/resources/fhirelementfactory.py"

# write_dependencies
WRITE_DEPENDENCIES = False

# tpl_dependencies_source
# template used to render the JSON dependency graph
DEPENDENCIES_SOURCE_TEMPLATE = "template-dependencies.json"

# tpl_dependencies_target
# write dependency JSON to project root
DEPENDENCIES_TARGET_FILE_NAME = "./dependencies.json"

# write_unittests
# Whether and where to write unit tests
WRITE_UNITTESTS = True

# tpl_unittest_source
# the template to use for unit test generation
UNITTEST_SOURCE_TEMPLATE = "template-unittest.jinja2"

# tpl_unittest_target
# target directory to write the generated unit test files to
UNITTEST_TARGET_DIRECTORY = "../tmp/fhir/resources/tests"

# tpl_unittest_target_ptrn
# target file name pattern for unit tests; the one placeholder (`{}`)
# will be the class name
UNITTEST_TARGET_FILE_NAME_PATTERN = "test_{}.py"

# unittest_copyfiles
# array of file names to copy to the test directory
# `UNITTEST_TARGET_DIRECTORY` (e.g. unit test base classes)
UNITTEST_COPY_FILES = ["templates/conftest.py", "templates/fixtures.py"]

# unittest_format_path_prepare
# used to format `path` before appending another path
# element - one placeholder for `path`
UNITTEST_FORMAT_PATH_PREPARE = "{}"

# unittest_format_path_key
# used to create property paths by appending
# `key` to the existing `path` - two placeholders
UNITTEST_FORMAT_PATH_KEY = "{}.{}"

# unittest_format_path_index
# used for array properties - two placeholders, `path`
# and the array index
UNITTEST_FORMAT_PATH_INDEX = "{}[{}]"

# Settings for classes and resources
# default_base
DEFAULT_BASES = {
    # the class to use for "Element" types
    "complex-type": "FHIRAbstractModel",
    # the class to use for "Resource" types
    "resource": "FHIRResourceModel",
}

# resource_modules_lowercase
# whether all resource paths (i.e. modules)
# should be lowercase
RESOURCE_MODULE_LOWERCASE = True

# camelcase_classes
# whether class name generation should use CamelCase
CAMELCASE_CLASSES = True

# camelcase_enums
# whether names for enums should be camelCased
CAMELCASE_ENUMS = True

# backbone_class_adds_parent
# if True, backbone class names prepend their parent's class name
BACKBONE_CLASS_ADDS_PARENT = True

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
# manual_profiles
# All these files should be copied to `RESOURCE_TARGET_DIRECTORY`:
# tuples of (path/to/file, module, array-of-class-names)
# If the path is None, no file will be copied but the
# class names will still be recognized and it is assumed the class is present.
MANUAL_PROFILES = [
    ("templates/fhirresourcemodel.py", "fhirresourcemodel", ["FHIRResourceModel"],),
    ("templates/fhirabstractmodel.py", "fhirabstractmodel", ["FHIRAbstractModel"]),
    (
        "templates/fhirprimitiveextension.py",
        "fhirprimitiveextension",
        ["FHIRPrimitiveExtension"],
    ),
    ("templates/fhirtypes.py", "fhirtypes", FHIR_PRIMITIVES),
]
RESOURCES_WRITER_CLASS = "utils.ResourceWriter"
