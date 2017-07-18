<h1>Machines, devices, racks, and regions</h1>

Given a ``Client`` instance bound to your MAAS server, you can
interrogate your nodes.

## Read nodes

Each node type exists on the client: ``machines``, ``devices``,
``rack_controllers``, ``region_controllers``.

```pycon
>>> client.machines.list()
<Machines length=1 items=[<Machine hostname='wanted-falcon' system_id='ekgqwd'>]>
>>> client.devices.list()
<Devices length=0 items=[]>
>>> client.rack_controllers.list()
<RackControllers length=1 items=[<RackController hostname='maas-ctrl' system_id='efw3c4'>]>
>>> client.region_controllers.list()
<RegionControllers length=1 items=[<RegionController hostname='maas-ctrl' system_id='efw3c4'>]>
```

Easily iterate through the machines.

```pycon
>>> for machine in client.machines.list():
...     print(repr(machine))
<Machine hostname='botswana' system_id='pncys4'>
```

Get a machine from its system_id.

```pycon
>>> machine = client.machines.get(system_id="pncys4")
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

## Create nodes

Create a machine in MAAS. The architecture, MAC addresses, and power type are
required fields.

```pycon
>>> machine = client.machines.create(
...     "amd64", ["00:11:22:33:44:55", "AA:BB:CC:DD:EE:FF"], "manual")
<Machine hostname='wanted-falcon' system_id='ekgqwd'>
```

Normally you need to pass in power parameter so MAAS can talk to the BMC.

```pycon
>>> machine = client.machines.create(
...     "amd64", ["00:11:22:33:44:55", "AA:BB:CC:DD:EE:FF"], "ipmi", {
...         "power_address": "10.245.0.10",
...         "power_user": "root",
...         "power_pass": "calvin",
...     })
>>> machine
<Machine hostname='wanted-falcon' system_id='ekgqwd'>
>>> machine.status
<NodeStatus.COMMISSIONING: 1>
```

## Updating nodes

Updating a machine is as simple as modifying the attribute and saving.

```pycon
>>> machine.hostname = 'my-machine'
>>> machine.architecture = 'i386/generic'
>>> machine.save()
```

## Allocating and deploying

```pycon
>>> help(client.machines.allocate)
Help on method allocate in module maas.client.viscera.machines:

allocate(
    *, hostname:str=None, architecture:str=None, cpus:int=None,
    memory:float=None, tags:typing.Sequence=None)
  method of maas.client.viscera.machines.MachinesType instance
    Allocate a machine.

    :param hostname: The hostname to match.
    :param architecture: The architecture to match, e.g. "amd64".
    :param cpus: The minimum number of CPUs to match.
    :param memory: The minimum amount of RAM to match.
    :param tags: The tags to match, as a sequence. Each tag may be
        prefixed with a hyphen to denote that the given tag should NOT be
        associated with a matched machine.
>>> machine = client.machines.allocate(tags=("foo", "-bar"))
>>> print(machine.status)
NodeStatus.COMMISSIONING
>>> machine.deploy()
>>> print(machine.status)
NodeStatus.DEPLOYING
```
