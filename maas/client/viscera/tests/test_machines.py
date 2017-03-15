"""Test for `maas.client.viscera.machines`."""

from maas.client.bones.testing.server import ApplicationBuilder
from maas.client.utils.testing import make_Credentials
from maas.client.viscera import Origin
from testtools.matchers import (
    ContainsDict,
    Equals,
    MatchesStructure,
)

from .. import machines
from ...bones.testing import api_descriptions
from ...testing import (
    make_name_without_spaces,
    TestCase,
)
from ..testing import bind


def make_origin():
    # Create a new origin with Machines and Machine. The former refers to the
    # latter via the origin, hence why it must be bound.
    return bind(machines.Machines, machines.Machine)


class TestMachine(TestCase):

    def test__string_representation_includes_only_system_id_and_hostname(self):
        machine = machines.Machine({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        })
        self.assertThat(repr(machine), Equals(
            "<Machine hostname=%(hostname)r system_id=%(system_id)r>"
            % machine._data))


class TestMachine_APIVersion(TestCase):

    scenarios = tuple(
        (name, dict(version=version, description=description))
        for name, version, description in api_descriptions)

    async def test__deploy(self):
        builder = ApplicationBuilder(self.description)

        @builder.handle("auth:Machine.deploy")
        async def deploy(request, system_id):
            self.assertThat(request.params, ContainsDict({
                "distro_series": Equals("ubuntu/xenial"),
                "hwe_kernel": Equals("hwe-x"),
            }))
            return {
                "system_id": system_id,
                "status_name": "Deploying",
            }

        async with builder.serve() as baseurl:
            origin = await Origin.fromURL(
                baseurl, credentials=make_Credentials())
            machine = origin.Machine({
                "system_id": make_name_without_spaces("system-id"),
            })
            machine = await machine.deploy(
                distro_series='ubuntu/xenial',
                hwe_kernel='hwe-x',
            )
            self.assertThat(
                machine, MatchesStructure.byEquality(
                    status_name="Deploying"))


class TestMachines(TestCase):

    def test__allocate(self):
        Machines = make_origin().Machines
        Machines._handler.allocate.return_value = {}
        hostname = make_name_without_spaces("hostname")
        Machines.allocate(
            hostname=hostname,
            architecture='amd64/generic',
            cpus=4,
            memory=1024.0,
            tags=['foo', 'bar', '-baz'],
        )
        Machines._handler.allocate.assert_called_once_with(
            name=hostname,  # API parameter is actually name, not hostname
            architecture='amd64/generic',
            cpu_count='4',
            mem='1024.0',
            tags=['foo', 'bar'],
            not_tags=['baz'],
        )

    def test__power_parameters(self):
        Machines = make_origin().Machines
        Machines._handler.power_parameters.return_value = {}
        Machines.power_parameters()
        Machines._handler.power_parameters.assert_called_once_with(id=[])
