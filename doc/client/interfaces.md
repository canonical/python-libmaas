<h1>Interfaces</h1>

Given an ``Node`` instance bound to your MAAS server, you can
view and modify its interface configuration. This applies to all ``Machine``,
``Device``, ``RackController``, and ``RegionController``.

## Read interfaces

All ``Node`` objects have an ``interfaces`` property that provide a sequence of
all ``Interface``'s on the ``Node``.

```pycon
>>> machine.interfaces
<Interfaces.Managed#Machine length=1 items=[
  <Interface mac_address='52:54:00:b4:7e:8c' name='ens3'
    type=<InterfaceType.PHYSICAL: 'physical'>>]>
>>> machine.boot_interface
<Interface mac_address='52:54:00:b4:7e:8c' name='ens3'
  type=<InterfaceType.PHYSICAL: 'physical'>>
```

On bond, VLAN, and bridge interfaces you can get the parents that make the
interface. You can also go the other direction and view the children interfaces
that are using this interface.

**Note:** Parent and children objects are unloaded so they must be loaded to
access the properties of the object.

```pycon
>>> bond.parents
<Interfaces.Managed#Interface length=2 items=[
  <Interface name='ens3'
    node=<Node system_id='yr7fym' (unloaded)> (unloaded)>,
  <Interface name='ens4'
    node=<Node system_id='yr7fym' (unloaded)> (unloaded)>,
  ]>
>>> ens3 = bond.parents[0]
>>> ens3.loaded
False
>>> ens3.refresh()
>>> ens3.type
<InterfaceType.PHYSICAL: 'physical'>
>>> ens3.children
<Interfaces.Managed#Interface length=1 items=[
  <Interface name='bond0'
    node=<Node system_id='yr7fym' (unloaded)> (unloaded)>,
  ]>
```

## Get interface by name

The ``interfaces`` property on ``Node`` gives you access to all interfaces on
the node. Sometimes you want to access the interface objects by name.
``by_name`` and ``get_by_name`` are helpers on ``Interfaces`` that help.

```pycon
>>> machine.interfaces.by_name
{'bond0': <Interface mac_address='52:54:00:b4:7e:8c'
    name='bond0' type=<InterfaceType.BOND: 'bond'>>,
 'ens3': <Interface mac_address='52:54:00:b4:7e:8c'
     name='ens3' type=<InterfaceType.PHYSICAL: 'physical'>>,
 'ens8': <Interface mac_address='52:54:00:11:f3:d2'
    name='ens8' type=<InterfaceType.PHYSICAL: 'physical'>>}
>>> bond = machine.interfaces.get_by_name('bond0')
>>> bond
<Interface mac_address='52:54:00:b4:7e:8c'
    name='bond0' type=<InterfaceType.BOND: 'bond'>>
```

## Read IP configuration

Every ``Interface`` has a ``links`` property that provides all the IP
information on how the interface is configured.

```pycon
>>> bond.links
<InterfaceLinks.Managed#Interface length=1 items=[
  <InterfaceLink ip_address=None mode=<LinkMode.AUTO: 'auto'>
    subnet=<Subnet cidr='192.168.122.0/24' name='192.168.122.0/24'
      vlan=<Vlan name='untagged' vid=0>>>]>
```

## Create physical

Creation of interfaces is done directly on the ``interfaces`` property of a
``Node``. Physical interface is the default type for the ``create`` method so
only ``mac_address`` is required.

```pycon
>>> new_phy = machine.interfaces.create(mac_address="00:11:22:aa:bb:cc")
>>> new_phy
<Interface mac_address='00:11:22:aa:bb:cc' name='eth0'
  type=<InterfaceType.PHYSICAL: 'physical'>>
```

By default the interface is created disconnected. To create it the interface
with it connected to a VLAN pass the ``vlan`` parameter.

```pycon
>>> default_vlan = client.fabrics.get_default().vlans.get_default()
>>> new_phy = machine.interfaces.create(
...    mac_address="00:11:22:aa:bb:cc", vlan=default_vlan)
>>> new_phy
<Interface mac_address='00:11:22:aa:bb:cc' name='eth0'
  type=<InterfaceType.PHYSICAL: 'physical'>>
>>> new_phy.vlan
<Vlan name='untagged' vid=0>
```

## Create bond

Bond creation is the same as creating a physical interface but an
``InterfaceType`` is provided with options specific for a bond.

```pycon
>>> new_bond = machine.interfaces.create(
...    InterfaceType.BOND, name='bond0', parents=machine.interfaces,
...    bond_mode='802.3ad')
>>> new_bond
<Interface mac_address='52:54:00:b4:7e:8c' name='bond0'
  type=<InterfaceType.BOND: 'bond'>>
>>> new_bond.params
{'bond_downdelay': 0,
 'bond_lacp_rate': 'slow',
 'bond_miimon': 100,
 'bond_mode': '802.3ad',
 'bond_updelay': 0,
 'bond_xmit_hash_policy': 'layer2'}
```

## Create vlan

VLAN creation only requires a single parent and a tagged VLAN to connect
the interface to.

```pycon
>>> default_fabric = client.fabrics.get_default()
>>> vlan_10 = default_fabric.vlans.create(10)
>>> vlan_nic = machine.interfaces.create(
...     InterfaceType.VLAN, parent=new_bond, vlan=vlan_10)
>>> vlan_nic
<Interface mac_address='52:54:00:b4:7e:8c' name='bond0.10'
  type=<InterfaceType.VLAN: 'vlan'>>
```

## Create bridge

Bridge creation only requires the name and parent interface you want the
bridge to be created on.

```pycon
>>> bridge_nic = machine.interfaces.create(
...     InterfaceType.BRIDGE, name='br0', parent=vlan_nic)
>>> bridge_nic
<Interface mac_address='52:54:00:b4:7e:8c' name='br0'
  type=<InterfaceType.BRIDGE: 'bridge'>>
```

## Update interface

To update an interface just changing the properties of the interface and
calling ``save`` is all that is required.

```pycon
>>> new_bond.name = 'my-bond'
>>> new_bond.params['bond_mode'] = 'active-backup'
>>> new_bond.save()
```

## Change IP configuration

To adjust the IP configuration on a specific interface ``create`` on the
``links`` property and ``delete`` on the ``InterfaceLink`` can be used.

```pycon
>>> new_bond.links.create(LinkMode.AUTO, subnet=subnet)
<InterfaceLink ip_address=None mode=<LinkMode.AUTO: 'auto'>
  subnet=<Subnet cidr='192.168.122.0/24' name='192.168.122.0/24'
    vlan=<Vlan name='untagged' vid=0>>>
>>> new_bond.links[-1].delete()
>>> new_bond.links.create(
...     LinkMode.STATIC, subnet=subnet, ip_address='192.168.122.1')
<InterfaceLink ip_address='192.168.122.10' mode=<LinkMode.STATIC: 'static'>
  subnet=<Subnet cidr='192.168.122.0/24' name='192.168.122.0/24'
    vlan=<Vlan name='untagged' vid=0>>>
>>> new_bond.links[-1].delete()
```

## Disconnect interface

To completely mark an interface as disconnected and remove all configuration
the ``disconnect`` call makes this easy.

```
>>> new_bond.disconnect()
```

## Delete interface

``delete`` exists directly on the ``Interface`` object so deletion is simple.

```pycon
>>> new_bond.delete()
```
