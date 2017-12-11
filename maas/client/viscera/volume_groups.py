"""Objects for volume groups."""

__all__ = [
    "VolumeGroup",
    "VolumeGroups",
]

from typing import Iterable, Union

from . import (
    check,
    ObjectField,
    ObjectFieldRelatedSet,
    ObjectSet,
    ObjectType,
)
from .nodes import Node
from .block_devices import BlockDevice
from .partitions import Partition
from .filesystem_groups import (
    FilesystemGroup,
    DevicesField,
)


class VolumeGroupType(ObjectType):
    """Metaclass for `VolumeGroup`."""

    async def read(cls, node, id):
        """Get `VolumeGroup` by `id`."""
        if isinstance(node, str):
            system_id = node
        elif isinstance(node, Node):
            system_id = node.system_id
        else:
            raise TypeError(
                "node must be a Node or str, not %s"
                % type(node).__name__)
        return cls(await cls._handler.read(system_id=system_id, id=id))


class VolumeGroup(FilesystemGroup, metaclass=VolumeGroupType):
    """A volume group on a machine."""

    uuid = ObjectField.Checked("uuid", check(str), check(str))

    size = ObjectField.Checked(
        "size", check(int), check(int), readonly=True)
    available_size = ObjectField.Checked(
        "available_size", check(int), readonly=True)
    used_size = ObjectField.Checked(
        "used_size", check(int), readonly=True)

    devices = DevicesField("devices")
    logical_volumes = ObjectFieldRelatedSet(
        "logical_volumes", "BlockDevices", reverse=None)

    def __repr__(self):
        return super(VolumeGroup, self).__repr__(
            fields={"name", "size"})

    async def delete(self):
        """Delete this volume group."""
        await self._handler.delete(
            system_id=self.node.system_id, id=self.id)


class VolumeGroupsType(ObjectType):
    """Metaclass for `VolumeGroups`."""

    async def read(cls, node):
        """Get list of `VolumeGroup`'s for `node`."""
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
            devices: Iterable[Union[BlockDevice, Partition]],
            *, uuid: str=None):
        """
        Create a volume group on a Node.

        :param node: Node to create the interface on.
        :type node: `Node` or `str`
        :param name: Name of the volume group.
        :type name: `str`
        :param devices: Mixed list of block devices or partitions to create
            the volume group from.
        :type devices: iterable of mixed type of `BlockDevice` or `Partition`
        :param uuid: The UUID for the volume group (optional).
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


class VolumeGroups(ObjectSet, metaclass=VolumeGroupsType):
    """The set of volume groups on a machine."""

    @property
    def by_name(self):
        """Return mapping of name to `VolumeGroup`."""
        return {
            vg.name: vg
            for vg in self
        }

    def get_by_name(self, name):
        """Return a `VolumeGroup` by its name."""
        return self.by_name[name]
