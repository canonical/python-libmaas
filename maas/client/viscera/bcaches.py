"""Objects for Bcaches."""

__all__ = [
    "Bcache",
    "Bcaches",
]

from typing import Union

from . import (
    ObjectField,
    ObjectFieldRelated,
    ObjectSet,
    ObjectType,
    to,
    check,
)
from .nodes import Node
from .bcache_cache_sets import BcacheCacheSet
from .block_devices import BlockDevice
from .partitions import Partition
from .filesystem_groups import (
    DeviceField,
    FilesystemGroup,
)
from ..enum import CacheMode


class BcacheType(ObjectType):
    """Metaclass for `Bcache`."""

    async def read(cls, node, id):
        """Get `Bcache` by `id`."""
        if isinstance(node, str):
            system_id = node
        elif isinstance(node, Node):
            system_id = node.system_id
        else:
            raise TypeError(
                "node must be a Node or str, not %s"
                % type(node).__name__)
        return cls(await cls._handler.read(system_id=system_id, id=id))


class Bcache(FilesystemGroup, metaclass=BcacheType):
    """A Bcache on a machine."""

    cache_mode = ObjectField.Checked(
        "cache_mode", to(CacheMode), check(CacheMode))
    uuid = ObjectField.Checked("uuid", check(str), check(str))

    backing_device = DeviceField("backing_device")
    cache_set = ObjectFieldRelated(
        "cache_set", "BcacheCacheSet", reverse=None)
    virtual_device = ObjectFieldRelated(
        "virtual_device", "BlockDevice", reverse=None, readonly=True)

    def __repr__(self):
        return super(Bcache, self).__repr__(
            fields={"name", "cache_mode", "size", "backing_device"})

    async def delete(self):
        """Delete this Bcache."""
        await self._handler.delete(
            system_id=self.node.system_id, id=self.id)


class BcachesType(ObjectType):
    """Metaclass for `Bcaches`."""

    async def read(cls, node):
        """Get list of `Bcache`'s for `node`."""
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
            name: str,
            backing_device: Union[BlockDevice, Partition],
            cache_set: Union[BcacheCacheSet, int],
            cache_mode: CacheMode, *,
            uuid: str = None):
        """
        Create a Bcache on a Node.

        :param node: Node to create the interface on.
        :type node: `Node` or `str`
        :param name: Name of the Bcache.
        :type name: `str`
        :param backing_device: Either a block device or partition to create
            the Bcache from.
        :type backing_device: `BlockDevice` or `Partition`
        :param cache_set: Bcache cache set to use in front of backing device.
        :type cache_set: `BcacheCacheSet` or `int`
        :param cache_mode: Caching mode to use for this device.
        :type cache_mode: `CacheMode`
        :type backing_device: `BlockDevice` or `Partition`
        :param uuid: The UUID for the Bcache (optional).
        :type uuid: `str`
        """
        params = {
            'name': name,
        }
        if isinstance(node, str):
            params['system_id'] = node
        elif isinstance(node, Node):
            params['system_id'] = node.system_id
        else:
            raise TypeError(
                'node must be a Node or str, not %s' % (
                    type(node).__name__))

        if isinstance(backing_device, BlockDevice):
            params['backing_device'] = backing_device.id
        elif isinstance(backing_device, Partition):
            params['backing_partition'] = backing_device.id
        else:
            raise TypeError(
                "backing_device must be a BlockDevice or Partition, "
                "not %s" % type(backing_device).__name__)

        if isinstance(cache_set, BcacheCacheSet):
            params['cache_set'] = cache_set.id
        elif isinstance(cache_set, int):
            params['cache_set'] = cache_set
        else:
            raise TypeError(
                "cache_set must be a BcacheCacheSet or int, "
                "not %s" % type(cache_set).__name__)

        if isinstance(cache_mode, CacheMode):
            params['cache_mode'] = cache_mode.value
        else:
            raise TypeError(
                "cache_mode must be a CacheMode, "
                "not %s" % type(cache_mode).__name__)

        if uuid is not None:
            params['uuid'] = uuid
        return cls._object(await cls._handler.create(**params))


class Bcaches(ObjectSet, metaclass=BcachesType):
    """The set of Bcaches on a machine."""

    @property
    def by_name(self):
        """Return mapping of name to `Bcache`."""
        return {
            bcache.name: bcache
            for bcache in self
        }

    def get_by_name(self, name):
        """Return a `Bcache` by its name."""
        return self.by_name[name]
