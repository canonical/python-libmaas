"""Objects for cache sets."""

__all__ = [
    "BcacheCacheSet",
    "BcacheCacheSets",
]

from typing import Union

from . import (
    ObjectSet,
    ObjectType,
)
from .nodes import Node
from .block_devices import BlockDevice
from .partitions import Partition
from .filesystem_groups import (
    DeviceField,
    FilesystemGroup,
)


class BcacheCacheSetType(ObjectType):
    """Metaclass for `BcacheCacheSet`."""

    async def read(cls, node, id):
        """Get `BcacheCacheSet` by `id`."""
        if isinstance(node, str):
            system_id = node
        elif isinstance(node, Node):
            system_id = node.system_id
        else:
            raise TypeError(
                "node must be a Node or str, not %s"
                % type(node).__name__)
        return cls(await cls._handler.read(system_id=system_id, id=id))


class BcacheCacheSet(FilesystemGroup, metaclass=BcacheCacheSetType):
    """A cache set on a machine."""

    cache_device = DeviceField("cache_device")

    def __repr__(self):
        return super(BcacheCacheSet, self).__repr__(
            fields={"name", "cache_device"})

    async def delete(self):
        """Delete this cache set."""
        await self._handler.delete(
            system_id=self.node.system_id, id=self.id)


class BcacheCacheSetsType(ObjectType):
    """Metaclass for `BcacheCacheSets`."""

    async def read(cls, node):
        """Get list of `BcacheCacheSet`'s for `node`."""
        if isinstance(node, str):
            system_id = node
        elif isinstance(node, Node):
            system_id = node.system_id
        else:
            raise TypeError(
                "node must be a Node or str, not %s"
                % type(node).__name__)
        data = await cls._handler.read(system_id=system_id)
        return cls(
            cls._object(
                item, local_data={"node_system_id": system_id})
            for item in data)

    async def create(
            cls, node: Union[Node, str],
            cache_device: Union[BlockDevice, Partition]):
        """
        Create a BcacheCacheSet on a Node.

        :param node: Node to create the interface on.
        :type node: `Node` or `str`
        :param cache_device: Block device or partition to create
            the cache set on.
        :type cache_device: `BlockDevice` or `Partition`
        """
        params = {}
        if isinstance(node, str):
            params['system_id'] = node
        elif isinstance(node, Node):
            params['system_id'] = node.system_id
        else:
            raise TypeError(
                'node must be a Node or str, not %s' % (
                    type(node).__name__))
        if isinstance(cache_device, BlockDevice):
            params['cache_device'] = cache_device.id
        elif isinstance(cache_device, Partition):
            params['cache_partition'] = cache_device.id
        else:
            raise TypeError(
                'cache_device must be a BlockDevice or Partition, not %s' % (
                    type(cache_device).__name__))

        return cls._object(await cls._handler.create(**params))


class BcacheCacheSets(ObjectSet, metaclass=BcacheCacheSetsType):
    """The set of cache sets on a machine."""
