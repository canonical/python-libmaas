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

Then start an interactive Python shell, like `bin/python`:

```pycon
>>> from alburnum.maas import bones, viscera
>>> session = bones.SessionAPI.fromProfileName("foo")
>>> origin = viscera.Origin(session)
```

The `origin` instance is the root object of the API.

But there's no need! There's a command built in to do it for you:

```console
$ bin/maas shell
Welcome to the MAAS shell.

Predefined variables:

    origin: A `viscera` origin, configured for foo.
   session: A `bones` session, configured for foo.

>>>
```


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
...     print(repr(node))
<Node hostname='namibia.maas' system_id='433333'>
<Node hostname='botswana.maas' system_id='433334'>
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

Individual nodes can be read from the Web API.

```pycon
>>> node = origin.Node.read(system_id="433333")
```

Nodes have many useful attributes:

```pycon
>>> node.architecture
'amd64/generic'
>>> node.cpus
4
```

Trying using tab-completion — the objects have been designed to be
particularly friendly for interactive use — or ``dir(node)`` to find out
what other fields and methods are available.

__TODO__: Updating nodes.


## Files, Users, Tags

Similarly to nodes, these sets of objects can be fetched:

```pycon
>>> tags = origin.Tags.read()
>>> files = origin.Files.read()
>>> users = origin.Users.read()
```

When reading from collections, as above, the returned object is
list-like:

```pycon
>>> len(tags)
5
>>> tags[3]
<Tag comment="Foo's stuff" definition='' kernel_opts='' name='foo'>
>>> tags[3] in tags
True
>>> not_foo = [tag for tag in tags if tag.name != 'foo']
>>> len(not_foo)
4
```

However, it's read-only:

```pycon
>>> tags[0] = "bob"
…
TypeError: 'Tags' object does not support item assignment
```


## Events

Events are similar... but different. The only way to get events is by
the ``query`` method:

```pycon
>>> events = origin.Events.query()
```

This accepts a plethora of optional arguments to narrow down the results:

```pycon
>>> events = origin.Events.query(hostnames={"foo", "bar"})
>>> events = origin.Events.query(domains={"example.com", "maas.io"})
>>> events = origin.Events.query(zones=["red", "blue"])
>>> events = origin.Events.query(macs=("12:34:56:78:90:ab", ))
>>> events = origin.Events.query(system_ids=…)
>>> events = origin.Events.query(agent_name=…)
>>> events = origin.Events.query(level=…)
>>> events = origin.Events.query(after=…, limit=…)
```

These arguments can be combined to narrow the results even further.

The ``level`` argument is a little special. It's a choice from a
predefined set. For convenience, those choices are defined in the
``Level`` enum:

```pycon
>>> events = origin.Events.query(level=origin.Events.Level.ERROR)
```

but you can also pass in the string "ERROR" or the number 40.
