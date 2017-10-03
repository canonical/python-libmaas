"""Objects for Bcaches."""

__all__ = [
    "Bcache",
    "Bcaches",
]

from typing import Iterable, Union

from . import (
    ObjectField,
    ObjectFieldRelated,
    ObjectSet,
    ObjectType,
    to,
)
from .nodes import Node
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
            backing_device: Union[BlockDevice, Partition],
            cache_mode: CacheMode, *,
            name: str=None, uuid: str=None):
        """
        Create a Bcache on a Node.

        :param node: Node to create the interface on.
        :type node: `Node` or `str`
        :param devices: Mixed list of block devices or partitions to create
            the Bcache from.
        :type devices: iterable of mixed type of `BlockDevice` or `Partition`
        :param name: Name of the Bcache (optional).
        :type name: `str`
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

        if len(devices) == 0:
            raise ValueError("devices must contain at least one device.")

        block_devices = []
        partitions = []
        for idx, device in enumerate(devices):
            if isinstance(device, BlockDevice):
                block_devices.append(device.id)
            elif isinstance(device, Partition):
                partitions.append(device.id)
            else:
                raise TypeError(
                    "devices[%d] must be a BlockDevice or "
                    "Partition, not %s" % type(device).__name__)
        if len(block_devices) > 0:
            params['block_devices'] = block_devices
        if len(partitions) > 0:
            params['partitions'] = partitions
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
