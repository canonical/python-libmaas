"""Test for `maas.client.viscera.interfaces`."""

import random

from testtools.matchers import (
    Equals,
    IsInstance,
)

from ..fabrics import (
    Fabric,
    Fabrics,
)
from ..interfaces import (
    Interface,
    Interfaces,
)
from ..nodes import (
    Node,
    Nodes,
)
from ..vlans import (
    Vlan,
    Vlans,
)

from .. testing import bind
from ...enum import InterfaceType
from ...testing import (
    make_string_without_spaces,
    TestCase,
)


def make_origin():
    """
    Create a new origin with required objects.
    """
    return bind(
        Fabrics, Fabric, Interfaces, Interface, Nodes, Node, Vlans, Vlan)


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

    def test__create_bond_fails_parents_not_sequence(self):
        Interfaces = make_origin().Interfaces
        error = self.assertRaises(
            TypeError, Interfaces.create,
            make_string_without_spaces(), InterfaceType.BOND,
            name=make_string_without_spaces(),
            parents=random.randint(1, 20))
        self.assertEquals(
            "parents must be a sequence, not int", str(error))

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
