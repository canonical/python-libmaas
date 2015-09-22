# Copyright 2015 Alburnum Ltd. This software is licensed under
# the GNU Affero General Public License version 3 (see LICENSE).

"""Distutils installer for alburnum-maas-client."""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
)

__metaclass__ = type

from sys import version_info

from setuptools import setup


package = b'alburnum.maas' if version_info.major == 2 else 'alburnum.maas'


setup(
    name='alburnum-maas-client',
    author='Gavin Panella',
    author_email='gavinpanella@gmail.com',
    url='https://github.com/alburnum/alburnum-maas-client',
    version="0.1",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
    ],
    packages={package},
    package_dir={'alburnum.maas': 'alburnum/maas'},
    # tests_require={"testtools >= 0.9.32", "fixtures >= 0.3.14"},
    test_suite="alburnum.maas.tests",
    description="A client API library specially for MAAS.",
)
