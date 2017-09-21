"""Tests for `maas.client.flesh.devices`."""

from operator import itemgetter
import yaml

from .testing import TestCaseWithProfile
from .. import (
    ArgumentParser,
    devices,
    tabular
)
from ...testing import make_name_without_spaces
from ...viscera.testing import bind
from ...viscera.devices import (
    Device,
    Devices
)
from ...viscera.interfaces import (
    Interface,
    Interfaces,
    InterfaceLink,
    InterfaceLinks,
)
from ...viscera.users import User


def make_origin():
    """Make origin for devices."""
    return bind(
        Devices, Device, User,
        Interfaces, Interface,
        InterfaceLinks, InterfaceLink)


class TestDevices(TestCaseWithProfile):
    """Tests for `cmd_devices`."""

    def test_returns_table_with_devices(self):
        origin = make_origin()
        parser = ArgumentParser()
        devices_objs = [
            {
                'hostname': make_name_without_spaces(),
                'owner': make_name_without_spaces(),
                'interface_set': [
                    {
                        'links': [
                            {'ip_address': '192.168.122.1'}
                        ],
                    },
                    {
                        'links': [
                            {'ip_address': '192.168.122.2'}
                        ],
                    },
                    {
                        'links': [
                            {}
                        ],
                    },
                ],
            },
            {
                'hostname': make_name_without_spaces(),
                'owner': make_name_without_spaces(),
                'interface_set': [
                    {
                        'links': [
                            {'ip_address': '192.168.122.10'}
                        ],
                    },
                    {
                        'links': [
                            {'ip_address': '192.168.122.11'}
                        ],
                    },
                    {
                        'links': [
                            {}
                        ],
                    },
                ],
            },
        ]
        origin.Devices._handler.read.return_value = devices_objs
        cmd = devices.cmd_devices(parser)
        subparser = devices.cmd_devices.register(parser)
        options = subparser.parse_args([])
        output = yaml.load(
            cmd.execute(origin, options, target=tabular.RenderTarget.yaml))
        self.assertEquals([
            {'name': 'hostname', 'title': 'Hostname'},
            {'name': 'owner', 'title': 'Owner'},
            {'name': 'ip_addresses', 'title': 'IP addresses'},
        ], output['columns'])
        devices_output = sorted([
            {
                'hostname': device['hostname'],
                'owner': device['owner'] if device['owner'] else '(none)',
                'ip_addresses': [
                    link['ip_address']
                    for nic in device['interface_set']
                    for link in nic['links']
                    if link.get('ip_address')
                ]
            }
            for device in devices_objs
        ], key=itemgetter('hostname'))
        self.assertEquals(devices_output, output['data'])

    def test_calls_handler_with_hostnames(self):
        origin = make_origin()
        parser = ArgumentParser()
        origin.Devices._handler.read.return_value = []
        subparser = devices.cmd_devices.register(parser)
        cmd = devices.cmd_devices(parser)
        hostnames = [
            make_name_without_spaces()
            for _ in range(3)
        ]
        options = subparser.parse_args(hostnames)
        cmd.execute(origin, options, target=tabular.RenderTarget.yaml)
        origin.Devices._handler.read.assert_called_once_with(
            hostname=hostnames)
