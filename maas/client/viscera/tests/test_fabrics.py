"""Test for `maas.client.viscera.fabrics`."""

import random

from testtools.matchers import Equals

from .. import fabrics

from .. testing import bind
from ...testing import (
    make_name_without_spaces,
    TestCase,
)


def make_origin():
    """
    Create a new origin with Fabrics and Fabric. The former
    refers to the latter via the origin, hence why it must be bound.
    """
    return bind(fabrics.Fabrics, fabrics.Fabric)


class TestFabric(TestCase):

    def test__read(self):
        Fabric = make_origin().Fabric
        fabric = {
            "id": random.randint(0, 100),
            "name": make_name_without_spaces("name"),
            "class_type": make_name_without_spaces("class_type"),
        }
        Fabric._handler.read.return_value = fabric
        self.assertThat(Fabric.read(id=fabric["id"]), Equals(Fabric(fabric)))
