"""Test for `alburnum.maas.viscera.machines`."""

__all__ = []


from alburnum.maas.testing import (
    make_name_without_spaces,
    TestCase,
)
from alburnum.maas.viscera.testing import bind

from testtools.matchers import Equals

from .. import machines


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
        Machine = bind(machines.Machine)
        Machine._handler.deploy.return_value = {}
        machine = Machine({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        })
        machine.deploy()
        machine._handler.deploy.assert_called_once_with(
            system_id=machine.system_id
        )


class TestMachines(TestCase):
    pass
