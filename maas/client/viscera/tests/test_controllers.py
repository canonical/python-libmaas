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


class TestRegionController(TestCase):

    def test__string_representation_includes_only_system_id_and_hostname(self):
        rack_controller = controllers.RegionController({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        })
        self.assertThat(repr(rack_controller), Equals(
            "<RegionController hostname=%(hostname)r system_id=%(system_id)r>"
            % rack_controller._data))
