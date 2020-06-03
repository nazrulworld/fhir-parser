#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import re
import shutil
import textwrap

from jinja2 import Environment, PackageLoader, TemplateNotFound
from jinja2.filters import environmentfilter
from logger import logger


class FHIRRenderer(object):
    """ Superclass for all renderer implementations.
    """

    def __init__(self, spec, settings):
        self.spec = spec
        self.settings = settings
        self.jinjaenv = Environment(
            loader=PackageLoader("generate", self.settings.TEMPLATE_DIRECTORY)
        )

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
            if profile.name == "Patient":
                breakpoint()
            imports = profile.needed_external_classes()
            has_fhir_primitive: bool = False
            for cls in imports:
                if cls.is_fhir_primitive:
                    has_fhir_primitive = True
                    break
            has_array_type = False
            _break = False
            for klass in classes:
                for prop in klass.properties:
                    if prop.is_array:
                        has_array_type = True
                        _break = True
                        break
                if _break is True:
                    break
                if klass.superclass and klass.superclass.properties:
                    for prop in klass.superclass.properties:
                        if prop.is_array:
                            has_array_type = True
                            _break = True
                            break
                if _break is True:
                    break

            data = {
                "profile": profile,
                "release_name": self.spec.settings.CURRENT_RELEASE_NAME,
                "info": self.spec.info,
                "imports": imports,
                "classes": classes,
                "has_fhir_primitive": has_fhir_primitive,
                "has_array_type": has_array_type
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


class FHIRFactoryRenderer(FHIRRenderer):
    """ Write factories for FHIR classes.
    """

    def render(self):
        classes = []
        for profile in self.spec.writable_profiles():
            classes.extend(profile.writable_classes())

        data = {
            "info": self.spec.info,
            "classes": sorted(classes, key=lambda x: x.name),
        }
        self.do_render(
            data,
            self.settings.FACTORY_SOURCE_TEMPLATE,
            self.settings.FACTORY_TARGET_NAME,
        )


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

            data = {
                "info": self.spec.info,
                "class": coll.klass,
                "tests": coll.tests,
                "profile": self.spec.profiles[coll.klass.name.lower()],
                "release_name": self.settings.CURRENT_RELEASE_NAME
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
