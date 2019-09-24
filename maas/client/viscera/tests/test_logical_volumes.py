"""Test for `maas.client.viscera.logical_volumes`."""

import random
from testtools.matchers import Equals, IsInstance

from .. import block_devices, logical_volumes, nodes, volume_groups
from ...testing import make_name_without_spaces, TestCase
from ..testing import bind


def make_origin():
    # Create a new origin with Devices and Device. The former refers to the
    # latter via the origin, hence why it must be bound.
    return bind(
        logical_volumes.LogicalVolume,
        logical_volumes.LogicalVolumes,
        block_devices.BlockDevice,
        block_devices.BlockDevices,
        nodes.Node,
        volume_groups.VolumeGroup,
    )


class TestLogicalVolume(TestCase):
    def test__string_representation_includes_only_name(self):
        volume = logical_volumes.LogicalVolume(
            {"name": make_name_without_spaces("name")}
        )
        self.assertThat(
            repr(volume), Equals("<LogicalVolume name=%(name)r>" % volume._data)
        )


class TestLogicalVolumes(TestCase):
    def test__create(self):
        origin = make_origin()

        system_id = make_name_without_spaces("system-id")
        lv_id = random.randint(1, 20)
        lv_name = make_name_without_spaces("lvname")

        VolumeGroup = origin.VolumeGroup
        vg = VolumeGroup({"system_id": system_id, "id": random.randint(21, 30)})
        VolumeGroup._handler.create_logical_volume.return_value = {
            "system_id": system_id,
            "id": lv_id,
        }

        uuid = make_name_without_spaces("uuid")
        tags = [make_name_without_spaces("tag")]

        BlockDevice = origin.BlockDevice
        BlockDevice._handler.read.return_value = {
            "system_id": system_id,
            "id": lv_id,
            "name": lv_name,
            "tags": [],
            "uuid": uuid,
        }

        LogicalVolumes = origin.LogicalVolumes
        observed = LogicalVolumes.create(vg, lv_name, 10 * 1024, uuid=uuid, tags=tags)
        self.assertThat(observed, IsInstance(logical_volumes.LogicalVolume))
        self.assertThat(observed.name, Equals(lv_name))

        VolumeGroup._handler.create_logical_volume.assert_called_once_with(
            system_id=system_id, id=vg.id, name=lv_name, size=10 * 1024, uuid=uuid
        )
        BlockDevice._handler.read.assert_called_once_with(system_id=system_id, id=lv_id)
        BlockDevice._handler.add_tag.assert_called_once_with(
            system_id=system_id, id=lv_id, tag=tags[0]
        )
