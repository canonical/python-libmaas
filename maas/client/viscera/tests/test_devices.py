"""Test for `maas.client.viscera.devices`."""

from testtools.matchers import Equals

from .. import devices
from ...testing import (
    make_name_without_spaces,
    TestCase,
)
from ..testing import bind


def make_origin():
    # Create a new origin with Devices and Device. The former refers to the
    # latter via the origin, hence why it must be bound.
    return bind(devices.Devices, devices.Device)


class TestDevice(TestCase):

    def test__string_representation_includes_only_system_id_and_hostname(self):
        device = devices.Device({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        })
        self.assertThat(repr(device), Equals(
            "<Device hostname=%(hostname)r system_id=%(system_id)r>"
            % device._data))

    def test__read(self):
        data = {
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        }

        origin = make_origin()
        origin.Device._handler.read.return_value = data

        device_observed = origin.Device.read(data["system_id"])
        device_expected = origin.Device(data)
        self.assertThat(device_observed, Equals(device_expected))


class TestDevices(TestCase):

    def test__read(self):
        data = {
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        }

        origin = make_origin()
        origin.Devices._handler.read.return_value = [data]

        devices_observed = origin.Devices.read()
        devices_expected = origin.Devices([origin.Device(data)])
        self.assertThat(devices_observed, Equals(devices_expected))
