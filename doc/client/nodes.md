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

## Deleting nodes

Delete a machine is simple as calling delete on the machine object.

```pycon
>>> machine.delete()
```

## Commissioning and testing

Easily commission a machine and wait until it successfully completes. By
default the `commission` method waits until commissioning succeeds.

```pycon
>>> machine.commission()
>>> machine.status
NodeStatus.READY
```

A more advanced asyncio based script that runs commissioning with extra scripts
and waits until all machines have successfully commissioned.

```python
#!/usr/bin/env python3.5

import asyncio

from maas.client import login
from maas.client.enum import NodeStatus
from maas.client.utils.async import asynchronous


@asynchronous
async def commission_all_machines():
    client = await login(
        "http://eucula.local:5240/MAAS/",
        username="gavin", password="f00b4r")

    # Get all machines that are in the NEW status.
    all_machines = await client.machines.list()
    new_machines = [
        machine
        for machine in all_machines
        if machine.status == NodeStatus.NEW
    ]

    # Run commissioning with a custom commissioning script on all new machines.
    for machine in new_machines:
        machine.commission(
            commissioning_scripts=['clear_hardware_raid'], wait=False)

    # Wait until all machines are ready.
    failed_machines = []
    completed_machines = []
    while len(new_machines) > 0:
        await asyncio.sleep(5)
        for machine in list(new_machines):
            await machine.refresh()
            if machine.status in [
                    NodeStatus.COMMISSIONING, NodeStatus.TESTING]:
                # Machine is still commissioning or testing.
                continue
            elif machine.status == NodeStatus.READY:
                # Machine is complete.
                completed_machines.append(machine)
                new_machines.remove(machine)
            else:
                # Machine has failed commissioning.
                failed_machines.append(machine)
                new_machines.remove(machine)

    # Print message if any machines failed to commission.
    if len(failed_machines) > 0:
        for machine in failed_machines:
            print("%s: transitioned to unexpected status - %s" % (
                machine.hostname, machine.status_name))
    else:
        print("Successfully commissioned %d machines." % len(
            completed_machines))


commission_all_machines()
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

## Abort

If an action is performed on a machine and it needs to be aborted before it
finishes ``abort`` can be used.

```pycon
>>> machine.commission(wait=False)
>>> machine.status
NodeStatus.COMMISSIONING
>>> machine.abort()
>>> machine.status
NodeStatus.NEW
```

## Rescue mode

Boot the machine into rescue mode and then exit.

```pycon
>>> machine.enter_rescue_mode()
>>> machine.exit_rescue_mode()
```

## Broken & Fixed

When a machine is identified as broken you can easily mark it broken and then
fixed once the issue is resolved.

```pycon
>>> machine.mark_broken()
>>> machine.status
NodeStatus.BROKEN
>>> machine.mark_fixed()
>>> machine.status
NodeStatus.READY
```
