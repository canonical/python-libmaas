# Copyright 2015 Alburnum Ltd. This software is licensed under
# the GNU Affero General Public License version 3 (see LICENSE).

"""Setuptools installer for alburnum-maas-client."""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
)

__metaclass__ = type

from sys import version_info

from setuptools import (
    find_packages,
    setup,
)


def native_string(string):
    """Ensure that `string` is a native string.

    i.e. a byte string on Python 2, a unicode string on Python 3.
    """
    if version_info.major == 2:
        if isinstance(string, unicode):
            return string.encode("utf-8")
        else:
            return string
    else:
        if isinstance(string, bytes):
            return string.decode("utf-8")
        else:
            return string


setup(
    name='alburnum-maas-client',
    author='Gavin Panella',
    author_email='gavinpanella@gmail.com',
    url='https://github.com/alburnum/alburnum-maas-client',
    version="0.2.0",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
    ],
    packages=find_packages(),
    package_data={
        native_string('alburnum.maas.tests'): ['*.json'],
    },
    install_requires={
        "httplib2 >= 0.8",
        "oauth >= 1.0.1",
        "pbr >= 1.8.0",
        "six >= 1.9.0",
    },
    test_suite="alburnum.maas.tests",
    tests_require={
        "django >= 1.6",
        "fixtures >= 1.0.0",
        "mock",
        "setuptools",
        "testscenarios",
        "testtools",
        "Twisted",
    },
    description="A client API library specially for MAAS.",
)
