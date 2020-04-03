import ast
import configparser
import pathlib
import os
SRC_BASE_PATH = pathlib.Path(os.path.abspath(__file__)).parents[1] / 'tmp' / 'fhir' / 'resources'


def update_pytest_fixture(src_base, version):
    """ """
    lines = list()
    fixture_file = src_base / version / 'tests' / 'fixtures.py'
    with open(str(fixture_file), 'r', encoding='utf-8') as fp:
        for line in fp:
            if 'ROOT_PATH =' in line:
                parts = list()
                parts.append(line.split('=')[0])
                parts.append("dirname(dirname(dirname(dirname(dirname(os.path.abspath(__file__))))))\n")
                line = '= '.join(parts)

            elif 'CACHE_PATH =' in line:
                parts = list()
                parts.append(line.split('=')[0])
                parts.append(f"os.path.join(ROOT_PATH, '.cache', '{version}')\n")
                line = '= '.join(parts)

            elif 'example_data_file_uri =' in line:

                parts = list()
                parts.append(line.split('=')[0])
                parts.append(f"'/'.join([settings['base_url'], '{version}', 'examples-json.zip'])\n")
                line = '= '.join(parts)

            lines.append(line)

    # let's write
    fixture_file.write_text(''.join(lines))

    with open(str(src_base / version / 'tests' / 'conftest.py'), 'w', encoding='utf-8') as fp:
        fp.write(
            "# _*_ coding: utf-8 _*_\n"
            f"pytest_plugins = ['fhir.resources.{version}.tests.fixtures']\n")

def get_cached_version_info():
    """ """
    if not PARSER_CACHE_DIR.exists():
        return
    version_file = PARSER_CACHE_DIR / 'version.info'

    if not version_file.exists():
        return

    config = configparser.ConfigParser()

    with open(str(version_file), 'r') as fp:
        txt = fp.read()
        config.read_string('\n'.join(txt.split('\n')[1:]))

    return config['FHIR']['version'], config['FHIR']['fhirversion']
