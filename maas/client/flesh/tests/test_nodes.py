"""Tests for `maas.client.flesh.nodes`."""

from operator import itemgetter
import yaml

from .testing import TestCaseWithProfile
from .. import (
    ArgumentParser,
    nodes,
    tabular
)
from ...enum import NodeType
from ...testing import make_name_without_spaces
from ...viscera.testing import bind
from ...viscera.nodes import (
    Node,
    Nodes
)


def make_origin():
    """Make origin for nodes."""
    return bind(Nodes, Node)


class TestNodes(TestCaseWithProfile):
    """Tests for `cmd_nodes`."""

    def test_returns_table_with_nodes(self):
        origin = make_origin()
        parser = ArgumentParser()
        node_obj = [
            {
                'hostname': make_name_without_spaces(),
                'node_type': NodeType.MACHINE.value,
            },
            {
                'hostname': make_name_without_spaces(),
                'node_type': NodeType.DEVICE.value,
            },
            {
                'hostname': make_name_without_spaces(),
                'node_type': NodeType.RACK_CONTROLLER.value,
            },
            {
                'hostname': make_name_without_spaces(),
                'node_type': NodeType.REGION_CONTROLLER.value,
            },
            {
                'hostname': make_name_without_spaces(),
                'node_type': NodeType.REGION_AND_RACK_CONTROLLER.value,
            },
        ]
        origin.Nodes._handler.read.return_value = node_obj
        cmd = nodes.cmd_nodes(parser)
        subparser = nodes.cmd_nodes.register(parser)
        options = subparser.parse_args([])
        output = yaml.load(
            cmd.execute(origin, options, target=tabular.RenderTarget.yaml))
        self.assertEquals([
            {'name': 'hostname', 'title': 'Hostname'},
            {'name': 'node_type', 'title': 'Type'},
        ], output['columns'])
        nodes_output = sorted([
            {
                'hostname': node['hostname'],
                'node_type': node['node_type'],
            }
            for node in node_obj
        ], key=itemgetter('hostname'))
        self.assertEquals(nodes_output, output['data'])

    def test_calls_handler_with_hostnames(self):
        origin = make_origin()
        parser = ArgumentParser()
        origin.Nodes._handler.read.return_value = []
        subparser = nodes.cmd_nodes.register(parser)
        cmd = nodes.cmd_nodes(parser)
        hostnames = [
            make_name_without_spaces()
            for _ in range(3)
        ]
        options = subparser.parse_args(hostnames)
        cmd.execute(origin, options, target=tabular.RenderTarget.yaml)
        origin.Nodes._handler.read.assert_called_once_with(
            hostname=hostnames)
