"""Tests for `maas.client.flesh.devices`."""

from operator import itemgetter
import yaml

from .. import (
    ArgumentParser,
    devices,
    tabular
)
from ...testing import (
    make_name_without_spaces,
    TestCase
)
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


def make_origin():
    """Make origin for devices."""
    return bind(
        Devices, Device,
        Interfaces, Interface,
        InterfaceLinks, InterfaceLink)


class TestDevices(TestCase):
    """Tests for `cmd_devices`."""

    def test_returns_table_with_devices(self):
        origin = make_origin()
        parser = ArgumentParser()
        devices_objs = [
            {
                'hostname': make_name_without_spaces(),
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
        output = yaml.load(
            cmd.execute(origin, {}, target=tabular.RenderTarget.yaml))
        self.assertEquals([
            {'name': 'hostname', 'title': 'Hostname'},
            {'name': 'ip_addresses', 'title': 'IP addresses'},
        ], output['columns'])
        devices_output = sorted([
            {
                'hostname': device['hostname'],
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
