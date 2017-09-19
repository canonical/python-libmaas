"""Tests for `maas.client.flesh.machines`."""

from operator import itemgetter
import yaml

from .. import (
    ArgumentParser,
    machines,
    tabular
)
from ...enum import (
    NodeStatus,
    PowerState
)
from ...testing import (
    make_name_without_spaces,
    TestCase
)
from ...viscera.testing import bind
from ...viscera.machines import (
    Machine,
    Machines
)


def make_origin():
    """Make origin for machines."""
    return bind(Machines, Machine)


class TestMachines(TestCase):
    """Tests for `cmd_machines`."""

    def test_returns_table_with_machines(self):
        origin = make_origin()
        parser = ArgumentParser()
        machine_objs = [
            {
                'hostname': make_name_without_spaces(),
                'architecture': 'amd64/generic',
                'status': NodeStatus.READY.value,
                'status_name': NodeStatus.READY.name,
                'power_state': PowerState.OFF.value,
                'cpu_count': 2,
                'memory': 1024,
            },
            {
                'hostname': make_name_without_spaces(),
                'architecture': 'i386/generic',
                'status': NodeStatus.DEPLOYED.value,
                'status_name': NodeStatus.DEPLOYED.name,
                'power_state': PowerState.ON.value,
                'cpu_count': 4,
                'memory': 4096,
            },
        ]
        origin.Machines._handler.read.return_value = machine_objs
        cmd = machines.cmd_machines(parser)
        subparser = machines.cmd_machines.register(parser)
        options = subparser.parse_args([])
        output = yaml.load(
            cmd.execute(origin, options, target=tabular.RenderTarget.yaml))
        self.assertEquals([
            {'name': 'hostname', 'title': 'Hostname'},
            {'name': 'power', 'title': 'Power'},
            {'name': 'status', 'title': 'Status'},
            {'name': 'architecture', 'title': 'Arch'},
            {'name': 'cpus', 'title': '#CPUs'},
            {'name': 'memory', 'title': 'RAM'},
        ], output['columns'])
        machines_output = sorted([
            {
                'hostname': machine['hostname'],
                'power': machine['power_state'],
                'status': machine['status_name'],
                'architecture': machine['architecture'],
                'cpus': machine['cpu_count'],
                'memory': machine['memory'],
            }
            for machine in machine_objs
        ], key=itemgetter('hostname'))
        self.assertEquals(machines_output, output['data'])

    def test_calls_handler_with_hostnames(self):
        origin = make_origin()
        parser = ArgumentParser()
        origin.Machines._handler.read.return_value = []
        subparser = machines.cmd_machines.register(parser)
        cmd = machines.cmd_machines(parser)
        hostnames = [
            make_name_without_spaces()
            for _ in range(3)
        ]
        options = subparser.parse_args(hostnames)
        cmd.execute(origin, options, target=tabular.RenderTarget.yaml)
        origin.Machines._handler.read.assert_called_once_with(
            hostname=hostnames)
