"""Tests for `maas.client.viscera.zones`."""

import random

from testtools.matchers import Equals

from .. import zones

from ..testing import bind
from ...testing import (
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

    def _assert_create_zone(self, **kwargs):
        Zones = make_origin().Zones
        zone = {"id": random.randint(0, 100)}
        zone.update(kwargs)
        Zones._handler.create.return_value = zone
        Zones.create(**kwargs)
        Zones._handler.create.assert_called_once_with(**kwargs)

    def test__zones_create(self):
        self._assert_create_zone(
            name=make_string_without_spaces(),
            description=make_string_without_spaces(),
        )

    def test__zones_create_no_description(self):
        self._assert_create_zone(name=make_string_without_spaces())

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
