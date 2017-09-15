"""Tests for `maas.client.flesh.nodes`."""

from operator import itemgetter
import yaml

from .. import (
    ArgumentParser,
    nodes,
    tabular
)
from ...enum import NodeType
from ...testing import (
    make_name_without_spaces,
    TestCase
)
from ...viscera.testing import bind
from ...viscera.nodes import (
    Node,
    Nodes
)


def make_origin():
    """Make origin for nodes."""
    return bind(Nodes, Node)


class TestNodes(TestCase):
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
        output = yaml.load(
            cmd.execute(origin, {}, target=tabular.RenderTarget.yaml))
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
