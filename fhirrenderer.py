#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import re
import shutil
import json
from fhirspec import FHIR_CLASS_TYPES
from fhirspec import FHIRClass

from jinja2 import Environment, PackageLoader, TemplateNotFound
from textwrap import TextWrapper
from jinja2.filters import contextfilter
from jinja2.filters import htmlsafe_json_dumps

from logger import logger
import io


@contextfilter
def string_wrap(ctx, value, width=88, to_json=True):
    """ """

    def simple_wrap(v):
        return f'"{v}"'

    if not value:
        return value
    if to_json is True:
        dumper = htmlsafe_json_dumps
    else:
        dumper = simple_wrap

    wrapper = TextWrapper(
        width=width, replace_whitespace=True, drop_whitespace=False, tabsize=4
    )
    new_value = map(lambda x: dumper(x), wrapper.wrap(value))
    return list(new_value)


def include_file(file_location):
    """ """
    with io.open(file_location, "r") as fp:
        return fp.read()


class FHIRRenderer(object):
    """ Superclass for all renderer implementations.
    """

    def __init__(self, spec, settings):
        self.spec = spec
        self.settings = settings
        self.jinjaenv = Environment(
            loader=PackageLoader("generate", self.settings.TEMPLATE_DIRECTORY)
        )
        self.jinjaenv.filters["string_wrap"] = string_wrap

    def render(self):
        """ The main rendering start point, for subclasses to override.
        """
        raise Exception("Cannot use abstract superclass' `render` method")

    def do_render(self, data, template_name, target_path):
        """ Render the given data using a Jinja2 template, writing to the file
        at the target path.

        :param template_name: The Jinja2 template to render, located in settings.TEMPLATE_DIRECTORY
        :param target_path: Output path
        """
        try:
            template = self.jinjaenv.get_template(template_name)
        except TemplateNotFound as e:
            logger.error(
                'Template "{}" not found in «{}», cannot render'.format(
                    template_name, self.settings.TEMPLATE_DIRECTORY
                )
            )
            return

        if not target_path:
            raise Exception("No target filepath provided")
        dirpath = target_path.parent
        if not dirpath.exists():
            dirpath.mkdir(parents=True)

        with io.open(target_path, "w", encoding="utf-8") as handle:
            logger.info("Writing {}".format(target_path))
            rendered = template.render(data)
            handle.write(rendered)
            # handle.write(rendered.encode('utf-8'))


