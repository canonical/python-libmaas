"""Test for `maas.client.viscera.machines`."""

from testtools.matchers import Equals

from .. import machines
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

    def test__deploy(self):
        Machine = make_origin().Machine
        Machine._handler.deploy.return_value = {}
        machine = Machine({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        })
        machine.deploy(
            distro_series='ubuntu/xenial',
            hwe_kernel='hwe-x',
        )
        machine._handler.deploy.assert_called_once_with(
            system_id=machine.system_id,
            distro_series='ubuntu/xenial',
            hwe_kernel='hwe-x',
        )


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
