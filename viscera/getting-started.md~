# Getting started with _viscera_


## Installation

Either work from a branch:

```sh
$ git clone https://github.com/alburnum/alburnum-maas-client.git
$ cd alburnum-maas-client
$ make
```

Or install from [PyPI](https://pypi.python.org/):

```sh
$ virtualenv --python=python3.5 maas
$ cd maas
$ bin/pip install alburnum-maas-client
```

## Logging-in

Log-in using the command-line tool:

```sh
$ bin/maas login foo http://example.com:5240/MAAS/ admin
Password: ...
```

__TODO__: Log-in programmatically.

Then start an interactive Python shell (e.g. `bin/python`):

```python
>>> from alburnum.maas import bones, viscera
>>> session = bones.Session.fromProfileName("foo")
>>> origin = viscera.Origin(session)
```

The `origin` instance is the root object of the API.


## Logging out

Log-out using the command-line tool:

```sh
$ bin/maas logout foo
```

__TODO__: Log-out programmatically.


## List nodes

```python
>>> for node in origin.Nodes:
...     print(node)
```