class FHIRStructureDefinitionRenderer(FHIRRenderer):
    """ Write classes for a profile/structure-definition.
    """

    def copy_files(self, target_dir):
        """ Copy base resources to the target location, according to settings.
        """
        for filepath, module, contains in self.settings.MANUAL_PROFILES:
            if not filepath:
                continue

            if filepath.exists():
                tgt = target_dir / filepath.name
                logger.info(
                    "Copying manual profiles in {0} to {1}".format(filepath.name, tgt)
                )
                shutil.copyfile(filepath, tgt)

    def render_validators(self):
        """ """
        for profile in self.spec.writable_profiles():
            profile.writable_classes()
        all_classes = [
            cls
            for cls in FHIRClass.__known_classes__.values()
            if cls.class_type
            in (
                FHIR_CLASS_TYPES.resource,
                FHIR_CLASS_TYPES.complex_type,
                FHIR_CLASS_TYPES.logical,
            )
        ]
        all_classes = sorted(all_classes, key=lambda x: x.name)
        target_path = self.settings.RESOURCE_TARGET_DIRECTORY / "fhirtypesvalidators.py"
        self.do_render(
            {"classes": all_classes}, "fhirtypesvalidators.jinja2", target_path
        )

    def render_fhir_types(self):
        """ """
        for profile in self.spec.writable_profiles():
            profile.writable_classes()
        all_classes = [
            cls
            for cls in FHIRClass.__known_classes__.values()
            if cls.class_type
            in (
                FHIR_CLASS_TYPES.resource,
                FHIR_CLASS_TYPES.complex_type,
                FHIR_CLASS_TYPES.logical,
            )
        ]
        all_classes = sorted(all_classes, key=lambda x: x.name)
        target_path = self.settings.RESOURCE_TARGET_DIRECTORY / "fhirtypes.py"
        self.do_render({"classes": all_classes}, "fhirtypes.jinja2", target_path)

    def render(self):
        for profile in self.spec.writable_profiles():
            classes = sorted(profile.writable_classes(), key=lambda x: x.name)
            if 0 == len(classes):
                if (
                    profile.url is not None
                ):  # manual profiles have no url and usually write no classes
                    logger.info(
                        'Profile "{}" returns zero writable classes, skipping'.format(
                            profile.url
                        )
                    )
                continue

            imports = profile.needed_external_classes()
            need_fhirtypes: bool = False
            has_one_of_many = False
            has_array_type = False
            need_union_type = False
            one_of_many_fields = dict()
            for klass in classes:
                for prop in klass.properties:
                    # special variable
                    prop.need_primitive_ext = False

                    if not prop.is_native and need_fhirtypes is False:
                        need_fhirtypes = True
                    if prop.is_array and has_array_type is False:
                        has_array_type = True

                    prop_klass = FHIRClass.with_name(prop.class_name)
                    if prop_klass.class_type in (
                        FHIR_CLASS_TYPES.resource,
                        FHIR_CLASS_TYPES.logical,
                        FHIR_CLASS_TYPES.complex_type,
                    ):
                        prop.field_type = prop.class_name + "Type"
                    elif (
                        prop_klass.class_type == FHIR_CLASS_TYPES.primitive_type
                        or prop.is_native
                    ):
                        prop.need_primitive_ext = True

                    if prop_klass.class_type != FHIR_CLASS_TYPES.other:
                        prop.field_type_module = "fhirtypes"

                    # Check for Union Type
                    if (
                        prop.need_primitive_ext is True
                        and prop.is_array
                        and need_union_type is False
                    ):
                        need_union_type = True
                    # check for one_of_many
                    if prop.one_of_many:
                        if has_one_of_many is False:
                            has_one_of_many = True
                        if klass.name not in one_of_many_fields:
                            one_of_many_fields[klass.name] = {prop.one_of_many: []}
                        if prop.one_of_many not in one_of_many_fields[klass.name]:
                            one_of_many_fields[klass.name][prop.one_of_many] = []
                        one_of_many_fields[klass.name][prop.one_of_many].append(
                            prop.name
                        )
                    # Check Enums
                    if prop.field_type == "Code" and prop.short and "|" in prop.short:
                        prop.enum = list(
                            map(lambda x: x.strip(), prop.short.split("|"))
                        )
                    else:
                        prop.enum = list()

            data = {
                "profile": profile,
                "release_name": self.spec.settings.CURRENT_RELEASE_NAME,
                "info": self.spec.info,
                "imports": imports,
                "classes": classes,
                "need_fhirtypes": need_fhirtypes,
                "has_array_type": has_array_type,
                "fhir_class_types": FHIR_CLASS_TYPES,
                "one_of_many_fields": one_of_many_fields,
                "has_one_of_many": has_one_of_many,
                "need_union_type": need_union_type,
            }
            ptrn = (
                profile.targetname.lower()
                if self.settings.RESOURCE_MODULE_LOWERCASE
                else profile.targetname
            )
            source_path = self.settings.RESOURCE_SOURCE_TEMPLATE
            target_name = self.settings.RESOURCE_FILE_NAME_PATTERN.format(ptrn)
            target_path = self.settings.RESOURCE_TARGET_DIRECTORY / target_name
            self.do_render(data, source_path, target_path)

        self.copy_files(target_path.parent)
        self.render_validators()
        self.render_fhir_types()


