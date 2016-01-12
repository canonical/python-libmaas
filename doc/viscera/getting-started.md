# Getting started with _viscera_


## Installation

Either work from a branch:

```console
$ git clone https://github.com/alburnum/alburnum-maas-client.git
$ cd alburnum-maas-client
$ make
```

Or install from [PyPI](https://pypi.python.org/):

```console
$ virtualenv --python=python3.5 maas
$ cd maas
$ bin/pip install alburnum-maas-client
```

## Logging-in

Log-in using the command-line tool:

```console
$ bin/maas login foo http://example.com:5240/MAAS/ admin
Password: …
```

__TODO__: Log-in programmatically.

Then start an interactive Python shell (e.g. `bin/python`):

```pycon
>>> from alburnum.maas import bones, viscera
>>> session = bones.SessionAPI.fromProfileName("foo")
>>> origin = viscera.Origin(session)
```

The `origin` instance is the root object of the API.


## Logging out

Log-out using the command-line tool:

```console
$ bin/maas logout foo
```

__TODO__: Log-out programmatically.


## Nodes

Listing nodes:

```pycon
>>> for node in origin.Nodes:
...     print(node)
```

Acquiring and starting nodes:

```pycon
>>> help(origin.Nodes.acquire)
acquire(*, hostname:str=None, architecture:str=None, cpus:int=None,
        memory:float=None, tags:typing.Sequence=None) method of
            alburnum.maas.viscera.NodesType instance
    :param hostname: The hostname to match.
    :param architecture: The architecture to match, e.g. "amd64".
    :param cpus: The minimum number of CPUs to match.
    :param memory: The minimum amount of RAM to match.
    :param tags: The tags to match, as a sequence. Each tag may be
        prefixed with a hyphen to denote that the given tag should NOT be
        associated with a matched node.
>>> node = origin.Nodes.acquire(tags=("foo", "-bar"))
>>> print(node.substatus_name)
Acquired
>>> node.start()
>>> print(node.substatus_name)
Deploying
```
