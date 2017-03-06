"""Integration tests for `maas.client`."""

from collections import Mapping
from datetime import datetime
from http import HTTPStatus
import io
from itertools import repeat
import random
from time import sleep

from maas.client import (
    bones,
    viscera,
)
from maas.client.testing import (
    make_name_without_spaces,
    TestCase,
)
from maas.client.utils import (
    creds,
    profiles,
    retries,
)
from testtools.matchers import (
    AllMatch,
    Equals,
    Is,
    IsInstance,
    MatchesAll,
    MatchesAny,
    MatchesStructure,
)


kiB = 2 ** 10
MiB = 2 ** 20


def scenarios():
    with profiles.ProfileStore.open() as config:
        return tuple(
            (profile.name, dict(profile=profile))
            for profile in map(config.load, config)
        )


class IntegrationTestCase(TestCase):

    scenarios = scenarios()

    def setUp(self):
        super(IntegrationTestCase, self).setUp()
        self.session = bones.SessionAPI.fromProfile(self.profile)
        self.origin = viscera.Origin(self.session)


class TestAccount(IntegrationTestCase):

    def test__create_and_delete_credentials(self):
        credentials = self.origin.Account.create_credentials()
        self.assertThat(credentials, IsInstance(creds.Credentials))
        self.origin.Account.delete_credentials(credentials)


