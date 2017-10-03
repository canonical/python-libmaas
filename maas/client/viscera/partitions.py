"""Objects for partitions."""

__all__ = [
    "Partition",
    "Partitions",
]

from . import (
    check,
    Object,
    ObjectField,
    ObjectFieldRelated,
    ObjectSet,
    ObjectType,
)
from .nodes import Node
from .block_devices import BlockDevice


def map_device_id_to_dict(instance, value):
    """Convert a device_id into a dictionary for BlockDevice."""
    return {
        'system_id': instance._data['system_id'],
        'id': value,
        '__incomplete__': True
    }


class PartitionType(ObjectType):
    """Metaclass for `Partition`."""

    async def read(cls, node, block_device, id):
        """Get `Partition` by `id`."""
        if isinstance(node, str):
            system_id = node
        elif isinstance(node, Node):
            system_id = node.system_id
        else:
            raise TypeError(
                "node must be a Node or str, not %s"
                % type(node).__name__)
        if isinstance(block_device, int):
            block_device = block_device
        elif isinstance(block_device, BlockDevice):
            block_device = block_device.id
        else:
            raise TypeError(
                "node must be a Node or str, not %s"
                % type(block_device).__name__)
        return cls(await cls._handler.read(
            system_id=system_id, device_id=block_device, id=id))


class Partition(Object, metaclass=PartitionType):
    """A partition on a block device."""

    block_device = ObjectFieldRelated(
        "device_id", "BlockDevice", readonly=True, pk=0,
        map_func=map_device_id_to_dict)
    id = ObjectField.Checked(
        "id", check(int), readonly=True, pk=1)
    uuid = ObjectField.Checked(
        "uuid", check(str), readonly=True)
    path = ObjectField.Checked(
        "path", check(str), readonly=True)
    size = ObjectField.Checked(
        "size", check(int), readonly=True)
    used_for = ObjectField.Checked(
        "used_for", check(str), readonly=True)

    filesystem = ObjectFieldRelated(
        "filesystem", "Filesystem", readonly=True)

    def __repr__(self):
        return super(Partition, self).__repr__(
            fields={"path", "size"})

    async def delete(self):
        """Delete this partition."""
        await self._handler.delete(
            system_id=self.block_device.node.system_id,
            device_id=self.block_device.id, id=self.id)

    async def format(self, fstype, *, uuid=None):
        """Format this partition."""
        self._data = await self._handler.format(
            system_id=self.block_device.node.system_id,
            device_id=self.block_device.id, id=self.id,
            fstype=fstype, uuid=uuid)

    async def unformat(self):
        """Unformat this partition."""
        self._data = await self._handler.unformat(
            system_id=self.block_device.node.system_id,
            device_id=self.block_device.id, id=self.id)

    async def mount(self, mount_point, *, mount_options=None):
        """Mount this partition."""
        self._data = await self._handler.mount(
            system_id=self.block_device.node.system_id,
            device_id=self.block_device.id, id=self.id,
            mount_point=mount_point,
            mount_options=mount_options)

    async def umount(self):
        """Unmount this partition."""
        self._data = await self._handler.unmount(
            system_id=self.block_device.node.system_id,
            device_id=self.block_device.id, id=self.id)


class PartitionsType(ObjectType):
    """Metaclass for `Partitions`."""

    async def read(cls, node, block_device):
        """Get list of `Partitions`'s for `node` and `block_device`."""
        if isinstance(node, str):
            system_id = node
        elif isinstance(node, Node):
            system_id = node.system_id
        else:
            raise TypeError(
                "node must be a Node or str, not %s"
                % type(node).__name__)
        if isinstance(block_device, int):
            block_device = block_device
        elif isinstance(block_device, BlockDevice):
            block_device = block_device.id
        else:
            raise TypeError(
                "node must be a Node or str, not %s"
                % type(block_device).__name__)
        data = await cls._handler.read(
            system_id=system_id, device_id=block_device)
        return cls(
            cls._object(item)
            for item in data)

    async def create(cls, block_device: BlockDevice, size: int):
        """
        Create a partition on a block device.

        :param block_device: BlockDevice to create the paritition on.
        :type block_device: `BlockDevice`
        :param size: The size of the partition in bytes.
        :type size: `int`
        """
        params = {}
        if isinstance(block_device, BlockDevice):
            params['system_id'] = block_device.node.system_id
            params['device_id'] = block_device.id
        else:
            raise TypeError(
                'block_device must be a BlockDevice, not %s' % (
                    type(block_device).__name__))

        if not size:
            raise ValueError("size must be provided and greater than zero.")
        params['size'] = size
        return cls._object(await cls._handler.create(**params))


class Partitions(ObjectSet, metaclass=PartitionsType):
    """The set of partitions on a block device."""
