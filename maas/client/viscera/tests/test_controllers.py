"""Test for `maas.client.viscera.controllers`."""

from testtools.matchers import Equals

from .. import controllers
from ...testing import (
    make_name_without_spaces,
    TestCase,
)
from ..testing import bind


def make_origin():
    # Create a new origin with RackController, RegionControllers,
    # RackController, and RegionController.
    return bind(
        controllers.RackControllers, controllers.RackController,
        controllers.RegionControllers, controllers.RegionController,
    )


class TestRackController(TestCase):

    def test__string_representation_includes_only_system_id_and_hostname(self):
        rack_controller = controllers.RackController({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        })
        self.assertThat(repr(rack_controller), Equals(
            "<RackController hostname=%(hostname)r system_id=%(system_id)r>"
            % rack_controller._data))

    def test__get_power_parameters(self):
        rack_controller = make_origin().RackController({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        })
        power_parameters = {
            "key": make_name_without_spaces("value"),
        }
        rack_controller._handler.power_parameters.return_value = (
            power_parameters)
        self.assertThat(
            rack_controller.get_power_parameters(),
            Equals(power_parameters),
        )
        rack_controller._handler.power_parameters.assert_called_once_with(
            system_id=rack_controller.system_id
        )

    def test__set_power(self):
        orig_power_type = make_name_without_spaces("power_type")
        new_power_type = make_name_without_spaces("power_type")
        rack_controller = make_origin().RackController({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "power_type": orig_power_type,
        })
        power_parameters = {
            "key": make_name_without_spaces("value"),
        }
        rack_controller._handler.update.return_value = {
            "power_type": new_power_type}
        rack_controller.set_power(new_power_type, power_parameters)
        rack_controller._handler.update.assert_called_once_with(
            system_id=rack_controller.system_id,
            power_type=new_power_type,
            power_parameters=power_parameters,
        )
        self.assertThat(
            rack_controller.power_type, Equals(new_power_type))


class TestRegionController(TestCase):

    def test__string_representation_includes_only_system_id_and_hostname(self):
        rack_controller = controllers.RegionController({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        })
        self.assertThat(repr(rack_controller), Equals(
            "<RegionController hostname=%(hostname)r system_id=%(system_id)r>"
            % rack_controller._data))

    def test__get_power_parameters(self):
        region_controller = make_origin().RegionController({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        })
        power_parameters = {
            "key": make_name_without_spaces("value"),
        }
        region_controller._handler.power_parameters.return_value = (
            power_parameters)
        self.assertThat(
            region_controller.get_power_parameters(),
            Equals(power_parameters),
        )
        region_controller._handler.power_parameters.assert_called_once_with(
            system_id=region_controller.system_id
        )

    def test__set_power(self):
        orig_power_type = make_name_without_spaces("power_type")
        new_power_type = make_name_without_spaces("power_type")
        region_controller = make_origin().RegionController({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "power_type": orig_power_type,
        })
        power_parameters = {
            "key": make_name_without_spaces("value"),
        }
        region_controller._handler.update.return_value = {
            "power_type": new_power_type}
        region_controller.set_power(new_power_type, power_parameters)
        region_controller._handler.update.assert_called_once_with(
            system_id=region_controller.system_id,
            power_type=new_power_type,
            power_parameters=power_parameters,
        )
        self.assertThat(
            region_controller.power_type, Equals(new_power_type))
