# Copyright 2015 Alburnum Ltd. This software is licensed under
# the GNU Affero General Public License version 3 (see LICENSE).

"""Setuptools installer for alburnum-maas-client.

This does not currently work with Python 3 because MAAS, part of upon which
this depends, does not currently work with Python 3.
"""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
)

__metaclass__ = type

from setuptools import (
    find_packages,
    setup,
)


setup(
    name='alburnum-maas-client',
    author='Gavin Panella',
    author_email='gavinpanella@gmail.com',
    url='https://github.com/alburnum/alburnum-maas-client',
    version="0.1.4.post4",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        # 'Programming Language :: Python :: 3',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
    ],
    packages=find_packages(),
    install_requires={
        "bzr >= 2.6",
        "httplib2 >= 0.8",
        "oauth >= 1.0.1",
    },
    test_suite="alburnum.maas.tests",
    description="A client API library specially for MAAS.",
)
