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

    def test__get_power_parameters(self):
        device = make_origin().Device({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        })
        power_parameters = {
            "key": make_name_without_spaces("value"),
        }
        device._handler.power_parameters.return_value = power_parameters
        self.assertThat(
            device.get_power_parameters(),
            Equals(power_parameters),
        )
        device._handler.power_parameters.assert_called_once_with(
            system_id=device.system_id
        )

    def test__set_power(self):
        orig_power_type = make_name_without_spaces("power_type")
        new_power_type = make_name_without_spaces("power_type")
        device = make_origin().Device({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "power_type": orig_power_type,
        })
        power_parameters = {
            "key": make_name_without_spaces("value"),
        }
        device._handler.update.return_value = {"power_type": new_power_type}
        device.set_power(new_power_type, power_parameters)
        device._handler.update.assert_called_once_with(
            system_id=device.system_id,
            power_type=new_power_type,
            power_parameters=power_parameters,
        )
        self.assertThat(
            device.power_type, Equals(new_power_type))


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
