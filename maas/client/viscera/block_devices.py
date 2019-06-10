"""Objects for block devices."""

__all__ = [
    "BlockDevice",
    "BlockDevices",
]

from typing import Iterable, Union

from . import (
    check,
    check_optional,
    Object,
    ObjectField,
    ObjectFieldRelated,
    ObjectFieldRelatedSet,
    ObjectSet,
    ObjectType,
    to,
)
from .nodes import Node
from ..enum import (
    BlockDeviceType,
    PartitionTableType,
)
from ..utils import remove_None


class BlockDeviceTypeMeta(ObjectType):
    """Metaclass for `BlockDevice`."""

    async def read(cls, node, id):
        """Get `BlockDevice` by `id`."""
        if isinstance(node, str):
            system_id = node
        elif isinstance(node, Node):
            system_id = node.system_id
        else:
            raise TypeError(
                "node must be a Node or str, not %s"
                % type(node).__name__)
        return cls(await cls._handler.read(system_id=system_id, id=id))


class BlockDevice(Object, metaclass=BlockDeviceTypeMeta):
    """A block device on a machine."""

    node = ObjectFieldRelated(
        "system_id", "Node", readonly=True, pk=0)
    id = ObjectField.Checked(
        "id", check(int), readonly=True, pk=1)
    type = ObjectField.Checked(
        "type", to(BlockDeviceType), readonly=True)
    name = ObjectField.Checked(
        "name", check(str), check(str), alt_pk=1)
    model = ObjectField.Checked(
        "model", check_optional(str), check_optional(str))
    serial = ObjectField.Checked(
        "serial", check_optional(str), check_optional(str))
    id_path = ObjectField.Checked(
        "id_path", check_optional(str), check_optional(str))
    size = ObjectField.Checked(
        "size", check(int), check(int))
    block_size = ObjectField.Checked(
        "block_size", check(int), check(int))
    uuid = ObjectField.Checked(
        "uuid", check(str), check(str))
    tags = ObjectField.Checked(
        "tags", check(list), check(list))

    available_size = ObjectField.Checked(
        "available_size", check(int), readonly=True)
    used_size = ObjectField.Checked(
        "used_size", check(int), readonly=True)
    used_for = ObjectField.Checked(
        "used_for", check(str), readonly=True)
    partition_table_type = ObjectField.Checked(
        "partition_table_type", to(PartitionTableType), readonly=True)

    partitions = ObjectFieldRelatedSet("partitions", "Partitions")
    filesystem = ObjectFieldRelated(
        "filesystem", "Filesystem", readonly=True)

    def __repr__(self):
        if self.type == BlockDeviceType.PHYSICAL:
            return super(BlockDevice, self).__repr__(
                name="PhysicalBlockDevice",
                fields={"name", "model", "serial", "id_path"})
        elif self.type == BlockDeviceType.VIRTUAL:
            return super(BlockDevice, self).__repr__(
                name="VirtualBlockDevice",
                fields={"name", })
        else:
            raise ValueError("Unknown type: %s" % self.type)

    async def save(self):
        """Save this block device."""
        old_tags = list(self._orig_data['tags'])
        new_tags = list(self.tags)
        self._changed_data.pop('tags', None)
        await super(BlockDevice, self).save()
        for tag_name in new_tags:
            if tag_name not in old_tags:
                await self._handler.add_tag(
                    system_id=self.node.system_id, id=self.id, tag=tag_name)
            else:
                old_tags.remove(tag_name)
        for tag_name in old_tags:
            await self._handler.remove_tag(
                system_id=self.node.system_id, id=self.id, tag=tag_name)
        self._orig_data['tags'] = new_tags
        self._data['tags'] = list(new_tags)

    async def delete(self):
        """Delete this block device."""
        await self._handler.delete(
            system_id=self.node.system_id, id=self.id)

    async def set_as_boot_disk(self):
        """Set as boot disk for this node."""
        await self._handler.set_boot_disk(
            system_id=self.node.system_id, id=self.id)

    async def format(self, fstype, *, uuid=None):
        """Format this block device."""
        self._reset(await self._handler.format(
            system_id=self.node.system_id, id=self.id,
            fstype=fstype, uuid=uuid))

    async def unformat(self):
        """Unformat this block device."""
        self._reset(await self._handler.unformat(
            system_id=self.node.system_id, id=self.id))

    async def mount(self, mount_point, *, mount_options=None):
        """Mount this block device."""
        self._reset(await self._handler.mount(
            system_id=self.node.system_id, id=self.id, mount_point=mount_point,
            mount_options=mount_options))

    async def unmount(self):
        """Unmount this block device."""
        self._reset(await self._handler.unmount(
            system_id=self.node.system_id, id=self.id))


class BlockDevicesType(ObjectType):
    """Metaclass for `BlockDevices`."""

    async def read(cls, node):
        """Get list of `BlockDevice`'s for `node`."""
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
            cls, node: Union[Node, str], name: str,
            *, model: str = None, serial: str = None,
            id_path: str = None, size: int = None, block_size: int = 512,
            tags: Iterable[str] = None):
        """
        Create a physical block device on a Node.

        Either model and serial or id_path must be provided when creating a
        `BlockDevice`. Size (bytes) is always required.

        NOTE: It is recommended to use the MAAS commissioning process to
        discover `BlockDevice`'s on a machine. Getting any of this information
        incorrect can result on the machine failing to deploy.

        :param node: Node to create the block device on.
        :type node: `Node` or `str`
        :param name: The name for the block device.
        :type name: `str`
        :param model: The model number for the block device.
        :type model: `str`
        :param serial: The serial number for the block device.
        :type serial: `str`
        :param id_path: Unique path that identifies the device no matter
            the kernel the machine boots. Use only when the block device
            does not have a model and serial number.
        :type id_path: `str`
        :param size: The size of the block device in bytes.
        :type size: `int`
        :param block_size: The block size of the block device in bytes.
        :type block_size: `int`
        :param tags: List of tags to add to the block device.
        :type tags: sequence of `str`
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

        if not size or size < 0:
            raise ValueError("size must be provided and greater than zero.")
        if not block_size or block_size < 0:
            raise ValueError(
                "block_size must be provided and greater than zero.")
        if model and not serial:
            raise ValueError("serial must be provided when model is provided.")
        if not model and serial:
            raise ValueError("model must be provided when serial is provided.")
        if not model and not serial and not id_path:
            raise ValueError(
                "Either model/serial is provided or id_path must be provided.")

        params.update(remove_None({
            'name': name,
            'model': model,
            'serial': serial,
            'id_path': id_path,
            'size': size,
            'block_size': block_size,
        }))
        device = cls._object(await cls._handler.create(**params))
        if tags:
            device.tags = tags
            await device.save()
        return device


class BlockDevices(ObjectSet, metaclass=BlockDevicesType):
    """The set of block devices on a machine."""

    @property
    def by_name(self):
        """Return mapping of name of block device to `BlockDevice`."""
        return {
            bd.name: bd
            for bd in self
        }

    def get_by_name(self, name):
        """Return a `BlockDevice` by its name."""
        return self.by_name[name]
