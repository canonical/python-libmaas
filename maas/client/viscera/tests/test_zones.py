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

    def test__zones_create(self):
        Zones = make_origin().Zones
        name = make_string_without_spaces()
        description = make_string_without_spaces()
        Zones._handler.create.return_value = {
            "id": 1,
            "name": name,
            "description": description,
        }
        Zones.create(
            name=name,
            description=description,
        )
        Zones._handler.create.assert_called_once_with(
            name=name,
            description=description,
        )

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
        assert False

    def test__zone_delete(self):
        assert False
