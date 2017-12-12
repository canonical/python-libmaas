"""Test for `maas.client.viscera.bcache_cache_sets`."""

import random

from testtools.matchers import Equals

from ..bcache_cache_sets import (
    BcacheCacheSet,
    BcacheCacheSets,
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
        BcacheCacheSets, BcacheCacheSet, BlockDevices, BlockDevice,
        Partitions, Partition, Nodes, Node)


class TestBcacheCacheSets(TestCase):

    def test__read_bad_node_type(self):
        BcacheCacheSets = make_origin().BcacheCacheSets
        error = self.assertRaises(
            TypeError, BcacheCacheSets.read, random.randint(0, 100))
        self.assertEquals("node must be a Node or str, not int", str(error))

    def test__read_with_system_id(self):
        BcacheCacheSets = make_origin().BcacheCacheSets
        system_id = make_string_without_spaces()
        cache_sets = [
            {
                "system_id": system_id,
                "id": random.randint(0, 100),
                "cache_device": {
                    "id": random.randint(0, 100),
                    "type": BlockDeviceType.PHYSICAL.value,
                }
            }
            for _ in range(3)
        ]
        BcacheCacheSets._handler.read.return_value = cache_sets
        cache_sets = BcacheCacheSets.read(system_id)
        self.assertThat(len(cache_sets), Equals(3))
        BcacheCacheSets._handler.read.assert_called_once_with(
            system_id=system_id)

    def test__read_with_Node(self):
        origin = make_origin()
        BcacheCacheSets, Node = origin.BcacheCacheSets, origin.Node
        system_id = make_string_without_spaces()
        node = Node(system_id)
        cache_sets = [
            {
                "system_id": system_id,
                "id": random.randint(0, 100),
                "cache_device": {
                    "id": random.randint(0, 100),
                    "type": BlockDeviceType.PHYSICAL.value,
                }
            }
            for _ in range(3)
        ]
        BcacheCacheSets._handler.read.return_value = cache_sets
        cache_sets = BcacheCacheSets.read(node)
        self.assertThat(len(cache_sets), Equals(3))
        BcacheCacheSets._handler.read.assert_called_once_with(
            system_id=system_id)

    def test__create_bad_node_type(self):
        origin = make_origin()
        BcacheCacheSets = origin.BcacheCacheSets
        error = self.assertRaises(
            TypeError, BcacheCacheSets.create,
            random.randint(0, 100), origin.BlockDevice({}))
        self.assertEquals("node must be a Node or str, not int", str(error))

    def test__create_bad_cache_device_type(self):
        BcacheCacheSets = make_origin().BcacheCacheSets
        error = self.assertRaises(
            TypeError, BcacheCacheSets.create,
            make_string_without_spaces(), random.randint(0, 100))
        self.assertEquals(
            "cache_device must be a BlockDevice or Partition, not int",
            str(error))

    def test__create_with_block_device(self):
        origin = make_origin()
        BcacheCacheSets = origin.BcacheCacheSets
        BlockDevice = origin.BlockDevice
        block_device = BlockDevice({
            'id': random.randint(0, 100),
        })
        BcacheCacheSets._handler.create.return_value = {
            'id': random.randint(0, 100),
            'cache_device': block_device
        }
        system_id = make_string_without_spaces()
        BcacheCacheSets.create(system_id, block_device)
        BcacheCacheSets._handler.create.assert_called_once_with(
            system_id=system_id, cache_device=block_device.id)

    def test__create_with_partition(self):
        origin = make_origin()
        BcacheCacheSets = origin.BcacheCacheSets
        Partition = origin.Partition
        partition = Partition({
            'id': random.randint(0, 100),
        })
        BcacheCacheSets._handler.create.return_value = {
            'id': random.randint(0, 100),
            'cache_device': partition
        }
        system_id = make_string_without_spaces()
        BcacheCacheSets.create(system_id, partition)
        BcacheCacheSets._handler.create.assert_called_once_with(
            system_id=system_id, cache_partition=partition.id)


class TestBcacheCacheSet(TestCase):

    def test__read_bad_node_type(self):
        BcacheCacheSet = make_origin().BcacheCacheSet
        error = self.assertRaises(
            TypeError, BcacheCacheSet.read,
            random.randint(0, 100), random.randint(0, 100))
        self.assertEquals("node must be a Node or str, not int", str(error))

    def test__read_with_system_id(self):
        BcacheCacheSet = make_origin().BcacheCacheSet
        system_id = make_string_without_spaces()
        cache_set = {
            "system_id": system_id,
            "id": random.randint(0, 100),
            "cache_device": {
                "id": random.randint(0, 100),
                "type": BlockDeviceType.PHYSICAL.value,
            }
        }
        BcacheCacheSet._handler.read.return_value = cache_set
        BcacheCacheSet.read(system_id, cache_set['id'])
        BcacheCacheSet._handler.read.assert_called_once_with(
            system_id=system_id, id=cache_set['id'])

    def test__read_with_Node(self):
        origin = make_origin()
        BcacheCacheSet = origin.BcacheCacheSet
        Node = origin.Node
        system_id = make_string_without_spaces()
        node = Node(system_id)
        cache_set = {
            "system_id": system_id,
            "id": random.randint(0, 100),
            "cache_device": {
                "id": random.randint(0, 100),
                "type": BlockDeviceType.PHYSICAL.value,
            }
        }
        BcacheCacheSet._handler.read.return_value = cache_set
        BcacheCacheSet.read(node, cache_set['id'])
        BcacheCacheSet._handler.read.assert_called_once_with(
            system_id=system_id, id=cache_set['id'])

    def test__delete(self):
        BcacheCacheSet = make_origin().BcacheCacheSet
        system_id = make_string_without_spaces()
        cache_set = BcacheCacheSet({
            "system_id": system_id,
            "id": random.randint(0, 100),
            "cache_device": {
                "id": random.randint(0, 100),
                "type": BlockDeviceType.PHYSICAL.value,
            }
        })
        BcacheCacheSet._handler.delete.return_value = None
        cache_set.delete()
        BcacheCacheSet._handler.delete.assert_called_once_with(
            system_id=system_id, id=cache_set.id)
