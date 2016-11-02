# python-libmaas

Python client API library made especially for [MAAS][1].

This was begun by a core MAAS developer, Gavin Panella, on his own time,
but is now maintained by the core MAAS team at Canonical. It is licensed
under the GNU Affero GPLv3, the same as MAAS itself.

[![Build Status](https://travis-ci.org/maas/python-libmaas.svg?branch=master)](https://travis-ci.org/maas/python-libmaas)
[![codecov.io](https://codecov.io/github/maas/python-libmaas/coverage.svg?branch=master)](https://codecov.io/github/maas/python-libmaas?branch=master)

Some of the code in here has come from MAAS, upon which Canonical Ltd
has the copyright. Gavin Panella licenses his parts under the AGPLv3,
and MAAS is also under the AGPLv3, so everything should be good.


## Installation

All the dependencies are declared in `setup.py` so this can be installed
with [pip](https://pip.pypa.io/). Python 3.5 is required.

When working from trunk it can be helpful to use `virtualenv`:

    $ virtualenv --python=python3.5 amc && source amc/bin/activate
    $ pip install git+https://github.com/maas/python-libmaas.git
    $ maas --help

Releases are periodically made to [PyPI](https://pypi.python.org/) but,
at least for now, it makes more sense to work directly from trunk.


## Documentation

Documentation can be generated with `make docs` which publishes into the
`site` directory. Recent documentation is also published to the
[MAAS Client Library & CLI documentation][2] site.


[1]: https://maas.ubuntu.com/
[2]: http://maas.github.io/python-libmaas/
