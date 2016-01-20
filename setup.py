"""Setuptools installer for alburnum-maas-client."""

from setuptools import (
    find_packages,
    setup,
)


setup(
    name='alburnum-maas-client',
    author='Gavin Panella',
    author_email='gavinpanella@gmail.com',
    url='https://github.com/alburnum/alburnum-maas-client',
    version="0.3.1",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries',
    ],
    packages=find_packages(),
    package_data={
        'alburnum.maas.bones.tests': ['*.json'],
    },
    install_requires={
        "argcomplete >= 1.0",
        "beautifulsoup4 >= 4.4.1",
        "colorclass >= 1.2.0",
        "httplib2 >= 0.8",
        "oauthlib >= 1.0.3",
        "PyYAML >= 3.11",
        "requests >= 2.9.1",
        "terminaltables >= 2.1.0",
    },
    test_suite="alburnum.maas",
    tests_require={
        "django >= 1.6",
        "fixtures >= 1.0.0",
        "setuptools",
        "testscenarios",
        "testtools",
        "Twisted",
    },
    description="A client API library specially for MAAS.",
    entry_points={
        "console_scripts": {
            "maas = alburnum.maas.flesh:main",
        },
    },
)