class TestBootResources(IntegrationTestCase):

    def test__list_boot_resources(self):
        boot_resources = self.origin.BootResources.read()
        self.assertThat(boot_resources, MatchesAll(
            IsInstance(self.origin.BootResources),
            AllMatch(IsInstance(self.origin.BootResource)),
        ))
        self.assertThat(
            boot_resources,
            AllMatch(MatchesStructure(
                id=IsInstance(int),
                type=IsInstance(str),
                name=IsInstance(str),
                architecture=IsInstance(str),
                subarches=Optional(IsInstance(str)),
                sets=Optional(IsInstance(Mapping)),
            )),
        )

    def test__create_and_delete_boot_resource(self):
        chunk = random.getrandbits(8 * 128).to_bytes(128, "big")
        content = b"".join(repeat(chunk, 5 * MiB // len(chunk)))
        boot_resource = self.origin.BootResources.create(
            make_name_without_spaces("ubuntu", "/"), "amd64/generic",
            io.BytesIO(content))
        self.assertThat(boot_resource, IsInstance(self.origin.BootResource))
        boot_resource.delete()
        error = self.assertRaises(
            bones.CallError, self.origin.BootResource.read, boot_resource.id)
        self.assertThat(error, MatchesStructure(
            status=Equals(HTTPStatus.NOT_FOUND)))


class TestBootSources(IntegrationTestCase):

    def test__create_and_delete_source_with_keyring_filename(self):
        source_url = make_name_without_spaces("http://maas.example.com/")
        keyring_filename = make_name_without_spaces("keyring-filename")
        boot_source = self.origin.BootSources.create(
            source_url, keyring_filename=keyring_filename)
        self.assertThat(boot_source, IsInstance(self.origin.BootSource))
        boot_source.delete()
        error = self.assertRaises(
            bones.CallError, self.origin.BootSource.read, boot_source.id)
        self.assertThat(error, MatchesStructure(
            status=Equals(HTTPStatus.NOT_FOUND)))

    def test__create_and_delete_source_with_keyring_data(self):
        source_url = make_name_without_spaces("http://maas.example.com/")
        keyring_data = make_name_without_spaces("keyring-data").encode()
        boot_source = self.origin.BootSources.create(
            source_url, keyring_data=io.BytesIO(keyring_data))
        self.assertThat(boot_source, IsInstance(self.origin.BootSource))
        boot_source.delete()
        error = self.assertRaises(
            bones.CallError, self.origin.BootSource.read, boot_source.id)
        self.assertThat(error, MatchesStructure(
            status=Equals(HTTPStatus.NOT_FOUND)))

    def test__list_boot_sources(self):
        boot_sources = self.origin.BootSources.read()
        self.assertThat(boot_sources, MatchesAll(
            IsInstance(self.origin.BootSources),
            AllMatch(IsInstance(self.origin.BootSource)),
        ))
        self.assertThat(
            boot_sources,
            AllMatch(MatchesStructure(
                id=IsInstance(int),
                url=IsInstance(str),
                keyring_filename=IsInstance(str),
                keyring_data=IsInstance(str),  # ??? Binary, no?
                created=IsInstance(datetime),
                updated=IsInstance(datetime),
            )),
        )


# TestBootSourceSelections
# TestDevices


class TestEvents(IntegrationTestCase):

    def test__query_events(self):
        events = self.origin.Events.query()
        self.assertThat(events, IsInstance(self.origin.Events))
        events = events.prev()
        self.assertThat(events, IsInstance(self.origin.Events))
        events = events.next()
        self.assertThat(events, IsInstance(self.origin.Events))

    def test__events(self):
        self.assertThat(
            self.origin.Events.query(),
            AllMatch(MatchesStructure(
                event_id=IsInstance(int),
                event_type=IsInstance(str),
                system_id=IsInstance(str),
                hostname=IsInstance(str),
                level=IsInstance(viscera.events.Level),
                created=IsInstance(datetime),
                description=IsInstance(str),
            )),
        )


# TestFiles
# TestMAAS


class TestMachines(IntegrationTestCase):

    def test__list_machines(self):
        machines = self.origin.Machines.read()
        self.assertThat(machines, MatchesAll(
            IsInstance(self.origin.Machines),
            AllMatch(IsInstance(self.origin.Machine)),
        ))
        self.assertThat(
            machines,
            AllMatch(MatchesStructure(
                # This is NOT exhaustive.
                system_id=IsInstance(str),
                architecture=IsInstance(str),
                hostname=IsInstance(str),
                ip_addresses=IsInstance(list),
                status=IsInstance(int),
                status_name=IsInstance(str),
                tags=IsInstance(list),
            )),
        )

    def XXXtest__allocate_deploy_and_release(self):
        machines_ready = [
            machine for machine in self.origin.Machines.read()
            if machine.status_name == "Ready"
        ]
        if len(machines_ready) == 0:
            self.skip("No machines available.")

        # Allocate one of the ready machines. XXX: This ought to be a method
        # on Machine or take a `system_id` argument.
        machine = random.choice(machines_ready)
        machine = self.origin.Machines.allocate(hostname=machine.hostname)
        self.assertThat(machine.status_name, Equals("Allocated"))

        try:
            # Deploy the machine with defaults.
            machine = machine.deploy()
            self.assertThat(machine.status_name, Equals("Deploying"))
            # Wait for the machine to deploy.
            for elapsed, remaining, wait in retries(600, 10):
                machine = self.origin.Machine.read(machine.system_id)
                if machine.status_name == "Deploying":
                    sleep(wait)
                else:
                    break
            else:
                self.fail("Timed-out waiting for machine to deploy.")
            # The machine has deployed.
            self.assertThat(machine.status_name, Equals("Deployed"))

        finally:
            # Release the machine.
            machine = machine.release("Finished with this now, thanks.")
            self.assertThat(machine.status_name, Equals("Releasing"))
            # Wait for the machine to release.
            for elapsed, remaining, wait in retries(300, 10):
                machine = self.origin.Machine.read(machine.system_id)
                if machine.status_name == "Releasing":
                    sleep(wait)
                else:
                    break
            else:
                self.fail("Timed-out waiting for machine to release.")
            # The machine has been released.
            self.assertThat(machine.status_name, Equals("Ready"))


class TestRackControllers(IntegrationTestCase):

    def test__list_rack_controllers(self):
        machines = self.origin.RackControllers.read()
        self.assertThat(machines, MatchesAll(
            IsInstance(self.origin.RackControllers),
            AllMatch(IsInstance(self.origin.RackController)),
        ))
        self.assertThat(
            machines,
            AllMatch(MatchesStructure(
                # This is NOT exhaustive.
                architecture=IsInstance(str),
                cpus=IsInstance(int),
                distro_series=IsInstance(str),
                fqdn=IsInstance(str),
                hostname=IsInstance(str),
                ip_addresses=IsInstance(list),
                memory=IsInstance(int),
                power_state=IsInstance(str),
                system_id=IsInstance(str),
                zone=IsInstance(self.origin.Zone),
            )),
        )


class TestRegionControllers(IntegrationTestCase):

    def test__list_region_controllers(self):
        machines = self.origin.RegionControllers.read()
        self.assertThat(machines, MatchesAll(
            IsInstance(self.origin.RegionControllers),
            AllMatch(IsInstance(self.origin.RegionController)),
        ))
        self.assertThat(
            machines,
            AllMatch(MatchesStructure(
                # This is NOT exhaustive.
                architecture=IsInstance(str),
                cpus=IsInstance(int),
                distro_series=IsInstance(str),
                fqdn=IsInstance(str),
                hostname=IsInstance(str),
                ip_addresses=IsInstance(list),
                memory=IsInstance(int),
                power_state=IsInstance(str),
                system_id=IsInstance(str),
                zone=IsInstance(self.origin.Zone),
            )),
        )


# TestTags
# TestTesting
# TestUsers
# TestVersion
# TestZones


# Additional matchers.

def Optional(matcher, default=Is(None)):
    return MatchesAny(matcher, default)


# End.
