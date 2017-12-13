"""Test for `maas.client.viscera.block_devices`."""

import random

from testtools.matchers import Equals

from ..block_devices import (
    BlockDevice,
    BlockDevices,
)
from ..nodes import (
    Node,
    Nodes,
)
from ..partitions import (
    Partition,
    Partitions,
)

from .. testing import bind
from ...enum import BlockDeviceType
from ...testing import (
    make_string_without_spaces,
    TestCase,
)


def make_origin():
    """
    Create a new origin with required objects.
    """
    return bind(
        BlockDevices, BlockDevice, Partitions, Partition,
        Nodes, Node)


class TestBlockDevices(TestCase):

    def test__by_name(self):
        origin = make_origin()
        BlockDevices, BlockDevice = origin.BlockDevices, origin.BlockDevice
        system_id = make_string_without_spaces()
        block_names = [
            make_string_without_spaces()
            for _ in range(3)
        ]
        blocks_by_name = {
            name: BlockDevice({
                "system_id": system_id,
                "id": random.randint(0, 100),
                "name": name,
                "type": BlockDeviceType.PHYSICAL.value,
            })
            for name in block_names
        }
        blocks = BlockDevices([
            obj
            for _, obj in blocks_by_name.items()
        ])
        self.assertEqual(blocks_by_name, blocks.by_name)

    def test__get_by_name(self):
        origin = make_origin()
        BlockDevices, BlockDevice = origin.BlockDevices, origin.BlockDevice
        system_id = make_string_without_spaces()
        block_names = [
            make_string_without_spaces()
            for _ in range(3)
        ]
        blocks_by_name = {
            name: BlockDevice({
                "system_id": system_id,
                "id": random.randint(0, 100),
                "name": name,
                "type": BlockDeviceType.PHYSICAL.value,
            })
            for name in block_names
        }
        bcaches = BlockDevices([
            obj
            for _, obj in blocks_by_name.items()
        ])
        name = block_names[0]
        self.assertEqual(blocks_by_name[name], bcaches.get_by_name(name))

    def test__read_bad_node_type(self):
        BlockDevices = make_origin().BlockDevices
        error = self.assertRaises(
            TypeError, BlockDevices.read, random.randint(0, 100))
        self.assertEquals("node must be a Node or str, not int", str(error))

    def test__read_with_system_id(self):
        BlockDevices = make_origin().BlockDevices
        system_id = make_string_without_spaces()
        blocks = [
            {
                "system_id": system_id,
                "id": random.randint(0, 100),
                "name": make_string_without_spaces(),
                "type": BlockDeviceType.PHYSICAL.value,
            }
            for _ in range(3)
        ]
        BlockDevices._handler.read.return_value = blocks
        blocks = BlockDevices.read(system_id)
        self.assertThat(len(blocks), Equals(3))
        BlockDevices._handler.read.assert_called_once_with(
            system_id=system_id)

    def test__read_with_Node(self):
        origin = make_origin()
        BlockDevices, Node = origin.BlockDevices, origin.Node
        system_id = make_string_without_spaces()
        node = Node(system_id)
        blocks = [
            {
                "system_id": system_id,
                "id": random.randint(0, 100),
                "name": make_string_without_spaces(),
                "type": BlockDeviceType.PHYSICAL.value,
            }
            for _ in range(3)
        ]
        BlockDevices._handler.read.return_value = blocks
        blocks = BlockDevices.read(node)
        self.assertThat(len(blocks), Equals(3))
        BlockDevices._handler.read.assert_called_once_with(
            system_id=system_id)

    def test__create_bad_node_type(self):
        origin = make_origin()
        BlockDevices = origin.BlockDevices
        error = self.assertRaises(
            TypeError, BlockDevices.create,
            random.randint(0, 100), 'sda',
            model='QEMU', serial='QEMU0001',
            size=(4096 * 1024), block_size=512)
        self.assertEquals("node must be a Node or str, not int", str(error))

    def test__create_missing_size(self):
        BlockDevices = make_origin().BlockDevices
        error = self.assertRaises(
            ValueError, BlockDevices.create,
            make_string_without_spaces(), 'sda',
            model='QEMU', serial='QEMU0001',
            block_size=512)
        self.assertEquals(
            "size must be provided and greater than zero.",
            str(error))

    def test__create_negative_size(self):
        BlockDevices = make_origin().BlockDevices
        error = self.assertRaises(
            ValueError, BlockDevices.create,
            make_string_without_spaces(), 'sda',
            model='QEMU', serial='QEMU0001',
            size=-1, block_size=512)
        self.assertEquals(
            "size must be provided and greater than zero.",
            str(error))

    def test__create_missing_block_size(self):
        BlockDevices = make_origin().BlockDevices
        error = self.assertRaises(
            ValueError, BlockDevices.create,
            make_string_without_spaces(), 'sda',
            model='QEMU', serial='QEMU0001',
            size=(4096 * 1024), block_size=None)
        self.assertEquals(
            "block_size must be provided and greater than zero.",
            str(error))

    def test__create_negative_block_size(self):
        BlockDevices = make_origin().BlockDevices
        error = self.assertRaises(
            ValueError, BlockDevices.create,
            make_string_without_spaces(), 'sda',
            model='QEMU', serial='QEMU0001',
            size=(4096 * 1024), block_size=-1)
        self.assertEquals(
            "block_size must be provided and greater than zero.",
            str(error))

    def test__create_model_requires_serial(self):
        BlockDevices = make_origin().BlockDevices
        error = self.assertRaises(
            ValueError, BlockDevices.create,
            make_string_without_spaces(), 'sda',
            model='QEMU',
            size=(4096 * 1024))
        self.assertEquals(
            "serial must be provided when model is provided.",
            str(error))

    def test__create_serial_requires_model(self):
        BlockDevices = make_origin().BlockDevices
        error = self.assertRaises(
            ValueError, BlockDevices.create,
            make_string_without_spaces(), 'sda',
            serial='QEMU0001',
            size=(4096 * 1024))
        self.assertEquals(
            "model must be provided when serial is provided.",
            str(error))

    def test__create_requires_model_and_serial_or_id_path(self):
        BlockDevices = make_origin().BlockDevices
        error = self.assertRaises(
            ValueError, BlockDevices.create,
            make_string_without_spaces(), 'sda',
            size=(4096 * 1024))
        self.assertEquals(
            "Either model/serial is provided or id_path must be provided.",
            str(error))

    def test__create(self):
        origin = make_origin()
        BlockDevices = origin.BlockDevices
        system_id = make_string_without_spaces()
        size = (4096 * 1024)
        BlockDevices._handler.create.return_value = {
            'system_id': system_id,
            'id': random.randint(0, 100),
            'name': 'sda',
            'model': 'QEMU',
            'serial': 'QEMU0001',
            'size': size,
            'block_size': 512,
        }
        BlockDevices.create(
            system_id, 'sda',
            model='QEMU', serial='QEMU0001',
            size=size)
        BlockDevices._handler.create.assert_called_once_with(
            system_id=system_id, name='sda', model='QEMU', serial='QEMU0001',
            size=size, block_size=512)

    def test__create_with_tags(self):
        origin = make_origin()
        BlockDevices, BlockDevice = origin.BlockDevices, origin.BlockDevice
        system_id = make_string_without_spaces()
        block_id = random.randint(0, 100)
        size = (4096 * 1024)
        BlockDevices._handler.create.return_value = {
            'system_id': system_id,
            'id': block_id,
            'name': 'sda',
            'model': 'QEMU',
            'serial': 'QEMU0001',
            'size': size,
            'block_size': 512,
            'tags': [],
        }
        BlockDevices._handler.add_tag.return_value = None
        tag = make_string_without_spaces()
        BlockDevices.create(
            system_id, 'sda',
            model='QEMU', serial='QEMU0001',
            size=size, tags=[tag])
        BlockDevices._handler.create.assert_called_once_with(
            system_id=system_id, name='sda', model='QEMU', serial='QEMU0001',
            size=size, block_size=512)
        BlockDevice._handler.add_tag.assert_called_once_with(
            system_id=system_id, id=block_id, tag=tag)


