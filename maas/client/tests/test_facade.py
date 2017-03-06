"""Tests for `maas.client._client`."""

from unittest.mock import Mock

from testtools.matchers import (
    IsInstance,
    MatchesAll,
    MatchesStructure,
)

from .. import (
    facade,
    viscera,
)
from ..testing import TestCase


class TestClient(TestCase):
    """Tests for the simplified client.

    Right now these are fairly trivial tests, not testing in depth. Work is in
    progress to create a unit test framework that will allow testing against
    fake MAAS servers that match the "shape" of real MAAS servers. At the
    point that lands these tests should be revised.
    """

    def setUp(self):
        super(TestClient, self).setUp()
        self.session = Mock(name="session", handlers={})
        self.origin = viscera.Origin(self.session)
        self.client = facade.Client(self.origin)

    def test__client_maps_account(self):
        self.assertThat(self.client, MatchesClient(
            account=MatchesFacade(
                create_credentials=self.origin.Account.create_credentials,
                delete_credentials=self.origin.Account.delete_credentials,
            ),
        ))

    def test__client_maps_boot_resources(self):
        self.assertThat(self.client, MatchesClient(
            boot_resources=MatchesFacade(
                create=self.origin.BootResources.create,
                get=self.origin.BootResource.read,
                list=self.origin.BootResources.read,
                start_import=self.origin.BootResources.start_import,
                stop_import=self.origin.BootResources.stop_import,
            ),
        ))

    def test__client_maps_boot_sources(self):
        self.assertThat(self.client, MatchesClient(
            boot_sources=MatchesFacade(
                create=self.origin.BootSources.create,
                get=self.origin.BootSource.read,
                list=self.origin.BootSources.read,
            ),
        ))

    def test__client_maps_devices(self):
        self.assertThat(self.client, MatchesClient(
            devices=MatchesFacade(
                get=self.origin.Device.read,
                list=self.origin.Devices.read,
            ),
        ))

    def test__client_maps_events(self):
        self.assertThat(self.client, MatchesClient(
            events=MatchesFacade(
                query=self.origin.Events.query,
                DEBUG=self.origin.Events.Level.DEBUG,
                INFO=self.origin.Events.Level.INFO,
                WARNING=self.origin.Events.Level.WARNING,
                ERROR=self.origin.Events.Level.ERROR,
                CRITICAL=self.origin.Events.Level.CRITICAL,
            ),
        ))

    def test__client_maps_files(self):
        self.assertThat(self.client, MatchesClient(
            files=MatchesFacade(
                list=self.origin.Files.read,
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

    def test__client_maps_rack_controllers(self):
        self.assertThat(self.client, MatchesClient(
            rack_controllers=MatchesFacade(
                get=self.origin.RackController.read,
                list=self.origin.RackControllers.read,
            ),
        ))

    def test__client_maps_region_controllers(self):
        self.assertThat(self.client, MatchesClient(
            region_controllers=MatchesFacade(
                get=self.origin.RegionController.read,
                list=self.origin.RegionControllers.read,
            ),
        ))

    def test__client_maps_tags(self):
        self.assertThat(self.client, MatchesClient(
            tags=MatchesFacade(
                create=self.origin.Tags.create,
                list=self.origin.Tags.read,
            ),
        ))

    def test__client_maps_users(self):
        self.assertThat(self.client, MatchesClient(
            users=MatchesFacade(
                create=self.origin.Users.create,
                list=self.origin.Users.read,
                whoami=self.origin.Users.whoami,
            ),
        ))

    def test__client_maps_version(self):
        self.assertThat(self.client, MatchesClient(
            version=MatchesFacade(
                get=self.origin.Version.read,
            ),
        ))

    def test__client_maps_zones(self):
        self.assertThat(self.client, MatchesClient(
            zones=MatchesFacade(
                get=self.origin.Zone.read,
                list=self.origin.Zones.read,
            ),
        ))


def MatchesClient(**facades):
    """Matches a `facade.Client` with the given facades."""
    return MatchesAll(
        IsInstance(facade.Client),
        MatchesStructure(**facades),
        first_only=True,
    )


def MatchesFacade(**methods):
    """Matches a `facade.Facade` with the given methods."""
    return MatchesAll(
        IsInstance(facade.Facade),
        MatchesStructure.byEquality(**methods),
        first_only=True,
    )
