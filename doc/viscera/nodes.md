<h1>Machines, devices, racks, and regions</h1>

Given an ``Origin`` instance bound to your MAAS server, you can
interrogate your nodes with:

```python
origin.Machines.read()
  # returns an origin.Machines instance, a
  # sequence of origin.Machine instances.

origin.Devices.read()
  # returns an origin.Devices instance, a
  # sequence of origin.Device instances.

origin.RackControllers.read()
  # returns an origin.RackControllers instance, a
  # sequence of origin.RackController instances.

origin.RegionControllers.read()
  # returns an origin.RegionControllers instance, a
  # sequence of origin.RegionController instances.
```


## An example

```pycon
>>> for machine in origin.Machines.read():
...     print(repr(node))
<Machine hostname='botswana' system_id='pncys4'>
```

Individual nodes can be read from the Web API.

```pycon
>>> machine = origin.Machine.read(system_id="pncys4")
>>> machine
<Machine hostname='botswana' system_id='pncys4'>
```

Machines — and devices, racks, and regions — have many useful
attributes:

```pycon
>>> machine.architecture
'amd64/generic'
>>> machine.cpus
4
```

Don't forget to try using tab-completion — the objects have been
designed to be particularly friendly for interactive use — or
``dir(machine)`` to find out what other fields and methods are
available.

__TODO__: Updating nodes.


## Allocating and deploying

```pycon
>>> help(origin.Machines.allocate)
Help on method allocate in module maas.client.viscera.machines:

allocate(
    *, hostname:str=None, architecture:str=None, cpus:int=None,
    memory:float=None, tags:typing.Sequence=None)
  method of maas.client.viscera.machines.MachinesType instance
    :param hostname: The hostname to match.
    :param architecture: The architecture to match, e.g. "amd64".
    :param cpus: The minimum number of CPUs to match.
    :param memory: The minimum amount of RAM to match.
    :param tags: The tags to match, as a sequence. Each tag may be
        prefixed with a hyphen to denote that the given tag should NOT be
        associated with a matched machine.
>>> machine = origin.Machines.allocate(tags=("foo", "-bar"))
>>> print(machine.status_name)
Acquired
>>> machine.deploy()
>>> print(machine.status_name)
Deploying
```
