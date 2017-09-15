"""Tests for `maas.client.flesh.controllers`."""

from operator import itemgetter
import yaml

from .. import (
    ArgumentParser,
    controllers,
    tabular
)
from ...enum import NodeType
from ...testing import (
    make_name_without_spaces,
    TestCase
)
from ...viscera.testing import bind
from ...viscera.controllers import (
    RackController,
    RackControllers,
    RegionController,
    RegionControllers
)


def make_origin():
    """Make origin for controllers."""
    return bind(
        RackControllers, RackController,
        RegionController, RegionControllers)


class TestControllers(TestCase):
    """Tests for `cmd_controllers`."""

    def test_returns_table_with_controllers(self):
        origin = make_origin()
        parser = ArgumentParser()
        region_rack_id = make_name_without_spaces()
        region_rack_hostname = make_name_without_spaces()
        racks = [
            {
                'system_id': region_rack_id,
                'hostname': region_rack_hostname,
                'node_type': NodeType.REGION_AND_RACK_CONTROLLER.value,
                'architecture': 'amd64/generic',
                'cpu_count': 2,
                'memory': 1024,
            },
            {
                'system_id': make_name_without_spaces(),
                'hostname': make_name_without_spaces(),
                'node_type': NodeType.RACK_CONTROLLER.value,
                'architecture': 'amd64/generic',
                'cpu_count': 2,
                'memory': 1024,
            },
        ]
        regions = [
            {
                'system_id': region_rack_id,
                'hostname': region_rack_hostname,
                'node_type': NodeType.REGION_AND_RACK_CONTROLLER.value,
                'architecture': 'amd64/generic',
                'cpu_count': 2,
                'memory': 1024,
            },
            {
                'system_id': make_name_without_spaces(),
                'hostname': make_name_without_spaces(),
                'node_type': NodeType.REGION_CONTROLLER.value,
                'architecture': 'amd64/generic',
                'cpu_count': 2,
                'memory': 1024,
            },
        ]
        origin.RackControllers._handler.read.return_value = racks
        origin.RegionControllers._handler.read.return_value = regions
        cmd = controllers.cmd_controllers(parser)
        output = yaml.load(
            cmd.execute(origin, {}, target=tabular.RenderTarget.yaml))
        self.assertEquals([
            {'name': 'hostname', 'title': 'Hostname'},
            {'name': 'node_type', 'title': 'Type'},
            {'name': 'architecture', 'title': 'Arch'},
            {'name': 'cpus', 'title': '#CPUs'},
            {'name': 'memory', 'title': 'RAM'},
        ], output['columns'])
        controller_output = {
            controller['hostname']: {
                'hostname': controller['hostname'],
                'node_type': controller['node_type'],
                'architecture': controller['architecture'],
                'cpus': controller['cpu_count'],
                'memory': controller['memory'],
            }
            for controller in racks + regions
        }
        self.assertEquals(
            sorted(controller_output.values(), key=itemgetter('hostname')),
            output['data'])
