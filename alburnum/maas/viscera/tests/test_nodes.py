"""Test for `alburnum.maas.viscera.nodes`."""

__all__ = []

from alburnum.maas.testing import (
    make_name_without_spaces,
    TestCase,
)
from testtools.matchers import Equals

from .. import nodes


class TestNode(TestCase):

    def test__string_representation_includes_only_system_id_and_hostname(self):
        node = nodes.Node({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        })
        self.assertThat(repr(node), Equals(
            "<Node hostname=%(hostname)r system_id=%(system_id)r>"
            % node._data))
