#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Download and parse FHIR resource definitions
#  Supply "-f" to force a redownload of the spec
#  Supply "-c" to force using the cached spec (incompatible with "-f")
#  Supply "-d" to load and parse but not write resources
#  Supply "-l" to only download the spec
#  Supply "-k" to keep previous version of FHIR resources

import io
import os
import sys

import config
import fhirloader
import fhirspec
import fhirclass
from distutils.version import StrictVersion

_cache = "downloads"


def ensure_init_py(settings, version_info):
    """ """
    init_tpl = """# _*_ coding: utf-8 _*_\n\n__fhir_version__ = "{0}"\n""".format(
        version_info.version
    )

    for file_location in [settings.RESOURCE_TARGET_DIRECTORY, settings.UNITTEST_TARGET_DIRECTORY]:

        if (file_location / "__init__.py").exists():
            lines = list()
            has_fhir_version = False
            with io.open(
                (file_location / "__init__.py"), "r"
            ) as fp:
                for line in fp:
                    if "__fhir_version__" in line:
                        has_fhir_version = True
                        parts = list()
                        parts.append(line.split("=")[0])
                        parts.append('"{0}"'.format(version_info.version))

                        line = "= ".join(parts)
                    lines.append(line.rstrip('\n'))

            if not has_fhir_version:
                lines.append('__fhir_version__ = "{0}"'.format(version_info.version))

            txt = "\n".join(lines)
        else:
            txt = init_tpl

        with io.open((file_location / "__init__.py"), "w") as fp:
            fp.write(txt)


if "__main__" == __name__:

    force_download = len(sys.argv) > 1 and "-f" in sys.argv
    dry = len(sys.argv) > 1 and ("-d" in sys.argv or "--dry-run" in sys.argv)
    load_only = len(sys.argv) > 1 and ("-l" in sys.argv or "--load-only" in sys.argv)
    force_cache = len(sys.argv) > 1 and ("-c" in sys.argv or "--cache-only" in sys.argv)
    keep_previous_versions = len(sys.argv) > 1 and (
        "-k" in sys.argv or "--keep-previous-versions" in sys.argv
    )

    # assure we have all files
    settings = config.Configuration()
    loader = fhirloader.FHIRLoader(settings, settings.BASE_PATH / _cache / settings.CURRENT_VERSION)
    spec_source = loader.load(force_download=force_download, force_cache=force_cache)

    # parse
    if not load_only:

        spec = fhirspec.FHIRSpec(spec_source, settings)
        if not dry:
            spec.write()
            # ensure init py has been created
            ensure_init_py(settings, spec.info)

    # checks for previous version maintain handler
    previous_version_info = getattr(settings, "PREVIOUS_VERSIONS", [])

    if previous_version_info and keep_previous_versions:
        # backup originals
        org_specification_url = settings.SPECIFICATION_URL
        org_tpl_resource_target = settings.RESOURCE_TARGET_DIRECTORY
        org_tpl_factory_target = settings.FACTORY_TARGET_NAME
        org_tpl_unittest_target = settings.UNITTEST_TARGET_DIRECTORY

        for version in previous_version_info:
            # reset cache
            fhirclass.FHIRClass.known = {}

            settings.SPECIFICATION_URL = (
                "/".join(org_specification_url.split("/")[:-1]) + "/" + version
            )
            settings.RESOURCE_TARGET_DIRECTORY = org_tpl_resource_target / version

            settings.FACTORY_TARGET_NAME = org_tpl_factory_target.parent / version / org_tpl_factory_target.name

            settings.UNITTEST_TARGET_DIRECTORY = org_tpl_unittest_target.parent / version / org_tpl_unittest_target.name

            # ##========>
            loader = fhirloader.FHIRLoader(settings, settings.BASE_PATH / _cache / version)
            spec_source = loader.load(
                force_download=force_download, force_cache=force_cache
            )
            # parse
            if not load_only:
                spec = fhirspec.FHIRSpec(spec_source, settings)

                if not dry:
                    spec.write()
                    # ensure init py has been created
                    ensure_init_py(settings, spec.info)

        # restore originals
        settings.SPECIFICATION_URL = org_specification_url
        settings.RESOURCE_TARGET_DIRECTORY = org_tpl_resource_target
        settings.FACTORY_TARGET_NAME = org_tpl_factory_target
        settings.UNITTEST_TARGET_DIRECTORY = org_tpl_unittest_target
        """
        if (StrictVersion(fhir_v_info[0]) > StrictVersion(cached_v_info[0])) and not force_download:
            sys.stdout.write(
                '==> New FHIR version {0} is available! However resources '
                'are generated from cache.'.format(fhir_v_info[0]))

        if keep_previous_versions and getattr(settings, 'previous_versions', None):

            for version in settings.previous_versions:
                update_pytest_fixture(version)
        """
