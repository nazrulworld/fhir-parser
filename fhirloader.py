#!/usr/bin/env python
from logger import logger
from fhirspec import Configuration
from fhirspec import download
import pathlib


class FHIRLoader(object):
    """ Class to download the files needed for the generator.

    The `needs` dictionary contains as key the local file needed and how to
    get it from the specification URL.
    """
    needs = {
        'version.info': ('version.info', None),
        'examples-json.zip': ('examples-json.zip', "examples"),
        'definitions.json.zip': ("definitions.json.zip", "definitions")
    }

    def __init__(self, settings: Configuration, cache: pathlib.Path):
        """ """
        self.settings = settings
        self.base_url = settings.SPECIFICATION_URL
        self.cache = cache

    def load(self, force_download=False, force_cache=False):
        """ Makes sure all the files needed have been downloaded.

        :returns: The path to the directory with all our files.
        """
        if force_download: assert not force_cache

        if self.cache.exists() and force_download:
            import shutil
            shutil.rmtree(self.cache)

        if not self.cache.exists():
            self.cache.mkdir(parents=True)

        # check all files and download if missing
        uses_cache = False
        for local, remote in self.__class__.needs.items():
            path_ = self.cache / local

            if not path_.exists():
                if force_cache:
                    raise Exception('Resource missing from cache: {}'.format(local))
                logger.info('Downloading {}'.format(remote))
                remote, expand_dir = remote
                filepath = self.download(remote)
                filename = filepath.name
                # unzip
                if '.zip' == filename[-4:]:
                    logger.info('Extracting {}'.format(filename))
                    target = self.cache
                    if expand_dir:
                        target = target / expand_dir
                        if not target.exists():
                            target.mkdir()

                    FHIRLoader.expand(filepath, target=target)
            else:
                uses_cache = True

        if uses_cache:
            logger.info('Using cached resources, supply "-f" to re-download')

        return self.cache

    def download(self, filename):
        """ Download the given file located on the server.

        :returns: The local file name in our cache directory the file was
            downloaded to
        """
        import requests     # import here as we can bypass its use with a manual download

        url = self.base_url+'/'+filename
        print(url)
        return download(url, download_directory=self.cache)

    @staticmethod
    def expand(filepath: pathlib.Path, target: pathlib.Path):
        """ Expand the ZIP file at the given path to the cache directory.
        """
        assert filepath.exists() and filepath.is_file()
        # import here as we can bypass its use with a manual unzip
        import zipfile

        with zipfile.ZipFile(filepath) as z:
            z.extractall(target)

