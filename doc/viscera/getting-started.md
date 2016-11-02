# Getting started with _viscera_


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

*Note* that PyPI may lag the others.


## Logging-in

Log-in using the command-line tool and start an interactive Python
shell:

```console
$ maas profiles login foo http://example.com:5240/MAAS/ admin
Password: …
$ maas shell
```

This will provide you with a pre-prepared `origin` object that points to
`foo` from above. This is the root object of the API.

You can also log-in programmatically:

```pycon
>>> profile, origin = Origin.login(
...     "http://example.com:5240/MAAS/", username="admin",
...     password="…")
```

The `profile` has not been saved, but it's easy to do so:

```pycon
>>> profile = profile.replace(name="foo")
>>> with ProfileStore.open() as store:
...     store.save(profile)
...     store.default = profile
```

This does the same as the `maas profiles login` command.

But there's no need! There's a command built in to do it for you:

```console
$ bin/maas shell
Welcome to the MAAS shell.

Predefined variables:

    origin: A `viscera` origin, configured for foo.
   session: A `bones` session, configured for foo.

>>>
```


## Logging-out

Log-out using the command-line tool:

```console
$ bin/maas profiles remove foo
```

or, programmatically:

```pycon
>>> with ProfileStore.open() as store:
...     store.delete("foo")
```


## `dir()`, `help()`, and tab-completion

The _viscera_ API has been designed to be very discoverable using
tab-completion, `dir()`, `help()`, and so on. Start with that:

```pycon
>>> origin.<tab>
…
```

This works best when you've got [IPython](https://ipython.org/)
installed.
