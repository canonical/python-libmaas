"""Test for `maas.client.viscera.nodes`."""

from testtools.matchers import Equals

from .. import nodes
from ...testing import (
    make_name_without_spaces,
    TestCase,
)
from ..testing import bind


def make_origin():
    # Create a new origin with Nodes and Node. The former refers to the
    # latter via the origin, hence why it must be bound.
    return bind(nodes.Nodes, nodes.Node)


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
