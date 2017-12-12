"""Test for `maas.client.viscera.bcache_cache_sets`."""

import random

from testtools.matchers import Equals

from ..bcache_cache_sets import (
    BcacheCacheSet,
    BcacheCacheSets,
)
from ..bcaches import (
    Bcache,
    Bcaches,
)
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
from ...enum import BlockDeviceType, CacheMode
from ...testing import (
    make_string_without_spaces,
    TestCase,
)


def make_origin():
    """
    Create a new origin with required objects.
    """
    return bind(
        Bcaches, Bcache, BcacheCacheSets, BcacheCacheSet,
        BlockDevices, BlockDevice, Partitions, Partition,
        Nodes, Node)


class TestBcaches(TestCase):

    def test__by_name(self):
        origin = make_origin()
        Bcaches, Bcache = origin.Bcaches, origin.Bcache
        system_id = make_string_without_spaces()
        bcache_names = [
            make_string_without_spaces()
            for _ in range(3)
        ]
        bcaches_by_name = {
            name: Bcache({
                "system_id": system_id,
                "id": random.randint(0, 100),
                "name": name,
                "backing_device": {
                    "id": random.randint(0, 100),
                    "type": BlockDeviceType.PHYSICAL.value,
                },
                "cache_set": {
                    "id": random.randint(0, 100),
                },
                "virtual_device": {
                    "id": random.randint(0, 100),
                    "type": BlockDeviceType.VIRTUAL.value,
                },
            })
            for name in bcache_names
        }
        bcaches = Bcaches([
            obj
            for _, obj in bcaches_by_name.items()
        ])
        self.assertEqual(bcaches_by_name, bcaches.by_name)

    def test__get_by_name(self):
        origin = make_origin()
        Bcaches, Bcache = origin.Bcaches, origin.Bcache
        system_id = make_string_without_spaces()
        bcache_names = [
            make_string_without_spaces()
            for _ in range(3)
        ]
        bcaches_by_name = {
            name: Bcache({
                "system_id": system_id,
                "id": random.randint(0, 100),
                "name": name,
                "backing_device": {
                    "id": random.randint(0, 100),
                    "type": BlockDeviceType.PHYSICAL.value,
                },
                "cache_set": {
                    "id": random.randint(0, 100),
                },
                "virtual_device": {
                    "id": random.randint(0, 100),
                    "type": BlockDeviceType.VIRTUAL.value,
                },
            })
            for name in bcache_names
        }
        bcaches = Bcaches([
            obj
            for _, obj in bcaches_by_name.items()
        ])
        name = bcache_names[0]
        self.assertEqual(bcaches_by_name[name], bcaches.get_by_name(name))

    def test__read_bad_node_type(self):
        Bcaches = make_origin().Bcaches
        error = self.assertRaises(
            TypeError, Bcaches.read, random.randint(0, 100))
        self.assertEquals("node must be a Node or str, not int", str(error))

    def test__read_with_system_id(self):
        Bcaches = make_origin().Bcaches
        system_id = make_string_without_spaces()
        bcaches = [
            {
                "system_id": system_id,
                "id": random.randint(0, 100),
                "name": make_string_without_spaces(),
                "backing_device": {
                    "id": random.randint(0, 100),
                    "type": BlockDeviceType.PHYSICAL.value,
                },
                "cache_set": {
                    "id": random.randint(0, 100),
                },
                "virtual_device": {
                    "id": random.randint(0, 100),
                    "type": BlockDeviceType.VIRTUAL.value,
                },
            }
            for _ in range(3)
        ]
        Bcaches._handler.read.return_value = bcaches
        bcaches = Bcaches.read(system_id)
        self.assertThat(len(bcaches), Equals(3))
        Bcaches._handler.read.assert_called_once_with(
            system_id=system_id)

    def test__read_with_Node(self):
        origin = make_origin()
        Bcaches, Node = origin.Bcaches, origin.Node
        system_id = make_string_without_spaces()
        node = Node(system_id)
        bcaches = [
            {
                "system_id": system_id,
                "id": random.randint(0, 100),
                "name": make_string_without_spaces(),
                "backing_device": {
                    "id": random.randint(0, 100),
                    "type": BlockDeviceType.PHYSICAL.value,
                },
                "cache_set": {
                    "id": random.randint(0, 100),
                },
                "virtual_device": {
                    "id": random.randint(0, 100),
                    "type": BlockDeviceType.VIRTUAL.value,
                },
            }
            for _ in range(3)
        ]
        Bcaches._handler.read.return_value = bcaches
        bcaches = Bcaches.read(node)
        self.assertThat(len(bcaches), Equals(3))
        Bcaches._handler.read.assert_called_once_with(
            system_id=system_id)

    def test__create_bad_node_type(self):
        origin = make_origin()
        Bcaches = origin.Bcaches
        error = self.assertRaises(
            TypeError, Bcaches.create,
            random.randint(0, 100),
            make_string_without_spaces(), origin.BlockDevice({}),
            random.randint(0, 100), CacheMode.WRITETHROUGH)
        self.assertEquals("node must be a Node or str, not int", str(error))

    def test__create_bad_cache_device_type(self):
        Bcaches = make_origin().Bcaches
        error = self.assertRaises(
            TypeError, Bcaches.create,
            make_string_without_spaces(),
            make_string_without_spaces(), random.randint(0, 100),
            random.randint(0, 100), CacheMode.WRITETHROUGH)
        self.assertEquals(
            "backing_device must be a BlockDevice or Partition, not int",
            str(error))

    def test__create_bad_cache_set_type(self):
        origin = make_origin()
        Bcaches = origin.Bcaches
        error = self.assertRaises(
            TypeError, Bcaches.create,
            make_string_without_spaces(),
            make_string_without_spaces(), origin.BlockDevice({
                'id': random.randint(0, 100)
            }),
            make_string_without_spaces(), CacheMode.WRITETHROUGH)
        self.assertEquals(
            "cache_set must be a BcacheCacheSet or int, not str",
            str(error))

    def test__create_bad_cache_mode_type(self):
        origin = make_origin()
        Bcaches = origin.Bcaches
        error = self.assertRaises(
            TypeError, Bcaches.create,
            make_string_without_spaces(),
            make_string_without_spaces(), origin.BlockDevice({
                'id': random.randint(0, 100)
            }),
            random.randint(0, 100), 'writethrough')
        self.assertEquals(
            "cache_mode must be a CacheMode, not str",
            str(error))

    def test__create_with_block_device(self):
        origin = make_origin()
        Bcaches = origin.Bcaches
        BlockDevice = origin.BlockDevice
        BcacheCacheSet = origin.BcacheCacheSet
        block_device = BlockDevice({
            'id': random.randint(0, 100),
        })
        cache_set = BcacheCacheSet({
            'id': random.randint(0, 100),
        })
        Bcaches._handler.create.return_value = {
            'id': random.randint(0, 100),
            'backing_device': block_device._data,
            'cache_set': cache_set._data,
        }
        name = make_string_without_spaces()
        system_id = make_string_without_spaces()
        Bcaches.create(
            system_id, name, block_device, cache_set, CacheMode.WRITEBACK)
        Bcaches._handler.create.assert_called_once_with(
            system_id=system_id, name=name, backing_device=block_device.id,
            cache_set=cache_set.id, cache_mode=CacheMode.WRITEBACK.value)

    def test__create_with_partition(self):
        origin = make_origin()
        Bcaches = origin.Bcaches
        Partition = origin.Partition
        partition = Partition({
            'id': random.randint(0, 100),
        })
        cache_set_id = random.randint(0, 100)
        Bcaches._handler.create.return_value = {
            'id': random.randint(0, 100),
            'backing_device': partition._data,
            'cache_set': {
                'id': cache_set_id
            },
        }
        name = make_string_without_spaces()
        system_id = make_string_without_spaces()
        Bcaches.create(
            system_id, name, partition, cache_set_id, CacheMode.WRITEBACK)
        Bcaches._handler.create.assert_called_once_with(
            system_id=system_id, name=name, backing_partition=partition.id,
            cache_set=cache_set_id, cache_mode=CacheMode.WRITEBACK.value)


