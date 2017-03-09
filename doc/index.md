# Welcome to MAAS's new command-line tool & Python client libraries

_python-libmaas_ provides:

* A rich and stable Python client library for interacting with MAAS 2.0+
  servers. This can be used in a synchronous/blocking mode, or an
  asynchronous/non-blocking mode based on [asyncio][].

* A lower-level Python client library, auto-generated to match the MAAS
  server it's interacting with.

* A command-line tool for working with MAAS servers.

For MAAS _server_ documentation, visit
[docs.ubuntu.com](https://docs.ubuntu.com/maas/).


## Installation

Either work from a branch:

```console
$ git clone https://github.com/maas/python-libmaas.git
$ cd python-libmaas
$ make
```

Or install with [pip](https://pip.pypa.io/) into a
[virtualenv](https://virtualenv.readthedocs.org/):

```console
$ virtualenv --python=python3.5 amc && source amc/bin/activate
$ pip install git+https://github.com/maas/python-libmaas.git
```

Or install from [PyPI](https://pypi.python.org/):

```console
$ virtualenv --python=python3.5 amc && source amc/bin/activate
$ pip install python-libmaas
```

**Note** that PyPI may lag the others.

This documentation assumes you're working from a branch or in a
virtualenv. In practice this means it will use partially qualified paths
like ``bin/maas`` instead of bare ``maas`` invocations. If you've
installed from PyPI the ``maas`` command will probably be installed on
your shell's ``PATH`` so you can invoke it as ``maas``.


## Command-line

```console
$ bin/maas profiles login --help
$ bin/maas profiles login exmpl \
>   http://example.com:5240/MAAS/ my_username
Password: …
$ bin/maas list
┌───┬────────────┬───────────┬───────┬────────┬────────┬─────────┐
│   │ Hostname   │ System ID │ #CPUs │ RAM    │ Status │ Power   │
├───┼────────────┼───────────┼───────┼────────┼────────┼─────────┤
│ m │ botswana   │ pncys4    │ 4     │ 8.0 GB │ Ready  │ Off     │
│ c │ namibia    │ xfaxgw    │ 4     │ 8.0 GB │ —      │ Error   │
│ C │ madagascar │ 4y3h7n    │ 4     │ 8.0 GB │ —      │ Unknown │
└───┴────────────┴───────────┴───────┴────────┴────────┴─────────┘
```


## Client library

The simplest entry points into ``python-libmaas`` are the ``connect``
and ``login`` functions in ``maas.client``. The former connects to a
MAAS server using a previously obtained API key, and the latter logs-in
to MAAS with your username and password. These returns a ``Client``
object that has convenient attributes for working with MAAS. For
example, to print out a few recent events:

```python
from maas.client import login
client = login(
    "http://localhost:5240/MAAS/",
    username="my_user", password="my_pass",
)
tmpl = (
    "{0.created:%Y-%m-%d %H:%M:%S} "
    "{0.level.name} {0.description_short}"
)
for event in client.events.query():
    print(tmpl.format(event))
```

Learn more about the [client](client/index.md).


### _Bones_ & _viscera_

The primary client is based on two underlying libraries:

* A lower-level library that closely mirrors MAAS's Web API, referred to
  as _bones_. The MAAS server publishes a description of its Web API and
  _bones_ provides a convenient mechanism to interact with it.

* A higher-level library that's designed for developers, referred to as
  _viscera_. MAAS's Web API is sometimes unfriendly or inconsistent, but
  _viscera_ presents a hand-crafted API specifically _designed_ for
  developers rather than machines.

The implementation of [_viscera_](viscera/index.md) makes use of
[_bones_](bones/index.md).

Try this next: [Get started with _viscera_](viscera/getting-started.md)


## Shell

There's an interactive shell too. This imports some convenient bits into
the default namespace, and creates a _viscera_ ``Origin`` instance and a
_bones_ ``SessionAPI`` instance bound to the currently selected profile.

For the best experience install [IPython](https://ipython.org/) first.

```console
$ bin/maas shell
Welcome to the MAAS shell.
...
```

```pycon
>>> origin.Version.read()
<Version 2.2.0 beta2+bzr5717 [bridging-automatic-ubuntu ...]>
```


[asyncio]: https://docs.python.org/3/library/asyncio.html
