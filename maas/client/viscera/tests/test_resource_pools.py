"""Tests for `maas.client.viscera.resource_pools`."""

import random

from testtools.matchers import (
    Equals,
    IsInstance,
    MatchesStructure,
)

from .. import resource_pools

from ..testing import bind
from ...testing import (
    make_string_without_spaces,
    TestCase,
)


def make_origin():
    """
    Create a new origin with ResourcePool and ResourcePools. The former
    refers to the latter via the origin, hence why it must be bound.
    """
    return bind(resource_pools.ResourcePools, resource_pools.ResourcePool)


class TestResourcePools(TestCase):

    def test_resource_pools_create(self):
        origin = make_origin()
        pool_id = random.randint(0, 100)
        name = make_string_without_spaces()
        description = make_string_without_spaces()
        origin.ResourcePools._handler.create.return_value = {
            "id": pool_id,
            "name": name,
            "description": description,
        }
        pool = origin.ResourcePools.create(
            name=name,
            description=description,
        )
        origin.ResourcePools._handler.create.assert_called_once_with(
            name=name,
            description=description,
        )
        self.assertThat(pool, IsInstance(origin.ResourcePool))
        self.assertThat(pool, MatchesStructure.byEquality(
            id=pool_id, name=name, description=description
        ))

    def test_resource_pools_create_without_description(self):
        origin = make_origin()
        pool_id = random.randint(0, 100)
        name = make_string_without_spaces()
        description = ''
        origin.ResourcePools._handler.create.return_value = {
            "id": pool_id,
            "name": name,
            "description": description,
        }
        pool = origin.ResourcePools.create(
            name=name,
            description=description,
        )
        origin.ResourcePools._handler.create.assert_called_once_with(
            name=name,
            description=description,
        )
        self.assertThat(pool, IsInstance(origin.ResourcePool))
        self.assertThat(pool, MatchesStructure.byEquality(
            id=pool_id, name=name, description=description
        ))

    def test_resource_pools_read(self):
        ResourcePools = make_origin().ResourcePools
        pools = [
            {
                "id": random.randint(0, 100),
                "name": make_string_without_spaces(),
                "description": make_string_without_spaces(),
            }
            for _ in range(3)
        ]
        ResourcePools._handler.read.return_value = pools
        pools = ResourcePools.read()
        self.assertThat(len(pools), Equals(3))


class TestResourcePool(TestCase):

    def test_resource_pool_read(self):
        ResourcePool = make_origin().ResourcePool
        pool = {
            "id": random.randint(0, 100),
            "name": make_string_without_spaces(),
            "description": make_string_without_spaces(),
        }
        ResourcePool._handler.read.return_value = pool
        self.assertThat(
            ResourcePool.read(id=pool['id']), Equals(ResourcePool(pool)))
        ResourcePool._handler.read.assert_called_once_with(id=pool['id'])

    def test_resource_pool_delete(self):
        ResourcePool = make_origin().ResourcePool
        pool_id = random.randint(0, 100)
        pool = ResourcePool({
            "id": pool_id,
            "name": make_string_without_spaces(),
            "description": make_string_without_spaces(),
        })
        pool.delete()
        ResourcePool._handler.delete.assert_called_once_with(id=pool_id)
