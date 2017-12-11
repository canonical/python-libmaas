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
        Nodes, Node)


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
