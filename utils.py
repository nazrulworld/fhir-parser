import configparser
import os
import pathlib
import sys
import typing
from subprocess import check_call, CalledProcessError

from fhirspec import FHIRSpecWriter

import fhirrenderer

__author__ = "Md Nazrul Islam <email2nazrul@gmail.com>"

INIT_TPL = (
    """
__author__ = "Md Nazrul Islam"
__email__ = "email2nazrul@gmail.com"
__fhir_version__ = "{0}"

"""
)


def ensure_init_py(settings, version_info):
    """ """
    init_tpl = INIT_TPL.format(version_info.version, "element_type")

    for file_location in [
        settings.RESOURCE_TARGET_DIRECTORY,
        settings.UNITTEST_TARGET_DIRECTORY,
    ]:

        if (file_location / "__init__.py").exists():
            lines = list()
            has_fhir_version = False
            with open((file_location / "__init__.py"), "r") as fp:
                for line in fp:
                    if "__fhir_version__" in line:
                        has_fhir_version = True
                        parts = list()
                        parts.append(line.split("=")[0])
                        parts.append('"{0}"'.format(version_info.version))

                        line = "= ".join(parts)
                    lines.append(line.rstrip("\n"))

            if not has_fhir_version:
                lines.append('__fhir_version__ = "{0}"'.format(version_info.version))

            txt = "\n".join(lines)
        else:
            txt = init_tpl

        with open((file_location / "__init__.py"), "w") as fp:
            fp.write(txt)


def update_pytest_fixture(settings):
    """ """
    lines = list()
    fixture_file = settings.RESOURCE_TARGET_DIRECTORY / "tests" / "fixtures.py"
    with open(str(fixture_file), "r", encoding="utf-8") as fp:
        for line in fp:
            if "ROOT_PATH =" in line:
                parts = list()
                parts.append(line.split("=")[0])
                parts.append(
                    "dirname(dirname(dirname(dirname(dirname(os.path.abspath(__file__))))))\n"
                )
                line = "= ".join(parts)

            elif "CACHE_PATH =" in line:
                parts = list()
                parts.append(line.split("=")[0])
                parts.append(
                    f"os.path.join(ROOT_PATH, '.cache', '{settings.CURRENT_RELEASE_NAME}')\n"
                )
                line = "= ".join(parts)

            lines.append(line)

    # let's write
    fixture_file.write_text("".join(lines))

    with open(
        str(settings.RESOURCE_TARGET_DIRECTORY / "tests" / "conftest.py"),
        "w",
        encoding="utf-8",
    ) as fp:
        fp.write(
            "# -*- coding: utf-8 _*_\n"
            f"pytest_plugins = ['fhir.resources.{settings.CURRENT_RELEASE_NAME}.tests.fixtures']\n"
        )


def get_cached_version_info(spec_source):
    """ """
    if not spec_source.exists():
        return
    version_file = spec_source / "version.info"

    if not version_file.exists():
        return

    config = configparser.ConfigParser()

    with open(str(version_file), "r") as fp:
        txt = fp.read()
        config.read_string("\n".join(txt.split("\n")[1:]))

    return config["FHIR"]["version"], config["FHIR"]["fhirversion"]


def parse_path(path_str: str) -> pathlib.Path:
    """Path normalizer"""
    if path_str.startswith("~"):
        return pathlib.Path(os.path.expanduser(path_str))

    if len(path_str) == 1 and path_str == ".":
        path_str = os.getcwd()
    elif path_str.startswith("." + os.sep):
        path_str = os.getcwd() + path_str[1:]
    if path_str.endswith(os.sep):
        path_str = path_str[: -len(os.sep)]

    return pathlib.Path(path_str)


class ResourceWriter(FHIRSpecWriter):
    def write(self):
        """ """
        if self.settings.WRITE_RESOURCES:
            renderer = fhirrenderer.FHIRStructureDefinitionRenderer(
                self.spec, self.settings
            )
            renderer.render()

            vsrenderer = fhirrenderer.FHIRValueSetRenderer(self.spec, self.settings)
            vsrenderer.render()

        if self.settings.WRITE_DEPENDENCIES:
            renderer = fhirrenderer.FHIRDependencyRenderer(self.spec, self.settings)
            renderer.render()

        if self.settings.WRITE_UNITTESTS:
            renderer = fhirrenderer.FHIRUnitTestRenderer(self.spec, self.settings)
            renderer.render()


class FhirPathExpressionParserWriter:
    output_dir: pathlib.Path = None
    grammar_path: pathlib.Path = None
    antlr4_executable: str = "antlr4"
    antlr4_version: str = None

    def __init__(
        self, output_dir=typing.Union[pathlib.Path, str], antlr4_version: str = "4.9.3"
    ):
        """ """
        if isinstance(output_dir, str):
            self.output_dir = parse_path(output_dir)
        elif isinstance(output_dir, pathlib.Path):
            self.output_dir = output_dir
        self.grammar_path = (
            pathlib.Path(os.path.abspath(__file__)).parent / "FHIRPathExpression.g4"
        )
        self.antlr4_version = antlr4_version

    def write(self):
        """ """
        options = [
            str(self.antlr4_executable),
            "-v",
            self.antlr4_version,
            "-o",
            str(self.output_dir),
            "-Dlanguage=Python3",
            str(self.grammar_path),
        ]
        sys.stdout.write(f"Start executing command '{options}'\n")
        try:
            check_call(options)
            sys.stdout.write(f"Files are written at {self.output_dir}" + "\n")
            return 0
        except CalledProcessError as exc:
            sys.stderr.write("Cannot write!\n")
            sys.stderr.write(str(exc) + "\n")
            return 1
