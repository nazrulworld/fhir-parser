#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Download and parse FHIR resource definitions
#  Supply "-f" to force a redownload of the spec
#  Supply "-c" to force using the cached spec (incompatible with "-f")
#  Supply "-d" to load and parse but not write resources
#  Supply "-l" to only download the spec
#  Supply "-k" to keep previous version of FHIR resources

import sys

import config
import fhirloader
import fhirspec
import fhirclass
import typing
import click
import pathlib

from utils import ensure_init_py
from utils import update_pytest_fixture

_cache_path = "downloads"


@click.command()
@click.option(
    "--fhir-release",
    "-r",
    type=click.Choice(["STU3", "R4"], case_sensitive=True),
    help="FHIR Release",
    default=None,
    required=False,
)
@click.option("--dry-run", "-d", is_flag=True, default=False, help="Dry Run")
@click.option(
    "--force-download", "-f", is_flag=True, default=False, help="Force Download"
)
@click.option("--load-only", "-l", is_flag=True, default=False, help="Load Only")
@click.option("--cache-only", "-c", is_flag=True, default=False, help="Cache only")
@click.option(
    "--build-previous-versions",
    "-k",
    is_flag=True,
    default=False,
    help="Build previous versions",
)
@click.option(
    "--previous-versions",
    "-p",
    multiple=True,
    type=click.Choice(["STU3", "R4"], case_sensitive=True),
    required=False,
)
def main(
    dry_run: bool,
    force_download: bool,
    load_only: bool,
    cache_only: bool,
    build_previous_versions: bool,
    fhir_release: str = None,
    previous_versions: typing.Sequence[str] = None,
):
    """ """
    settings = config.Configuration()
    if fhir_release is not None:
        settings["CURRENT_RELEASE_NAME"] = fhir_release
        settings["SPECIFICATION_URL"] = "/".join([settings.FHIR_BASE_URL, fhir_release])
    if previous_versions:
        settings["PREVIOUS_RELEASES"] = set(previous_versions)

    spec_source = load(settings, force_download=force_download, cache_only=cache_only)
    if load_only is False:
        generate_from_fhir_spec(spec_source, settings, dry_run=dry_run)

    # checks for previous version maintain handler
    current_version = settings["CURRENT_RELEASE_NAME"]
    previous_versions = [
        pv
        for pv in getattr(settings, "PREVIOUS_RELEASES", set())
        if pv != current_version
    ]

    if len(previous_versions) > 0 and build_previous_versions is True:
        # backup originals
        ORG_SPECIFICATION_URL = settings.SPECIFICATION_URL
        ORG_RESOURCE_TARGET_DIRECTORY = settings.RESOURCE_TARGET_DIRECTORY
        ORG_FACTORY_TARGET_NAME = settings.FACTORY_TARGET_NAME
        ORG_UNITTEST_TARGET_DIRECTORY = settings.UNITTEST_TARGET_DIRECTORY
        for pv in previous_versions:
            # reset cache, important!
            fhirclass.FHIRClass.known = {}

            settings["CURRENT_RELEASE_NAME"] = pv
            settings["SPECIFICATION_URL"] = "/".join([settings.FHIR_BASE_URL, pv])

            settings["RESOURCE_TARGET_DIRECTORY"] = ORG_RESOURCE_TARGET_DIRECTORY / pv

            settings["FACTORY_TARGET_NAME"] = (
                ORG_FACTORY_TARGET_NAME.parent / pv / ORG_FACTORY_TARGET_NAME.name
            )

            settings["UNITTEST_TARGET_DIRECTORY"] = (
                ORG_UNITTEST_TARGET_DIRECTORY.parent
                / pv
                / ORG_UNITTEST_TARGET_DIRECTORY.name
            )
            spec_source = load(
                settings, force_download=force_download, cache_only=cache_only
            )
            if load_only is False:
                generate_from_fhir_spec(spec_source, settings, dry_run=dry_run)
                if dry_run is False:
                    update_pytest_fixture(settings)

        # restore originals
        fhirclass.FHIRClass.known = {}
        settings["CURRENT_RELEASE_NAME"] = current_version
        settings["SPECIFICATION_URL"] = ORG_SPECIFICATION_URL
        settings["RESOURCE_TARGET_DIRECTORY"] = ORG_FACTORY_TARGET_NAME
        settings["FACTORY_TARGET_NAME"] = ORG_FACTORY_TARGET_NAME
        settings["UNITTEST_TARGET_DIRECTORY"] = ORG_UNITTEST_TARGET_DIRECTORY

    return 0


def load(settings: config.Configuration, force_download: bool, cache_only: bool):
    """ """
    loader = fhirloader.FHIRLoader(
        settings, settings.BASE_PATH / _cache_path / settings.CURRENT_RELEASE_NAME
    )
    spec_source = loader.load(force_download=force_download, force_cache=cache_only)
    return spec_source


def generate_from_fhir_spec(
    spec_source: pathlib.Path, settings: config.Configuration, dry_run: bool
):
    """ """
    spec = fhirspec.FHIRSpec(spec_source, settings)
    if dry_run is False:
        spec.write()
        # ensure init py has been created
        ensure_init_py(settings, spec.info)


if "__main__" == __name__:
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        click.echo(
            "Operation aborted, as interrupted by user.", color=click.style("yellow")
        )
        sys.exit(1)
