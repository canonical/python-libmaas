<h1>Fabrics, VLANs, Subnets, Spaces, IP Ranges, Static Routes</h1>

Given a ``Client`` instance bound to your MAAS server, you can
interrogate your entire networking configuration.

## Read networking

``fabrics``, ``subnets``, ``spaces``, ``ip_ranges``, and ``static_routes`` is
exposed directly on your ``Client`` instance. ``vlans`` are nested under each
``Fabric``.

```pycon
>>> fabrics = client.fabrics.list()
>>> len(fabrics)
1
>>> default_fabric = fabrics.get_default()
>>> default_fabric.name
'fabric-0'
>>> default_fabric.vlans
<Vlans.Managed#Fabric length=1 items=[<Vlan name='untagged' vid=0>]>
>>> for vlan in default_fabric.vlans:
...     print(vlan)
...
<Vlan name='untagged' vid=0>
>>>
```

Get a specific subnet and view the ``Vlan`` and ``Fabric`` that it is
assigned to. Going up the tree from ``Vlan`` to ``Fabric`` results in an
unloaded ``Fabric``. Calling ``refresh`` on ``Fabric`` will load the object
from MAAS.


```pycon
>>> vm_subnet = client.subnets.get('192.168.122.0/24')
>>> vm_subnet.cidr
'192.168.122.0/24'
>>> vm_subnet.vlan
<Vlan name='untagged' vid=0>
>>> fabric = vm_subnet.vlan.fabric
>>> fabric
<Fabric id=20 (unloaded)>
>>> fabric.refresh()
>>> fabric.vlans
Traceback (most recent call last):
...
ObjectNotLoaded: cannot access attribute 'vlans' of object 'Fabric'
>>> fabric.is_loaded
False
>>> fabric.refresh()
>>> fabric.is_loaded
True
>>> fabric.vlans
<Vlans.Managed#Fabric length=1 items=[<Vlan name='untagged' vid=0>]>
```

Access to ``spaces``, ``ip_ranges``, and ``static_routes`` works similarly.

```pycon
>>> client.spaces.list()
>>> client.ip_ranges.list()
>>> client.static_routes.list()
```

## Create fabric & vlan

Creating a new fabric and vlan is done directly from each set of objects on
the ``Client`` respectively.

```pycon
>>> new_fabric = client.fabrics.create()
>>> new_fabric.name
'fabric-2'
>>> new_vlan = new_fabric.vlans.create(20)
>>> new_vlan
<Vlan name='' vid=20>
>>> new_vlan.fabric
<Fabric id=2 (unloaded)>
```

## Create subnet

Create a new subnet and assign it to an existing vlan.

```pycon
>>> new_subnet = client.subnets.create('192.168.128.0/24', new_vlan)
>>> new_subnet.cidr
'192.168.128.0/24'
>>> new_subnet.vlan
<Vlan name='' vid=20>
```

## Update subnet

Quickly move the newly created subnet from vlan to default fabric
untagged vlan.

```pycon
>>> default_fabric = client.fabrics.get_default()
>>> untagged = default_fabric.vlans.get_default()
>>> new_subnet.vlan = untagged
>>> new_subnet.save()
>>> new_subnet.vlan
<Vlan name='untagged' vid=0>
```

## Delete subnet

``delete`` exists directly on the ``Subnet`` object so deletion is simple.

```pycon
>>> new_subnet.delete()
>>>
```

## Enable DHCP

Create a new dynamic IP range and turn DHCP on the selected
rack controller.

```pycon
>>> fabric = client.fabrics.get_default()
>>> untagged = fabric.vlans.get_default()
>>> new_range = client.ip_ranges.create(
...     '192.168.122.100', '192.168.122.200', type=IPRangeType.DYNAMIC)
>>> rack = client.rack_controllers.list()[0]
>>> untagged.dhcp_on = True
>>> untagged.primary_rack = rack
>>> untagged.save()
```
