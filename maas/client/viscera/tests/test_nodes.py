"""Test for `maas.client.viscera.nodes`."""

from testtools.matchers import Equals

from .. import nodes
from ..controllers import (
    RackController,
    RegionController,
)
from ..devices import Device
from ..machines import Machine
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
        nodes.Nodes, nodes.Node, Device, Machine,
        RackController, RegionController)


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
