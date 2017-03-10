"""Setuptools installer for python-libmaas."""

from setuptools import (
    find_packages,
    setup,
)


setup(
    name='python-libmaas',
    author='MAAS Developers',
    author_email='maas-devel@lists.launchpad.net',
    url='https://github.com/maas/python-libmaas',
    version="0.4.1",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries',
    ],
    namespace_packages=['maas'],
    packages=find_packages(),
    package_data={
        'maas.client.bones.testing': ['*.json'],
    },
    install_requires={
        "aiohttp >= 1.1.4",
        "argcomplete >= 1.0",
        "beautifulsoup4 >= 4.4.1",
        "colorclass >= 1.2.0",
        "oauthlib >= 1.0.3",
        "pytz >= 2014.10",
        "PyYAML >= 3.11",
        "terminaltables >= 2.1.0",
    },
    test_suite="maas.client",
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
            "maas = maas.client.flesh:main",
        },
    },
)
