# _Viscera_: Working with nodes


## Listing

```pycon
>>> for node in origin.Nodes:
...     print(repr(node))
<Node hostname='namibia.maas' system_id='433333'>
<Node hostname='botswana.maas' system_id='433334'>
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

Don't forget to try using tab-completion — the objects have been
designed to be particularly friendly for interactive use — or
``dir(node)`` to find out what other fields and methods are available.

__TODO__: Updating nodes.


## Acquiring and starting

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
