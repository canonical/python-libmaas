"""Test for `maas.client.viscera.interfaces`."""

import random

from testtools.matchers import (
    Equals,
    IsInstance,
    MatchesAll,
    MatchesSetwise,
    MatchesStructure,
)

from ..fabrics import (
    Fabric,
    Fabrics,
)
from ..interfaces import (
    Interface,
    Interfaces,
    InterfaceDiscoveredLink,
    InterfaceDiscoveredLinks,
    InterfaceLink,
    InterfaceLinks,
)
from ..nodes import (
    Node,
    Nodes,
)
from ..subnets import (
    Subnet,
    Subnets,
)
from ..vlans import (
    Vlan,
    Vlans,
)

from .. testing import bind
from ...enum import (
    InterfaceType,
    LinkMode,
)
from ...testing import (
    make_string_without_spaces,
    TestCase,
)


def make_origin():
    """
    Create a new origin with required objects.
    """
    return bind(
        Fabrics, Fabric, Interfaces, Interface, InterfaceLinks, InterfaceLink,
        InterfaceDiscoveredLinks, InterfaceDiscoveredLink,
        Nodes, Node, Subnets, Subnet, Vlans, Vlan)


class TestInterfaces(TestCase):

    def test__read_bad_node_type(self):
        Interfaces = make_origin().Interfaces
        error = self.assertRaises(
            TypeError, Interfaces.read, random.randint(0, 100))
        self.assertEquals("node must be a Node or str, not int", str(error))

    def test__read_with_system_id(self):
        Interfaces = make_origin().Interfaces
        system_id = make_string_without_spaces()
        interfaces = [
            {
                "system_id": system_id,
                "id": random.randint(0, 100),
                "name": make_string_without_spaces(),
                "type": InterfaceType.PHYSICAL.value,
            }
            for _ in range(3)
        ]
        Interfaces._handler.read.return_value = interfaces
        interfaces = Interfaces.read(system_id)
        self.assertThat(len(interfaces), Equals(3))
        Interfaces._handler.read.assert_called_once_with(system_id=system_id)

    def test__read_with_Node(self):
        origin = make_origin()
        Interfaces, Node = origin.Interfaces, origin.Node
        system_id = make_string_without_spaces()
        node = Node(system_id)
        interfaces = [
            {
                "system_id": system_id,
                "id": random.randint(0, 100),
                "name": make_string_without_spaces(),
                "type": InterfaceType.PHYSICAL.value,
            }
            for _ in range(3)
        ]
        Interfaces._handler.read.return_value = interfaces
        interfaces = Interfaces.read(node)
        self.assertThat(len(interfaces), Equals(3))
        Interfaces._handler.read.assert_called_once_with(system_id=system_id)

    def test__create_bad_node_type(self):
        Interfaces = make_origin().Interfaces
        error = self.assertRaises(
            TypeError, Interfaces.create, random.randint(0, 100))
        self.assertEquals("node must be a Node or str, not int", str(error))

    def test__create_bad_vlan_type(self):
        Interfaces = make_origin().Interfaces
        error = self.assertRaises(
            TypeError, Interfaces.create,
            make_string_without_spaces(), vlan=make_string_without_spaces())
        self.assertEquals("vlan must be a Vlan or int, not str", str(error))

    def test__create_bad_interface_type_type(self):
        Interfaces = make_origin().Interfaces
        error = self.assertRaises(
            TypeError, Interfaces.create,
            make_string_without_spaces(),
            interface_type=make_string_without_spaces())
        self.assertEquals(
            "interface_type must be an InterfaceType, not str", str(error))

    def test__create_physical_requires_mac_address(self):
        Interfaces = make_origin().Interfaces
        error = self.assertRaises(
            ValueError, Interfaces.create,
            make_string_without_spaces())
        self.assertEquals(
            "mac_address required for physical interface", str(error))

    def test__create_physical_with_all_values(self):
        origin = make_origin()
        Interfaces, Interface = origin.Interfaces, origin.Interface
        system_id = make_string_without_spaces()
        mac_address = "00:11:22:33:44:55"
        name = make_string_without_spaces()
        tags = [
            make_string_without_spaces()
            for _ in range(3)
        ]
        mtu = random.randint(1500, 3000)
        vlan = random.randint(1, 20)
        accept_ra = random.choice([True, False])
        autoconf = random.choice([True, False])
        interface_data = {
            'system_id': system_id,
            'id': random.randint(1, 20),
            'type': InterfaceType.PHYSICAL.value,
            'name': name,
            'tags': tags,
        }
        Interfaces._handler.create_physical.return_value = interface_data
        nic = Interfaces.create(
            node=system_id, mac_address=mac_address, name=name,
            tags=tags, mtu=mtu, vlan=vlan,
            accept_ra=accept_ra, autoconf=autoconf)
        self.assertThat(nic, IsInstance(Interface))
        Interfaces._handler.create_physical.assert_called_once_with(
            system_id=system_id, mac_address=mac_address, name=name,
            tags=tags, mtu=mtu, vlan=vlan,
            accept_ra=accept_ra, autoconf=autoconf)

    def test__create_physical_with_objects(self):
        origin = make_origin()
        Interfaces, Interface = origin.Interfaces, origin.Interface
        system_id = make_string_without_spaces()
        node = origin.Node(system_id)
        mac_address = "00:11:22:33:44:55"
        name = make_string_without_spaces()
        tags = [
            make_string_without_spaces()
            for _ in range(3)
        ]
        mtu = random.randint(1500, 3000)
        vlan_id = random.randint(1, 20)
        vlan = origin.Vlan({
            'fabric_id': random.randint(1, 20),
            'id': vlan_id,
        })
        accept_ra = random.choice([True, False])
        autoconf = random.choice([True, False])
        interface_data = {
            'system_id': system_id,
            'id': random.randint(1, 20),
            'type': InterfaceType.PHYSICAL.value,
            'name': name,
            'tags': tags,
        }
        Interfaces._handler.create_physical.return_value = interface_data
        nic = Interfaces.create(
            node=node, mac_address=mac_address, name=name,
            tags=tags, mtu=mtu, vlan=vlan,
            accept_ra=accept_ra, autoconf=autoconf)
        self.assertThat(nic, IsInstance(Interface))
        Interfaces._handler.create_physical.assert_called_once_with(
            system_id=system_id, mac_address=mac_address, name=name,
            tags=tags, mtu=mtu, vlan=vlan_id,
            accept_ra=accept_ra, autoconf=autoconf)

    def test__create_bond_fails_with_parent(self):
        Interfaces = make_origin().Interfaces
        error = self.assertRaises(
            ValueError, Interfaces.create,
            make_string_without_spaces(), InterfaceType.BOND,
            name=make_string_without_spaces(),
            parent=make_string_without_spaces())
        self.assertEquals(
            "use parents not parent for bond interface", str(error))

    def test__create_bond_fails_parents_not_iterable(self):
        Interfaces = make_origin().Interfaces
        error = self.assertRaises(
            TypeError, Interfaces.create,
            make_string_without_spaces(), InterfaceType.BOND,
            name=make_string_without_spaces(),
            parents=random.randint(1, 20))
        self.assertEquals(
            "parents must be a iterable, not int", str(error))

    def test__create_bond_fails_parents_is_not_Interface_or_int(self):
        Interfaces = make_origin().Interfaces
        error = self.assertRaises(
            TypeError, Interfaces.create,
            make_string_without_spaces(), InterfaceType.BOND,
            name=make_string_without_spaces(),
            parents=[make_string_without_spaces()])
        self.assertEquals(
            "parent[0] must be an Interface or int, not str", str(error))

    def test__create_bond_fails_name_missing(self):
        Interfaces = make_origin().Interfaces
        error = self.assertRaises(
            ValueError, Interfaces.create,
            make_string_without_spaces(), InterfaceType.BOND,
            parents=[random.randint(1, 20)])
        self.assertEquals(
            "name is required for bond interface", str(error))

    def test__create_bond_with_all_values(self):
        origin = make_origin()
        Interfaces, Interface = origin.Interfaces, origin.Interface
        system_id = make_string_without_spaces()
        mac_address = "00:11:22:33:44:55"
        name = make_string_without_spaces()
        tags = [
            make_string_without_spaces()
            for _ in range(3)
        ]
        mtu = random.randint(1500, 3000)
        vlan = random.randint(1, 20)
        accept_ra = random.choice([True, False])
        autoconf = random.choice([True, False])
        bond_mode = make_string_without_spaces()
        bond_miimon = random.randint(1, 100)
        bond_downdelay = random.randint(1, 10)
        bond_updelay = random.randint(1, 10)
        bond_lacp_rate = random.choice(['fast', 'slow'])
        bond_xmit_hash_policy = make_string_without_spaces()
        parents = [
            random.randint(1, 10)
            for _ in range(3)
        ]
        interface_data = {
            'system_id': system_id,
            'id': random.randint(1, 20),
            'type': InterfaceType.BOND.value,
            'name': name,
            'tags': tags,
        }
        Interfaces._handler.create_bond.return_value = interface_data
        nic = Interfaces.create(
            node=system_id, interface_type=InterfaceType.BOND,
            parents=parents, mac_address=mac_address, name=name,
            tags=tags, mtu=mtu, vlan=vlan, accept_ra=accept_ra,
            autoconf=autoconf, bond_mode=bond_mode, bond_miimon=bond_miimon,
            bond_downdelay=bond_downdelay, bond_updelay=bond_updelay,
            bond_lacp_rate=bond_lacp_rate,
            bond_xmit_hash_policy=bond_xmit_hash_policy)
        self.assertThat(nic, IsInstance(Interface))
        Interfaces._handler.create_bond.assert_called_once_with(
            system_id=system_id,
            parents=parents, mac_address=mac_address, name=name,
            tags=tags, mtu=mtu, vlan=vlan, accept_ra=accept_ra,
            autoconf=autoconf, bond_mode=bond_mode, bond_miimon=bond_miimon,
            bond_downdelay=bond_downdelay, bond_updelay=bond_updelay,
            bond_lacp_rate=bond_lacp_rate,
            bond_xmit_hash_policy=bond_xmit_hash_policy)

    def test__create_bond_with_objects(self):
        origin = make_origin()
        Interfaces, Interface = origin.Interfaces, origin.Interface
        system_id = make_string_without_spaces()
        node = origin.Node(system_id)
        mac_address = "00:11:22:33:44:55"
        name = make_string_without_spaces()
        tags = [
            make_string_without_spaces()
            for _ in range(3)
        ]
        mtu = random.randint(1500, 3000)
        vlan_id = random.randint(1, 10)
        vlan = origin.Vlan({
            'fabric_id': random.randint(1, 20),
            'id': vlan_id,
        })
        accept_ra = random.choice([True, False])
        autoconf = random.choice([True, False])
        bond_mode = make_string_without_spaces()
        bond_miimon = random.randint(1, 100)
        bond_downdelay = random.randint(1, 10)
        bond_updelay = random.randint(1, 10)
        bond_lacp_rate = random.choice(['fast', 'slow'])
        bond_xmit_hash_policy = make_string_without_spaces()
        parents = [
            random.randint(1, 10)
            for _ in range(3)
        ]
        parent_objs = [
            Interface((system_id, parent))
            for parent in parents
        ]
        interface_data = {
            'system_id': system_id,
            'id': random.randint(1, 20),
            'type': InterfaceType.BOND.value,
            'name': name,
            'tags': tags,
        }
        Interfaces._handler.create_bond.return_value = interface_data
        nic = Interfaces.create(
            node=node, interface_type=InterfaceType.BOND,
            parents=parent_objs, mac_address=mac_address, name=name,
            tags=tags, mtu=mtu, vlan=vlan, accept_ra=accept_ra,
            autoconf=autoconf, bond_mode=bond_mode, bond_miimon=bond_miimon,
            bond_downdelay=bond_downdelay, bond_updelay=bond_updelay,
            bond_lacp_rate=bond_lacp_rate,
            bond_xmit_hash_policy=bond_xmit_hash_policy)
        self.assertThat(nic, IsInstance(Interface))
        Interfaces._handler.create_bond.assert_called_once_with(
            system_id=system_id,
            parents=parents, mac_address=mac_address, name=name,
            tags=tags, mtu=mtu, vlan=vlan_id, accept_ra=accept_ra,
            autoconf=autoconf, bond_mode=bond_mode, bond_miimon=bond_miimon,
            bond_downdelay=bond_downdelay, bond_updelay=bond_updelay,
            bond_lacp_rate=bond_lacp_rate,
            bond_xmit_hash_policy=bond_xmit_hash_policy)

    def test__create_vlan_fails_with_parents(self):
        Interfaces = make_origin().Interfaces
        error = self.assertRaises(
            ValueError, Interfaces.create,
            make_string_without_spaces(), InterfaceType.VLAN,
            parents=[make_string_without_spaces()])
        self.assertEquals(
            "use parent not parents for VLAN interface", str(error))

    def test__create_vlan_fails_without_parent(self):
        Interfaces = make_origin().Interfaces
        error = self.assertRaises(
            ValueError, Interfaces.create,
            make_string_without_spaces(), InterfaceType.VLAN)
        self.assertEquals(
            "parent is required for VLAN interface", str(error))

    def test__create_vlan_fails_parent_wrong_type(self):
        Interfaces = make_origin().Interfaces
        error = self.assertRaises(
            TypeError, Interfaces.create,
            make_string_without_spaces(), InterfaceType.VLAN,
            parent=make_string_without_spaces())
        self.assertEquals(
            "parent must be an Interface or int, not str", str(error))

    def test__create_vlan_fails_without_vlan(self):
        Interfaces = make_origin().Interfaces
        error = self.assertRaises(
            ValueError, Interfaces.create,
            make_string_without_spaces(), InterfaceType.VLAN,
            parent=random.randint(1, 10))
        self.assertEquals(
            "vlan is required for VLAN interface", str(error))

    def test__create_vlan_with_all_values(self):
        origin = make_origin()
        Interfaces, Interface = origin.Interfaces, origin.Interface
        system_id = make_string_without_spaces()
        tags = [
            make_string_without_spaces()
            for _ in range(3)
        ]
        mtu = random.randint(1500, 3000)
        vlan = random.randint(1, 20)
        accept_ra = random.choice([True, False])
        autoconf = random.choice([True, False])
        parent = random.randint(1, 10)
        interface_data = {
            'system_id': system_id,
            'id': random.randint(1, 20),
            'type': InterfaceType.VLAN.value,
            'tags': tags,
        }
        Interfaces._handler.create_vlan.return_value = interface_data
        nic = Interfaces.create(
            node=system_id, interface_type=InterfaceType.VLAN,
            parent=parent, tags=tags, mtu=mtu, vlan=vlan, accept_ra=accept_ra,
            autoconf=autoconf)
        self.assertThat(nic, IsInstance(Interface))
        Interfaces._handler.create_vlan.assert_called_once_with(
            system_id=system_id, parent=parent,
            tags=tags, mtu=mtu, vlan=vlan, accept_ra=accept_ra,
            autoconf=autoconf)

    def test__create_vlan_with_objects(self):
        origin = make_origin()
        Interfaces, Interface = origin.Interfaces, origin.Interface
        system_id = make_string_without_spaces()
        node = origin.Node(system_id)
        tags = [
            make_string_without_spaces()
            for _ in range(3)
        ]
        mtu = random.randint(1500, 3000)
        vlan_id = random.randint(1, 10)
        vlan = origin.Vlan({
            'fabric_id': random.randint(1, 20),
            'id': vlan_id,
        })
        accept_ra = random.choice([True, False])
        autoconf = random.choice([True, False])
        parent_id = random.randint(1, 10)
        parent_obj = Interface((system_id, parent_id))
        interface_data = {
            'system_id': system_id,
            'id': random.randint(1, 20),
            'type': InterfaceType.VLAN.value,
            'tags': tags,
        }
        Interfaces._handler.create_vlan.return_value = interface_data
        nic = Interfaces.create(
            node=node, interface_type=InterfaceType.VLAN,
            parent=parent_obj, tags=tags, mtu=mtu, vlan=vlan,
            accept_ra=accept_ra, autoconf=autoconf)
        self.assertThat(nic, IsInstance(Interface))
        Interfaces._handler.create_vlan.assert_called_once_with(
            system_id=system_id, parent=parent_id,
            tags=tags, mtu=mtu, vlan=vlan_id, accept_ra=accept_ra,
            autoconf=autoconf)

    def test__create_bridge_fails_with_parents(self):
        Interfaces = make_origin().Interfaces
        error = self.assertRaises(
            ValueError, Interfaces.create,
            make_string_without_spaces(), InterfaceType.BRIDGE,
            parents=[make_string_without_spaces()])
        self.assertEquals(
            "use parent not parents for bridge interface", str(error))

    def test__create_bridge_fails_without_parent(self):
        Interfaces = make_origin().Interfaces
        error = self.assertRaises(
            ValueError, Interfaces.create,
            make_string_without_spaces(), InterfaceType.BRIDGE)
        self.assertEquals(
            "parent is required for bridge interface", str(error))

    def test__create_bridge_fails_parent_wrong_type(self):
        Interfaces = make_origin().Interfaces
        error = self.assertRaises(
            TypeError, Interfaces.create,
            make_string_without_spaces(), InterfaceType.BRIDGE,
            parent=make_string_without_spaces())
        self.assertEquals(
            "parent must be an Interface or int, not str", str(error))

    def test__create_bridge_fails_missing_name(self):
        Interfaces = make_origin().Interfaces
        error = self.assertRaises(
            ValueError, Interfaces.create,
            make_string_without_spaces(), InterfaceType.BRIDGE,
            parent=random.randint(1, 10))
        self.assertEquals(
            "name is required for bridge interface", str(error))

    def test__create_bridge_with_all_values(self):
        origin = make_origin()
        Interfaces, Interface = origin.Interfaces, origin.Interface
        system_id = make_string_without_spaces()
        name = make_string_without_spaces()
        mac_address = "00:11:22:33:44:55"
        tags = [
            make_string_without_spaces()
            for _ in range(3)
        ]
        mtu = random.randint(1500, 3000)
        vlan = random.randint(1, 20)
        accept_ra = random.choice([True, False])
        autoconf = random.choice([True, False])
        parent = random.randint(1, 10)
        bridge_stp = random.choice([True, False])
        bridge_fd = random.randint(1, 10)
        interface_data = {
            'system_id': system_id,
            'id': random.randint(1, 20),
            'type': InterfaceType.BRIDGE.value,
            'name': name,
            'tags': tags,
        }
        Interfaces._handler.create_bridge.return_value = interface_data
        nic = Interfaces.create(
            node=system_id, interface_type=InterfaceType.BRIDGE,
            parent=parent, name=name, tags=tags, mtu=mtu, vlan=vlan,
            accept_ra=accept_ra, autoconf=autoconf, mac_address=mac_address,
            bridge_stp=bridge_stp, bridge_fd=bridge_fd)
        self.assertThat(nic, IsInstance(Interface))
        Interfaces._handler.create_bridge.assert_called_once_with(
            system_id=system_id, parent=parent, name=name,
            tags=tags, mtu=mtu, vlan=vlan, accept_ra=accept_ra,
            autoconf=autoconf, mac_address=mac_address,
            bridge_stp=bridge_stp, bridge_fd=bridge_fd)

    def test__create_bridge_with_objects(self):
        origin = make_origin()
        Interfaces, Interface = origin.Interfaces, origin.Interface
        system_id = make_string_without_spaces()
        node = origin.Node(system_id)
        name = make_string_without_spaces()
        mac_address = "00:11:22:33:44:55"
        tags = [
            make_string_without_spaces()
            for _ in range(3)
        ]
        mtu = random.randint(1500, 3000)
        vlan_id = random.randint(1, 10)
        vlan = origin.Vlan({
            'fabric_id': random.randint(1, 20),
            'id': vlan_id,
        })
        accept_ra = random.choice([True, False])
        autoconf = random.choice([True, False])
        parent_id = random.randint(1, 10)
        parent_obj = Interface((system_id, parent_id))
        bridge_stp = random.choice([True, False])
        bridge_fd = random.randint(1, 10)
        interface_data = {
            'system_id': system_id,
            'id': random.randint(1, 20),
            'type': InterfaceType.VLAN.value,
            'name': name,
            'tags': tags,
        }
        Interfaces._handler.create_bridge.return_value = interface_data
        nic = Interfaces.create(
            node=node, interface_type=InterfaceType.BRIDGE,
            parent=parent_obj, name=name, tags=tags, mtu=mtu, vlan=vlan,
            accept_ra=accept_ra, autoconf=autoconf, mac_address=mac_address,
            bridge_stp=bridge_stp, bridge_fd=bridge_fd)
        self.assertThat(nic, IsInstance(Interface))
        Interfaces._handler.create_bridge.assert_called_once_with(
            system_id=system_id, parent=parent_id, name=name,
            tags=tags, mtu=mtu, vlan=vlan_id, accept_ra=accept_ra,
            autoconf=autoconf, mac_address=mac_address,
            bridge_stp=bridge_stp, bridge_fd=bridge_fd)

    def test__create_unknown_fails(self):
        Interfaces = make_origin().Interfaces
        error = self.assertRaises(
            ValueError, Interfaces.create,
            make_string_without_spaces(), InterfaceType.UNKNOWN)
        self.assertEquals(
            "cannot create an interface of type: %s" % InterfaceType.UNKNOWN,
            str(error))

    def test__by_name(self):
        origin = make_origin()
        Interfaces, Interface = origin.Interfaces, origin.Interface
        system_id = make_string_without_spaces()
        eth0_Interface = Interface({
            'system_id': system_id,
            'id': random.randint(0, 100),
            'name': 'eth0',
        })
        eth1_Interface = Interface({
            'system_id': system_id,
            'id': random.randint(0, 100),
            'name': 'eth1',
        })
        interfaces = Interfaces([eth0_Interface, eth1_Interface])
        self.assertEquals({
            'eth0': eth0_Interface,
            'eth1': eth1_Interface,
        }, interfaces.by_name)

    def test__get_by_name(self):
        origin = make_origin()
        Interfaces, Interface = origin.Interfaces, origin.Interface
        system_id = make_string_without_spaces()
        eth0_Interface = Interface({
            'system_id': system_id,
            'id': random.randint(0, 100),
            'name': 'eth0',
        })
        eth1_Interface = Interface({
            'system_id': system_id,
            'id': random.randint(0, 100),
            'name': 'eth1',
        })
        interfaces = Interfaces([eth0_Interface, eth1_Interface])
        eth0 = interfaces.get_by_name('eth0')
        self.assertEquals(eth0, eth0_Interface)


