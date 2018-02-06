# python-libmaas

Python client API library made especially for [MAAS][].

[![Build Status](https://travis-ci.org/maas/python-libmaas.svg?branch=master)](https://travis-ci.org/maas/python-libmaas)
[![codecov.io](https://codecov.io/github/maas/python-libmaas/coverage.svg?branch=master)](https://codecov.io/github/maas/python-libmaas?branch=master)


## Installation

All the dependencies are declared in `setup.py` so this can be installed
with [pip](https://pip.pypa.io/). Python 3.5+ is required.

When working from trunk it can be helpful to use `virtualenv`:

    $ virtualenv --python=python3 amc && source amc/bin/activate
    $ pip install git+https://github.com/maas/python-libmaas.git
    $ maas --help

Releases are periodically made to [PyPI](https://pypi.python.org/) but,
at least for now, it makes more sense to work directly from trunk.


## Documentation

Documentation can be generated with `make docs` which publishes into the
`site` directory. Recent documentation is also published to the
[MAAS Client Library & CLI documentation][docs] site.


## Development

It's pretty easy to start hacking on _python-libmaas_:

    $ git clone git@github.com:maas/python-libmaas.git
    $ cd python-libmaas
    $ make develop
    $ make test

Installing [IPython][] is generally a good idea too:

    $ bin/pip install -UI IPython

Pull requests are welcome but authors need to sign the [Canonical
contributor license agreement][CCLA] before those PRs can be merged.


## History & licence

In short: [AGPLv3][].

_python-libmaas_ was begun by a core MAAS developer, Gavin Panella, on
his own time, but is now maintained by the core MAAS team at Canonical.
It is licensed under the GNU Affero GPLv3, the same as MAAS itself.

Some of the code in here has come from MAAS, upon which Canonical Ltd
has the copyright. Gavin Panella licenses his parts under the AGPLv3,
and MAAS is also under the AGPLv3, so everything should be good.


[MAAS]: https://maas.io/
[docs]: http://maas.github.io/python-libmaas/

[CCLA]: https://www.ubuntu.com/legal/contributors
[AGPLv3]: https://www.gnu.org/licenses/agpl-3.0.html

[IPython]: https://ipython.org/