class TestBlockDevice(TestCase):

    def test__read_bad_node_type(self):
        BlockDevice = make_origin().BlockDevice
        error = self.assertRaises(
            TypeError, BlockDevice.read,
            random.randint(0, 100), random.randint(0, 100))
        self.assertEquals("node must be a Node or str, not int", str(error))

    def test__read_with_system_id(self):
        BlockDevice = make_origin().BlockDevice
        system_id = make_string_without_spaces()
        block = {
            "system_id": system_id,
            "id": random.randint(0, 100),
            "type": BlockDeviceType.PHYSICAL.value,
        }
        BlockDevice._handler.read.return_value = block
        BlockDevice.read(system_id, block['id'])
        BlockDevice._handler.read.assert_called_once_with(
            system_id=system_id, id=block['id'])

    def test__read_with_Node(self):
        origin = make_origin()
        BlockDevice = origin.BlockDevice
        Node = origin.Node
        system_id = make_string_without_spaces()
        node = Node(system_id)
        block = {
            "system_id": system_id,
            "id": random.randint(0, 100),
            "type": BlockDeviceType.PHYSICAL.value,
        }
        BlockDevice._handler.read.return_value = block
        BlockDevice.read(node, block['id'])
        BlockDevice._handler.read.assert_called_once_with(
            system_id=system_id, id=block['id'])

    def test__save_add_tag(self):
        BlockDevice = make_origin().BlockDevice
        system_id = make_string_without_spaces()
        block = BlockDevice({
            "system_id": system_id,
            "id": random.randint(0, 100),
            "type": BlockDeviceType.PHYSICAL.value,
            "tags": [],
        })
        tag = make_string_without_spaces()
        block.tags.append(tag)
        BlockDevice._handler.add_tag.return_value = None
        block.save()
        BlockDevice._handler.add_tag.assert_called_once_with(
            system_id=system_id, id=block.id, tag=tag)

    def test__save_remove_tag(self):
        BlockDevice = make_origin().BlockDevice
        system_id = make_string_without_spaces()
        tag = make_string_without_spaces()
        block = BlockDevice({
            "system_id": system_id,
            "id": random.randint(0, 100),
            "type": BlockDeviceType.PHYSICAL.value,
            "tags": [tag],
        })
        block.tags.remove(tag)
        BlockDevice._handler.remove_tag.return_value = None
        block.save()
        BlockDevice._handler.remove_tag.assert_called_once_with(
            system_id=system_id, id=block.id, tag=tag)

    def test__delete(self):
        BlockDevice = make_origin().BlockDevice
        system_id = make_string_without_spaces()
        block = BlockDevice({
            "system_id": system_id,
            "id": random.randint(0, 100),
            "type": BlockDeviceType.PHYSICAL.value,
        })
        BlockDevice._handler.delete.return_value = None
        block.delete()
        BlockDevice._handler.delete.assert_called_once_with(
            system_id=system_id, id=block.id)

    def test__set_as_boot_disk(self):
        BlockDevice = make_origin().BlockDevice
        system_id = make_string_without_spaces()
        block = BlockDevice({
            "system_id": system_id,
            "id": random.randint(0, 100),
            "type": BlockDeviceType.PHYSICAL.value,
        })
        BlockDevice._handler.set_boot_disk.return_value = None
        block.set_as_boot_disk()
        BlockDevice._handler.set_boot_disk.assert_called_once_with(
            system_id=system_id, id=block.id)

    def test__format(self):
        BlockDevice = make_origin().BlockDevice
        system_id = make_string_without_spaces()
        block_id = random.randint(0, 100)
        block = BlockDevice({
            "system_id": system_id,
            "id": block_id,
            "type": BlockDeviceType.PHYSICAL.value,
        })
        BlockDevice._handler.format.return_value = {
            "system_id": system_id,
            "id": block_id,
            "type": BlockDeviceType.PHYSICAL.value,
            "filesystem": {
                "fstype": "ext4",
            }
        }
        block.format("ext4")
        BlockDevice._handler.format.assert_called_once_with(
            system_id=system_id, id=block_id, fstype="ext4", uuid=None)

    def test__unformat(self):
        BlockDevice = make_origin().BlockDevice
        system_id = make_string_without_spaces()
        block_id = random.randint(0, 100)
        block = BlockDevice({
            "system_id": system_id,
            "id": block_id,
            "type": BlockDeviceType.PHYSICAL.value,
            "filesystem": {
                "fstype": "ext4",
            }
        })
        BlockDevice._handler.unformat.return_value = {
            "system_id": system_id,
            "id": block_id,
            "type": BlockDeviceType.PHYSICAL.value,
            "filesystem": None,
        }
        block.unformat()
        BlockDevice._handler.unformat.assert_called_once_with(
            system_id=system_id, id=block_id)

    def test__mount(self):
        BlockDevice = make_origin().BlockDevice
        system_id = make_string_without_spaces()
        block_id = random.randint(0, 100)
        block = BlockDevice({
            "system_id": system_id,
            "id": block_id,
            "type": BlockDeviceType.PHYSICAL.value,
            "filesystem": {
                "fstype": "ext4",
            }
        })
        BlockDevice._handler.mount.return_value = {
            "system_id": system_id,
            "id": block_id,
            "type": BlockDeviceType.PHYSICAL.value,
            "filesystem": {
                "fstype": "ext4",
                "mount_point": "/",
                "mount_options": "noatime"
            },
        }
        block.mount("/", mount_options="noatime")
        BlockDevice._handler.mount.assert_called_once_with(
            system_id=system_id, id=block_id, mount_point="/",
            mount_options="noatime")

    def test__unmount(self):
        BlockDevice = make_origin().BlockDevice
        system_id = make_string_without_spaces()
        block_id = random.randint(0, 100)
        block = BlockDevice({
            "system_id": system_id,
            "id": block_id,
            "type": BlockDeviceType.PHYSICAL.value,
            "filesystem": {
                "fstype": "ext4",
                "mount_point": "/",
                "mount_options": "noatime"
            }
        })
        BlockDevice._handler.unmount.return_value = {
            "system_id": system_id,
            "id": block_id,
            "type": BlockDeviceType.PHYSICAL.value,
            "filesystem": {
                "fstype": "ext4",
                "mount_point": "",
                "mount_options": ""
            },
        }
        block.unmount()
        BlockDevice._handler.unmount.assert_called_once_with(
            system_id=system_id, id=block_id)
