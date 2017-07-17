"""Test for `maas.client.viscera.fabrics`."""

import random

from testtools.matchers import (
    Equals,
    IsInstance,
    MatchesAll,
    MatchesSetwise,
    MatchesStructure,
)

from ...errors import CannotDelete
from ..fabrics import (
    Fabric,
    Fabrics,
)
from ..vlans import (
    Vlan,
    Vlans,
)

from .. testing import bind
from ...testing import (
    make_string_without_spaces,
    TestCase,
)


def make_origin():
    """
    Create a new origin with Fabrics, Fabric, Vlans, and Vlan.
    """
    return bind(Fabrics, Fabric, Vlans, Vlan)


class TestFabrics(TestCase):

    def test__fabrics_create(self):
        Fabrics = make_origin().Fabrics
        name = make_string_without_spaces()
        description = make_string_without_spaces()
        class_type = make_string_without_spaces()
        Fabrics._handler.create.return_value = {
            "id": 1,
            "name": name,
            "description": description,
            "class_type": class_type,
        }
        Fabrics.create(
            name=name,
            description=description,
            class_type=class_type,
        )
        Fabrics._handler.create.assert_called_once_with(
            name=name,
            description=description,
            class_type=class_type,
        )

    def test__fabrics_read(self):
        """Fabrics.read() returns a list of Fabrics."""
        Fabrics = make_origin().Fabrics
        fabrics = [
            {
                "id": random.randint(0, 100),
                "name": make_string_without_spaces(),
                "class_type": make_string_without_spaces(),
            }
            for _ in range(3)
        ]
        Fabrics._handler.read.return_value = fabrics
        fabrics = Fabrics.read()
        self.assertThat(len(fabrics), Equals(3))


class TestFabric(TestCase):

    def test__fabric_get_default(self):
        Fabric = make_origin().Fabric
        Fabric._handler.read.return_value = {
            "id": 0,
            "name": make_string_without_spaces(),
            "class_type": make_string_without_spaces(),
        }
        Fabric.get_default()
        Fabric._handler.read.assert_called_once_with(
            id=0
        )

    def test__fabric_read(self):
        Fabric = make_origin().Fabric
        fabric = {
            "id": random.randint(0, 100),
            "name": make_string_without_spaces(),
            "class_type": make_string_without_spaces(),
            "vlans": [{
                "id": 1,
            }, {
                "id": 2,
            }]
        }
        Fabric._handler.read.return_value = fabric
        self.assertThat(Fabric.read(id=fabric["id"]), Equals(Fabric(fabric)))
        Fabric._handler.read.assert_called_once_with(id=fabric["id"])
        self.assertThat(Fabric(fabric).vlans, MatchesSetwise(
            MatchesAll(IsInstance(Vlan), MatchesStructure.byEquality(id=1)),
            MatchesAll(IsInstance(Vlan), MatchesStructure.byEquality(id=2)),
        ))

    def test__fabric_delete(self):
        Fabric = make_origin().Fabric
        fabric_id = random.randint(1, 100)
        fabric = Fabric({
            "id": fabric_id,
            "name": make_string_without_spaces(),
            "class_type": make_string_without_spaces()
        })
        fabric.delete()
        Fabric._handler.delete.assert_called_once_with(id=fabric_id)

    def test__fabric_delete_default(self):
        Fabric = make_origin().Fabric
        fabric = Fabric({
            "id": 0,
            "name": make_string_without_spaces(),
            "class_type": make_string_without_spaces(),
        })
        self.assertRaises(CannotDelete, fabric.delete)