class FHIRDependencyRenderer(FHIRRenderer):
    """ Puts down dependencies for each of the FHIR resources. Per resource
    class will grab all class/resource names that are needed for its
    properties and add them to the "imports" key. Will also check
    classes/resources may appear in references and list those in the
    "references" key.
    """

    def render(self):
        data = {"info": self.spec.info}
        resources = []
        for profile in self.spec.writable_profiles():
            resources.append(
                {
                    "name": profile.targetname,
                    "imports": profile.needed_external_classes(),
                    "references": profile.referenced_classes(),
                }
            )
        data["resources"] = sorted(resources, key=lambda x: x["name"])
        self.do_render(
            data,
            self.settings.DEPENDENCIES_SOURCE_TEMPLATE,
            self.settings.DEPENDENCIES_TARGET_FILE_NAME,
        )


class FHIRValueSetRenderer(FHIRRenderer):
    """ Write ValueSet and CodeSystem contained in the FHIR spec.
    """

    def render(self):
        if not self.settings.CODE_SYSTEMS_SOURCE_TEMPLATE:
            logger.info(
                "Not rendering value sets and code systems since `CODE_SYSTEMS_SOURCE_TEMPLATE` is not set"
            )
            return

        systems = [v for k, v in self.spec.codesystems.items()]
        data = {
            "info": self.spec.info,
            "systems": sorted(systems, key=lambda x: x.name),
        }
        target_name = self.settings.CODE_SYSTEMS_TARGET_NAME
        target_path = os.path.join(self.settings.RESOURCE_TARGET_DIRECTORY, target_name)
        self.do_render(data, self.settings.CODE_SYSTEMS_SOURCE_TEMPLATE, target_path)


class FHIRUnitTestRenderer(FHIRRenderer):
    """ Write unit tests.
    """

    def render(self):
        if not self.spec.unit_tests:
            return
        # render all unit test collections
        for coll in self.spec.unit_tests:
            tests = coll.tests
            if (
                self.settings.CURRENT_RELEASE_NAME == "R4"
                and coll.klass.name == "Bundle"
            ):
                tests = [
                    t
                    for t in tests
                    if t.filename
                    not in ("profiles-types.json", "extension-definitions.json")
                ]
            data = {
                "info": self.spec.info,
                "class": coll.klass,
                "tests": tests,
                "profile": self.spec.profiles[coll.klass.name.lower()],
                "release_name": self.settings.CURRENT_RELEASE_NAME,
            }

            file_pattern = coll.klass.name
            if self.settings.RESOURCE_MODULE_LOWERCASE:
                file_pattern = file_pattern.lower()
            file_name = self.settings.UNITTEST_TARGET_FILE_NAME_PATTERN.format(
                file_pattern
            )
            file_path = self.settings.UNITTEST_TARGET_DIRECTORY / file_name

            self.do_render(data, self.settings.UNITTEST_SOURCE_TEMPLATE, file_path)

        # copy unit test files, if any
        if self.settings.UNITTEST_COPY_FILES is not None:
            for filepath in self.settings.UNITTEST_COPY_FILES:
                if filepath.exists():
                    target = self.settings.UNITTEST_TARGET_DIRECTORY / filepath.name
                    logger.info(
                        "Copying unittest file {} to {}".format(filepath.name, target)
                    )
                    if filepath.name == "fixtures.py":
                        with open(filepath, "r") as fp:
                            contents = fp.read()
                            contents = contents.replace(
                                "{{release}}", self.settings.CURRENT_RELEASE_NAME
                            ).replace("{{fhir_version}}", self.spec.info.version)

                        with open(target, "w") as fp:
                            fp.write(contents)
                    else:
                        shutil.copyfile(filepath, target)
                else:
                    logger.warn(
                        'Unit test file "{0}" configured in `UNITTEST_COPY_FILES` does not exist'.format(
                            filepath
                        )
                    )
