"""Tests for `maas.client.viscera.zones`."""

import random

from testtools.matchers import (
    Equals,
    IsInstance,
    MatchesStructure,
)

from .. import zones

from ..testing import bind
from ...testing import (
    make_name,
    make_string_without_spaces,
    TestCase,
)


def make_origin():
    """
    Create a new origin with Zone and Zones. The former
    refers to the latter via the origin, hence why it must be bound.
    """
    return bind(zones.Zones, zones.Zone)


class TestZones(TestCase):

    def test__zones_create(self):
        origin = make_origin()
        zone_id = random.randint(0, 100)
        name = make_string_without_spaces()
        description = make_string_without_spaces()
        origin.Zones._handler.create.return_value = {
            "id": zone_id,
            "name": name,
            "description": description,
        }
        zone = origin.Zones.create(
            name=name,
            description=description,
        )
        origin.Zones._handler.create.assert_called_once_with(
            name=name,
            description=description,
        )
        self.assertThat(zone, IsInstance(origin.Zone))
        self.assertThat(zone, MatchesStructure.byEquality(
            id=zone_id, name=name, description=description
        ))

    def test__zones_create_without_description(self):
        origin = make_origin()
        zone_id = random.randint(0, 100)
        name = make_string_without_spaces()
        description = ""
        origin.Zones._handler.create.return_value = {
            "id": zone_id,
            "name": name,
            "description": description,
        }
        zone = origin.Zones.create(name=name)
        origin.Zones._handler.create.assert_called_once_with(name=name)
        self.assertThat(zone, IsInstance(origin.Zone))
        self.assertThat(zone, MatchesStructure.byEquality(
            id=zone_id, name=name, description=description
        ))

    def test__zones_read(self):
        """Zones.read() returns a list of Zones."""
        Zones = make_origin().Zones
        zones = [
            {
                "id": random.randint(0, 100),
                "name": make_string_without_spaces(),
                "description": make_string_without_spaces(),
            }
            for _ in range(3)
        ]
        Zones._handler.read.return_value = zones
        zones = Zones.read()
        self.assertThat(len(zones), Equals(3))


class TestZone(TestCase):

    def test__zone_unloaded(self):
        Zone = make_origin().Zone
        name = make_name("zone")
        zone = Zone(name)
        self.assertFalse(zone.loaded)
        self.assertEqual(name, zone.name)

    def test__zone_read(self):
        Zone = make_origin().Zone
        zone = {
            "id": random.randint(0, 100),
            "name": make_string_without_spaces(),
            "description": make_string_without_spaces(),
        }
        Zone._handler.read.return_value = zone
        self.assertThat(Zone.read(name=zone["name"]), Equals(Zone(zone)))
        Zone._handler.read.assert_called_once_with(name=zone["name"])

    def test__zone_delete(self):
        Zone = make_origin().Zone
        zone_name = make_string_without_spaces()
        zone = Zone({
            "id": random.randint(0, 100),
            "name": zone_name,
            "description": make_string_without_spaces(),
        })
        zone.delete()
        Zone._handler.delete.assert_called_once_with(name=zone_name)
