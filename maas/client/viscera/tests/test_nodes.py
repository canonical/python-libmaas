"""Test for `maas.client.viscera.nodes`."""

from copy import deepcopy

from testtools.matchers import Equals

from .. import nodes
from ..controllers import (
    RackController,
    RegionController,
)
from ..devices import Device
from ..domains import Domain
from ..machines import Machine
from ..resource_pools import ResourcePool
from ..testing import bind
from ...enum import NodeType
from ...testing import (
    make_name_without_spaces,
    TestCase,
)


def make_origin():
    # Create a new origin with Nodes and Node. The former refers to the
    # latter via the origin, hence why it must be bound.
    return bind(
        nodes.Nodes, nodes.Node, Device, Domain, Machine,
        RackController, RegionController, ResourcePool)


class TestNode(TestCase):

    def test__string_representation_includes_only_system_id_and_hostname(self):
        node = nodes.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        })
        self.assertThat(repr(node), Equals(
            "<Node hostname=%(hostname)r system_id=%(system_id)r>"
            % node._data))

    def test__read(self):
        data = {
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        }

        origin = make_origin()
        origin.Node._handler.read.return_value = data

        node_observed = origin.Node.read(data["system_id"])
        node_expected = origin.Node(data)
        self.assertThat(node_observed, Equals(node_expected))

    def test__read_domain(self):
        domain = {
            "name": make_name_without_spaces("domain")
        }
        data = {
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "domain": domain,
        }
        origin = make_origin()
        origin.Node._handler.read.return_value = data
        node = origin.Node.read(data["system_id"])
        domain = origin.Domain(domain)
        self.assertThat(node.domain, Equals(domain))

    def test__save_change_pool(self):
        pool_data = {"id": 1, "name": "pool1", "description": "pool1"}
        new_pool_data = {"id": 2, "name": "pool2", "description": "pool2"}
        system_id = make_name_without_spaces("system-id")
        node_data = {
            "id": 1,
            "system_id": system_id,
            "hostname": make_name_without_spaces("hostname"),
            "pool": pool_data,
        }

        origin = make_origin()
        origin.ResourcePool._handler.read.return_value = new_pool_data
        origin.Node._handler.params = ['system_id', 'id']
        origin.Node._handler.read.return_value = node_data
        origin.Node._handler.update.return_value = deepcopy(node_data)
        origin.Node._handler.update.return_value['pool'] = new_pool_data

        new_pool = origin.ResourcePool.read(2)
        node = origin.Node.read(system_id)
        node.pool = new_pool
        node.save()
        origin.Node._handler.update.assert_called_once_with(
            id=1, pool="pool2", system_id=system_id)

    def test__save_change_domain(self):
        domain_data = {"id": 1, "name": "domain1"}
        new_domain_data = {"id": 2, "name": "domain2"}
        system_id = make_name_without_spaces("system-id")
        node_data = {
            "id": 1,
            "system_id": system_id,
            "hostname": make_name_without_spaces("hostname"),
            "domain": domain_data,
        }

        origin = make_origin()
        origin.Domain._handler.read.return_value = new_domain_data
        origin.Node._handler.params = ['system_id', 'id']
        origin.Node._handler.read.return_value = node_data
        origin.Node._handler.update.return_value = deepcopy(node_data)
        origin.Node._handler.update.return_value['domain'] = new_domain_data

        new_domain = origin.Domain.read(2)
        node = origin.Node.read(system_id)
        node.domain = new_domain
        node.save()
        origin.Node._handler.update.assert_called_once_with(
            id=1, domain=2, system_id=system_id)

    def test__as_machine_requires_machine_type(self):
        origin = make_origin()
        device_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.DEVICE.value,
        })
        rack_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.RACK_CONTROLLER.value,
        })
        region_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.REGION_CONTROLLER.value,
        })
        region_rack_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.REGION_AND_RACK_CONTROLLER.value,
        })
        self.assertRaises(ValueError, device_node.as_machine)
        self.assertRaises(ValueError, rack_node.as_machine)
        self.assertRaises(ValueError, region_node.as_machine)
        self.assertRaises(ValueError, region_rack_node.as_machine)

    def test__as_machine_returns_machine_type(self):
        origin = make_origin()
        machine_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.MACHINE.value,
        })
        machine = machine_node.as_machine()
        self.assertIsInstance(machine, Machine)

    def test__as_device_requires_device_type(self):
        origin = make_origin()
        machine_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.MACHINE.value,
        })
        rack_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.RACK_CONTROLLER.value,
        })
        region_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.REGION_CONTROLLER.value,
        })
        region_rack_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.REGION_AND_RACK_CONTROLLER.value,
        })
        self.assertRaises(ValueError, machine_node.as_device)
        self.assertRaises(ValueError, rack_node.as_device)
        self.assertRaises(ValueError, region_node.as_device)
        self.assertRaises(ValueError, region_rack_node.as_device)

    def test__as_device_returns_device_type(self):
        origin = make_origin()
        device_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.DEVICE.value,
        })
        device = device_node.as_device()
        self.assertIsInstance(device, Device)

    def test__as_rack_controller_requires_rack_types(self):
        origin = make_origin()
        machine_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.MACHINE.value,
        })
        device_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.DEVICE.value,
        })
        region_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.REGION_CONTROLLER.value,
        })
        self.assertRaises(ValueError, machine_node.as_rack_controller)
        self.assertRaises(ValueError, device_node.as_rack_controller)
        self.assertRaises(ValueError, region_node.as_rack_controller)

    def test__as_rack_controller_returns_rack_type(self):
        origin = make_origin()
        rack_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.RACK_CONTROLLER.value,
        })
        region_rack_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.REGION_AND_RACK_CONTROLLER.value,
        })
        rack = rack_node.as_rack_controller()
        region_rack = region_rack_node.as_rack_controller()
        self.assertIsInstance(rack, RackController)
        self.assertIsInstance(region_rack, RackController)

    def test__as_region_controller_requires_region_types(self):
        origin = make_origin()
        machine_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.MACHINE.value,
        })
        device_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.DEVICE.value,
        })
        rack_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.RACK_CONTROLLER.value,
        })
        self.assertRaises(ValueError, machine_node.as_region_controller)
        self.assertRaises(ValueError, device_node.as_region_controller)
        self.assertRaises(ValueError, rack_node.as_region_controller)

    def test__as_region_controller_returns_region_type(self):
        origin = make_origin()
        region_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.REGION_CONTROLLER.value,
        })
        region_rack_node = origin.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "node_type": NodeType.REGION_AND_RACK_CONTROLLER.value,
        })
        region = region_node.as_region_controller()
        region_rack = region_rack_node.as_region_controller()
        self.assertIsInstance(region, RegionController)
        self.assertIsInstance(region_rack, RegionController)

    def test__delete(self):
        Node = make_origin().Node

        system_id = make_name_without_spaces("system-id")
        node = Node({
            "id": 1,
            "system_id": system_id,
            "hostname": make_name_without_spaces("hostname"),
        })

        node.delete()
        Node._handler.delete.assert_called_once_with(system_id=node.system_id)


class TestNodes(TestCase):

    def test__read(self):
        data = {
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        }

        origin = make_origin()
        origin.Nodes._handler.read.return_value = [data]

        nodes_observed = origin.Nodes.read()
        nodes_expected = origin.Nodes([origin.Node(data)])
        self.assertThat(nodes_observed, Equals(nodes_expected))

    def test__read_with_hostnames(self):
        origin = make_origin()
        origin.Nodes._handler.read.return_value = []

        hostnames = [
            make_name_without_spaces()
            for _ in range(3)
        ]
        origin.Nodes.read(hostnames=hostnames)
        origin.Nodes._handler.read.assert_called_once_with(hostname=hostnames)

    def test__read_with_normalized_hostnames(self):
        origin = make_origin()
        origin.Nodes._handler.read.return_value = []

        hostnames = [
            make_name_without_spaces()
            for _ in range(3)
        ]
        origin.Nodes.read(hostnames=[
            '%s.%s' % (hostname, make_name_without_spaces())
            for hostname in hostnames
        ])
        origin.Nodes._handler.read.assert_called_once_with(hostname=hostnames)