class TestInterface(TestCase):

    def test__interface_read_system_id(self):
        Interface = make_origin().Interface
        system_id = make_string_without_spaces()
        interface = {
            "system_id": system_id,
            "id": random.randint(0, 100),
            "name": make_string_without_spaces(),
            "type": InterfaceType.PHYSICAL.value,
        }
        Interface._handler.read.return_value = interface
        self.assertThat(
            Interface.read(node=system_id, id=interface["id"]),
            Equals(Interface(interface)))
        Interface._handler.read.assert_called_once_with(
            system_id=system_id, id=interface["id"])

    def test__interface_read_Node(self):
        origin = make_origin()
        Interface = origin.Interface
        system_id = make_string_without_spaces()
        interface = {
            "system_id": system_id,
            "id": random.randint(0, 100),
            "name": make_string_without_spaces(),
            "type": InterfaceType.PHYSICAL.value,
        }
        Interface._handler.read.return_value = interface
        self.assertThat(
            Interface.read(node=origin.Node(system_id), id=interface["id"]),
            Equals(Interface(interface)))
        Interface._handler.read.assert_called_once_with(
            system_id=system_id, id=interface["id"])

    def test__interface_read_TypeError(self):
        Interface = make_origin().Interface
        error = self.assertRaises(
            TypeError, Interface.read,
            random.randint(0, 100), random.randint(0, 100))
        self.assertEquals("node must be a Node or str, not int", str(error))

    def test__interface_save_tags(self):
        Interface = make_origin().Interface
        Interface._handler.params = ['system_id', 'id']
        interface = Interface({
            'system_id': make_string_without_spaces(),
            'id': random.randint(0, 100),
            'tags': ['keep', 'update', 'delete'],
            'params': {},
        })
        del interface.tags[2]
        interface.tags[1] = 'updated'
        Interface._handler.update.return_value = {
            'system_id': interface.node.system_id,
            'id': interface.id,
            'tags': ['keep', 'updated'],
            'params': {},
        }
        interface.save()
        Interface._handler.update.assert_called_once_with(
            system_id=interface.node.system_id, id=interface.id,
            tags='keep,updated')

    def test__interface_doesnt_save_tags_if_same_diff_order(self):
        Interface = make_origin().Interface
        Interface._handler.params = ['system_id', 'id']
        interface = Interface({
            'system_id': make_string_without_spaces(),
            'id': random.randint(0, 100),
            'tags': ['keep', 'update', 'delete'],
            'params': {},
        })
        interface.tags = ['delete', 'keep', 'update']
        interface.save()
        self.assertEqual(0, Interface._handler.update.call_count)

    def test__interface_save_passes_parameters(self):
        Interface = make_origin().Interface
        Interface._handler.params = ['system_id', 'id']
        interface = Interface({
            'system_id': make_string_without_spaces(),
            'id': random.randint(0, 100),
            'tags': [],
            'params': {
                'mtu': 1500,
            },
        })
        interface.params['mtu'] = 3000
        Interface._handler.update.return_value = {
            'system_id': interface.node.system_id,
            'id': interface.id,
            'tags': [],
            'params': {
                'mtu': 3000
            },
        }
        interface.save()
        Interface._handler.update.assert_called_once_with(
            system_id=interface.node.system_id, id=interface.id,
            mtu=3000)

    def test__interface_save_handles_str_params(self):
        Interface = make_origin().Interface
        Interface._handler.params = ['system_id', 'id']
        interface = Interface({
            'system_id': make_string_without_spaces(),
            'id': random.randint(0, 100),
            'tags': [],
            'params': '',
        })
        interface.params = {'mtu': 3000}
        Interface._handler.update.return_value = {
            'system_id': interface.node.system_id,
            'id': interface.id,
            'tags': [],
            'params': {
                'mtu': 3000
            },
        }
        interface.save()
        Interface._handler.update.assert_called_once_with(
            system_id=interface.node.system_id, id=interface.id,
            mtu=3000)

    def test__interface_save_sets_vlan_to_None(self):
        Interface = make_origin().Interface
        Interface._handler.params = ['system_id', 'id']
        vlan_data = {
            'fabric_id': random.randint(0, 100),
            'id': random.randint(0, 100),
            'vid': random.randint(0, 100),
        }
        interface = Interface({
            'system_id': make_string_without_spaces(),
            'id': random.randint(0, 100),
            'tags': [],
            'params': {},
            'vlan': vlan_data,
        })
        interface.vlan = None
        Interface._handler.update.return_value = {
            'system_id': interface.node.system_id,
            'id': interface.id,
            'tags': [],
            'params': {},
            'vlan': None,
        }
        interface.save()
        Interface._handler.update.assert_called_once_with(
            system_id=interface.node.system_id, id=interface.id,
            vlan=None)

    def test__interface_save_sets_vlan_to_new_vlan(self):
        origin = make_origin()
        Interface, Vlan = origin.Interface, origin.Vlan
        Interface._handler.params = ['system_id', 'id']
        vlan_data = {
            'fabric_id': random.randint(0, 100),
            'id': random.randint(0, 100),
            'vid': random.randint(0, 100),
        }
        interface = Interface({
            'system_id': make_string_without_spaces(),
            'id': random.randint(0, 100),
            'tags': [],
            'params': {},
            'vlan': vlan_data,
        })
        new_vlan = Vlan({
            'fabric_id': random.randint(0, 100),
            'id': random.randint(101, 200),
            'vid': random.randint(0, 100),
        })
        interface.vlan = new_vlan
        Interface._handler.update.return_value = {
            'system_id': interface.node.system_id,
            'id': interface.id,
            'tags': [],
            'params': {},
            'vlan': new_vlan._data,
        }
        interface.save()
        Interface._handler.update.assert_called_once_with(
            system_id=interface.node.system_id, id=interface.id,
            vlan=new_vlan.id)

    def test__interface_save_doesnt_change_vlan_when_same(self):
        origin = make_origin()
        Interface, Vlan = origin.Interface, origin.Vlan
        Interface._handler.params = ['system_id', 'id']
        vlan_data = {
            'fabric_id': random.randint(0, 100),
            'id': random.randint(0, 100),
            'vid': random.randint(0, 100),
        }
        vlan = Vlan(dict(vlan_data))
        interface = Interface({
            'system_id': make_string_without_spaces(),
            'id': random.randint(0, 100),
            'tags': [],
            'params': {},
            'vlan': vlan_data,
        })
        interface.vlan = vlan
        interface.save()
        self.assertEqual(0, Interface._handler.update.call_count)

    def test__interface_delete(self):
        Interface = make_origin().Interface
        system_id = make_string_without_spaces()
        interface_data = {
            "system_id": system_id,
            "id": random.randint(0, 100),
            "name": make_string_without_spaces(),
            "type": InterfaceType.PHYSICAL.value,
        }
        interface = Interface(interface_data)
        interface.delete()
        Interface._handler.delete.assert_called_once_with(
            system_id=system_id, id=interface_data['id'])

    def test__interface_disconnect(self):
        Interface = make_origin().Interface
        system_id = make_string_without_spaces()
        interface_data = {
            "system_id": system_id,
            "id": random.randint(0, 100),
            "name": make_string_without_spaces(),
            "type": InterfaceType.PHYSICAL.value,
            "links": [
                {
                    'id': random.randint(0, 100),
                    'mode': LinkMode.AUTO.value,
                },
            ],
        }
        interface = Interface(interface_data)
        updated_data = dict(interface_data)
        updated_data['links'] = []
        Interface._handler.disconnect.return_value = updated_data
        interface.disconnect()
        Interface._handler.disconnect.assert_called_once_with(
            system_id=system_id, id=interface_data['id'])
        self.assertEquals([], list(interface.links))

    def test__interface_links_create_raises_TypeError_no_Interface(self):
        origin = make_origin()
        InterfaceLinks = origin.InterfaceLinks
        error = self.assertRaises(
            TypeError, InterfaceLinks.create,
            random.randint(0, 1000), LinkMode.AUTO)
        self.assertEquals(
            "interface must be an Interface, not int", str(error))

    def test__interface_links_create_raises_TypeError_no_LinkMode(self):
        origin = make_origin()
        Interface, InterfaceLinks = origin.Interface, origin.InterfaceLinks
        interface = Interface({
            'system_id': make_string_without_spaces(),
            'id': random.randint(0, 100),
        })
        error = self.assertRaises(
            TypeError, InterfaceLinks.create,
            interface, LinkMode.AUTO.value)
        self.assertEquals(
            "mode must be a LinkMode, not str", str(error))

    def test__interface_links_create_raises_TypeError_no_Subnet(self):
        origin = make_origin()
        Interface, InterfaceLinks = origin.Interface, origin.InterfaceLinks
        interface = Interface({
            'system_id': make_string_without_spaces(),
            'id': random.randint(0, 100),
        })
        error = self.assertRaises(
            TypeError, InterfaceLinks.create,
            interface, LinkMode.AUTO,
            subnet=make_string_without_spaces())
        self.assertEquals(
            "subnet must be a Subnet or int, not str", str(error))

    def test__interface_links_create_raises_ValueError_AUTO_no_Subnet(self):
        origin = make_origin()
        Interface, InterfaceLinks = origin.Interface, origin.InterfaceLinks
        interface = Interface({
            'system_id': make_string_without_spaces(),
            'id': random.randint(0, 100),
        })
        error = self.assertRaises(
            ValueError, InterfaceLinks.create,
            interface, LinkMode.AUTO)
        self.assertEquals(
            "subnet is required for %s" % LinkMode.AUTO, str(error))

    def test__interface_links_create_raises_ValueError_STATIC_no_Subnet(self):
        origin = make_origin()
        Interface, InterfaceLinks = origin.Interface, origin.InterfaceLinks
        interface = Interface({
            'system_id': make_string_without_spaces(),
            'id': random.randint(0, 100),
        })
        error = self.assertRaises(
            ValueError, InterfaceLinks.create,
            interface, LinkMode.STATIC)
        self.assertEquals(
            "subnet is required for %s" % LinkMode.STATIC, str(error))

    def test__interface_links_create_raises_ValueError_LINK_UP_gateway(self):
        origin = make_origin()
        Interface, InterfaceLinks = origin.Interface, origin.InterfaceLinks
        interface = Interface({
            'system_id': make_string_without_spaces(),
            'id': random.randint(0, 100),
        })
        error = self.assertRaises(
            ValueError, InterfaceLinks.create,
            interface, LinkMode.LINK_UP, default_gateway=True)
        self.assertEquals(
            "cannot set as default_gateway for %s" % LinkMode.LINK_UP,
            str(error))

    def test__interface_links_create_raises_ValueError_DHCP_gateway(self):
        origin = make_origin()
        Interface, InterfaceLinks = origin.Interface, origin.InterfaceLinks
        interface = Interface({
            'system_id': make_string_without_spaces(),
            'id': random.randint(0, 100),
        })
        error = self.assertRaises(
            ValueError, InterfaceLinks.create,
            interface, LinkMode.DHCP, default_gateway=True)
        self.assertEquals(
            "cannot set as default_gateway for %s" % LinkMode.DHCP,
            str(error))

    def test__interface_links_create_AUTO(self):
        origin = make_origin()
        Interface, Subnet = origin.Interface, origin.Subnet
        system_id = make_string_without_spaces()
        interface_data = {
            "system_id": system_id,
            "id": random.randint(0, 100),
            "name": make_string_without_spaces(),
            "type": InterfaceType.PHYSICAL.value,
            "links": [
                {
                    'id': random.randint(0, 100),
                    'mode': LinkMode.LINK_UP.value,
                    'subnet': {
                        'id': random.randint(0, 100),
                    }
                },
            ],
        }
        interface = Interface(interface_data)
        updated_data = dict(interface_data)
        link_id = random.randint(100, 200)
        subnet_id = random.randint(1, 100)
        updated_data['links'] = [
            {
                'id': link_id,
                'mode': LinkMode.AUTO.value,
                'subnet': {
                    'id': subnet_id,
                }
            }
        ]
        Interface._handler.link_subnet.return_value = updated_data
        interface.links.create(LinkMode.AUTO, subnet_id)
        Interface._handler.link_subnet.assert_called_once_with(
            system_id=interface.node.system_id, id=interface.id,
            mode=LinkMode.AUTO.value, subnet=subnet_id, force=False,
            default_gateway=False)
        self.assertThat(interface.links, MatchesSetwise(
            MatchesStructure(
                id=Equals(link_id), mode=Equals(LinkMode.AUTO),
                subnet=MatchesAll(
                    IsInstance(Subnet),
                    MatchesStructure(id=Equals(subnet_id))))))

    def test__interface_links_create_STATIC(self):
        origin = make_origin()
        Interface, Subnet = origin.Interface, origin.Subnet
        system_id = make_string_without_spaces()
        interface_data = {
            "system_id": system_id,
            "id": random.randint(0, 100),
            "name": make_string_without_spaces(),
            "type": InterfaceType.PHYSICAL.value,
            "links": [
                {
                    'id': random.randint(0, 100),
                    'mode': LinkMode.LINK_UP.value,
                    'subnet': {
                        'id': random.randint(0, 100),
                    }
                },
            ],
        }
        interface = Interface(interface_data)
        updated_data = dict(interface_data)
        link_id = random.randint(100, 200)
        subnet_id = random.randint(1, 100)
        updated_data['links'] = [
            {
                'id': link_id,
                'mode': LinkMode.STATIC.value,
                'ip_address': '192.168.122.10',
                'subnet': {
                    'id': subnet_id,
                }
            }
        ]
        Interface._handler.link_subnet.return_value = updated_data
        interface.links.create(
            LinkMode.STATIC, subnet=Subnet(subnet_id),
            ip_address='192.168.122.10', default_gateway=True, force=True)
        Interface._handler.link_subnet.assert_called_once_with(
            system_id=interface.node.system_id, id=interface.id,
            mode=LinkMode.STATIC.value, subnet=subnet_id,
            ip_address='192.168.122.10', force=True, default_gateway=True)
        self.assertThat(interface.links, MatchesSetwise(
            MatchesStructure(
                id=Equals(link_id), mode=Equals(LinkMode.STATIC),
                ip_address=Equals('192.168.122.10'),
                subnet=MatchesAll(
                    IsInstance(Subnet),
                    MatchesStructure(id=Equals(subnet_id))))))

    def test__interface_links_create_DHCP(self):
        origin = make_origin()
        Interface, Subnet = origin.Interface, origin.Subnet
        system_id = make_string_without_spaces()
        interface_data = {
            "system_id": system_id,
            "id": random.randint(0, 100),
            "name": make_string_without_spaces(),
            "type": InterfaceType.PHYSICAL.value,
            "links": [
                {
                    'id': random.randint(0, 100),
                    'mode': LinkMode.LINK_UP.value,
                    'subnet': {
                        'id': random.randint(0, 100),
                    }
                },
            ],
        }
        interface = Interface(interface_data)
        updated_data = dict(interface_data)
        link_id = random.randint(100, 200)
        subnet_id = random.randint(1, 100)
        updated_data['links'] = [
            {
                'id': link_id,
                'mode': LinkMode.DHCP.value,
                'subnet': {
                    'id': subnet_id,
                }
            }
        ]
        Interface._handler.link_subnet.return_value = updated_data
        interface.links.create(
            LinkMode.DHCP, subnet=Subnet(subnet_id))
        Interface._handler.link_subnet.assert_called_once_with(
            system_id=interface.node.system_id, id=interface.id,
            mode=LinkMode.DHCP.value, subnet=subnet_id,
            default_gateway=False, force=False)
        self.assertThat(interface.links, MatchesSetwise(
            MatchesStructure(
                id=Equals(link_id), mode=Equals(LinkMode.DHCP),
                subnet=MatchesAll(
                    IsInstance(Subnet),
                    MatchesStructure(id=Equals(subnet_id))))))

    def test__interface_links_create_LINK_UP(self):
        origin = make_origin()
        Interface, Subnet = origin.Interface, origin.Subnet
        system_id = make_string_without_spaces()
        interface_data = {
            "system_id": system_id,
            "id": random.randint(0, 100),
            "name": make_string_without_spaces(),
            "type": InterfaceType.PHYSICAL.value,
            "links": [],
        }
        interface = Interface(interface_data)
        updated_data = dict(interface_data)
        link_id = random.randint(0, 100)
        subnet_id = random.randint(1, 100)
        updated_data['links'] = [
            {
                'id': link_id,
                'mode': LinkMode.LINK_UP.value,
                'subnet': {
                    'id': subnet_id,
                }
            }
        ]
        Interface._handler.link_subnet.return_value = updated_data
        interface.links.create(
            LinkMode.LINK_UP, subnet=Subnet(subnet_id))
        Interface._handler.link_subnet.assert_called_once_with(
            system_id=interface.node.system_id, id=interface.id,
            mode=LinkMode.LINK_UP.value, subnet=subnet_id,
            default_gateway=False, force=False)
        self.assertThat(interface.links, MatchesSetwise(
            MatchesStructure(
                id=Equals(link_id), mode=Equals(LinkMode.LINK_UP),
                subnet=MatchesAll(
                    IsInstance(Subnet),
                    MatchesStructure(id=Equals(subnet_id))))))

    def test__interface_links_delete(self):
        origin = make_origin()
        Interface, Subnet = origin.Interface, origin.Subnet
        system_id = make_string_without_spaces()
        link_id = random.randint(0, 100)
        subnet_id = random.randint(1, 100)
        interface_data = {
            "system_id": system_id,
            "id": random.randint(0, 100),
            "name": make_string_without_spaces(),
            "type": InterfaceType.PHYSICAL.value,
            "links": [
                {
                    'id': link_id,
                    'mode': LinkMode.AUTO.value,
                    'subnet': {
                        'id': subnet_id,
                    }
                }
            ],
        }
        interface = Interface(interface_data)
        updated_data = dict(interface_data)
        new_link_id = random.randint(0, 100)
        new_subnet_id = random.randint(1, 100)
        updated_data['links'] = [
            {
                'id': new_link_id,
                'mode': LinkMode.LINK_UP.value,
                'subnet': {
                    'id': new_subnet_id,
                }
            }
        ]
        Interface._handler.unlink_subnet.return_value = updated_data
        interface.links[0].delete()
        Interface._handler.unlink_subnet.assert_called_once_with(
            system_id=interface.node.system_id, id=interface.id, _id=link_id)
        self.assertThat(interface.links, MatchesSetwise(
            MatchesStructure(
                id=Equals(new_link_id), mode=Equals(LinkMode.LINK_UP),
                subnet=MatchesAll(
                    IsInstance(Subnet),
                    MatchesStructure(id=Equals(new_subnet_id))))))

    def test__interface_links_set_as_default_gateway(self):
        origin = make_origin()
        Interface = origin.Interface
        system_id = make_string_without_spaces()
        link_id = random.randint(0, 100)
        subnet_id = random.randint(1, 100)
        interface_data = {
            "system_id": system_id,
            "id": random.randint(0, 100),
            "name": make_string_without_spaces(),
            "type": InterfaceType.PHYSICAL.value,
            "links": [
                {
                    'id': link_id,
                    'mode': LinkMode.AUTO.value,
                    'subnet': {
                        'id': subnet_id,
                    }
                }
            ],
        }
        interface = Interface(interface_data)
        interface.links[0].set_as_default_gateway()
        Interface._handler.set_default_gateway.assert_called_once_with(
            system_id=interface.node.system_id, id=interface.id,
            link_id=link_id)
