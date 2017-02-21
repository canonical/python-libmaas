"""Tests for `maas.client._client`."""

__all__ = []

from unittest.mock import Mock

from testtools.matchers import (
    IsInstance,
    MatchesAll,
    MatchesStructure,
)

from .. import (
    _client,
    viscera,
)
from ..testing import TestCase


class TestClient(TestCase):
    """Tests for the simplified client."""

    def setUp(self):
        super(TestClient, self).setUp()
        self.session = Mock(name="session", handlers={})
        self.origin = viscera.Origin(self.session)
        self.client = _client.Client(self.origin)

    def test__client_maps_devices(self):
        self.assertThat(self.client, MatchesClient(
            devices=MatchesFacade(
                get=self.origin.Device.read,
                list=self.origin.Devices.read,
            ),
        ))

    def test__client_maps_machines(self):
        self.assertThat(self.client, MatchesClient(
            machines=MatchesFacade(
                allocate=self.origin.Machines.allocate,
                get=self.origin.Machine.read,
                list=self.origin.Machines.read,
            ),
        ))


def MatchesClient(**facades):
    """Matches a `_client.Client` with the given facades."""
    return MatchesAll(
        IsInstance(_client.Client),
        MatchesStructure(**facades),
        first_only=True,
    )


def MatchesFacade(**methods):
    """Matches a `_client.Facade` with the given methods."""
    return MatchesAll(
        IsInstance(_client.Facade),
        MatchesStructure.byEquality(**methods),
        first_only=True,
    )
