"""Setuptools installer for python-libmaas."""

from os.path import (
    dirname,
    join,
)

from setuptools import (
    find_packages,
    setup,
)


# The directory in which setup.py lives.
here = dirname(__file__)


def read(filename):
    """Return the whitespace-stripped content of `filename`."""
    path = join(here, filename)
    with open(path, "r") as fin:
        return fin.read().strip()


setup(
    name='python-libmaas',
    author='MAAS Developers',
    author_email='maas-devel@lists.launchpad.net',
    url='https://github.com/canonical/python-libmaas',
    version="0.6.8",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: Libraries',
    ],
    packages=find_packages(
        include={"maas", "maas.*"},
        exclude={"*.tests", "*.testing"},
    ),
    package_data={
        'maas.client.bones.testing': ['*.json'],
    },
    install_requires=[
        "aiohttp >= 2.0.0",
        "argcomplete >= 1.0",
        "colorclass >= 1.2.0",
        "macaroonbakery >= 1.1.3",
        "oauthlib >= 1.0.3",
        "packaging >= 21.3",
        "pymongo >= 3.5.1",  # for bson
        "pytz >= 2014.10",
        "PyYAML >= 3.11",
        "setuptools >= 58.2.0",
        "terminaltables >= 2.1.0",
    ],
    test_suite="maas.client",
    tests_require=[
        "django >= 2.2.4, < 3.0",
        "fixtures >= 1.0.0",
        "setuptools >= 58.2.0",
        "testscenarios",
        "testtools",
        "Twisted<23.0.0",
    ],
    description="A client API library specially for MAAS.",
    long_description=read('README'),
    long_description_content_type='text/markdown',
    entry_points={
        "console_scripts": {
            "maas = maas.client.flesh:main",
        },
    },
)