class TestBcache(TestCase):

    def test__read_bad_node_type(self):
        Bcache = make_origin().Bcache
        error = self.assertRaises(
            TypeError, Bcache.read,
            random.randint(0, 100), random.randint(0, 100))
        self.assertEquals("node must be a Node or str, not int", str(error))

    def test__read_with_system_id(self):
        Bcache = make_origin().Bcache
        system_id = make_string_without_spaces()
        bcache = {
            "system_id": system_id,
            "id": random.randint(0, 100),
            "backing_device": {
                "id": random.randint(0, 100),
                "type": BlockDeviceType.PHYSICAL.value,
            }
        }
        Bcache._handler.read.return_value = bcache
        Bcache.read(system_id, bcache['id'])
        Bcache._handler.read.assert_called_once_with(
            system_id=system_id, id=bcache['id'])

    def test__read_with_Node(self):
        origin = make_origin()
        Bcache = origin.Bcache
        Node = origin.Node
        system_id = make_string_without_spaces()
        node = Node(system_id)
        bcache = {
            "system_id": system_id,
            "id": random.randint(0, 100),
            "backing_device": {
                "id": random.randint(0, 100),
                "type": BlockDeviceType.PHYSICAL.value,
            }
        }
        Bcache._handler.read.return_value = bcache
        Bcache.read(node, bcache['id'])
        Bcache._handler.read.assert_called_once_with(
            system_id=system_id, id=bcache['id'])

    def test__delete(self):
        Bcache = make_origin().Bcache
        system_id = make_string_without_spaces()
        bcache = Bcache({
            "system_id": system_id,
            "id": random.randint(0, 100),
            "backing_device": {
                "id": random.randint(0, 100),
                "type": BlockDeviceType.PHYSICAL.value,
            }
        })
        Bcache._handler.delete.return_value = None
        bcache.delete()
        Bcache._handler.delete.assert_called_once_with(
            system_id=system_id, id=bcache.id)
