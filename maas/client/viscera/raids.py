"""Objects for RAIDs."""

__all__ = [
    "Raid",
    "Raids",
]

from typing import Iterable, Union

from . import (
    check,
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
    DevicesField,
    FilesystemGroup,
)
from ..enum import RaidLevel


class RaidType(ObjectType):
    """Metaclass for `Raid`."""

    async def read(cls, node, id):
        """Get `Raid` by `id`."""
        if isinstance(node, str):
            system_id = node
        elif isinstance(node, Node):
            system_id = node.system_id
        else:
            raise TypeError(
                "node must be a Node or str, not %s"
                % type(node).__name__)
        return cls(await cls._handler.read(system_id=system_id, id=id))


class Raid(FilesystemGroup, metaclass=RaidType):
    """A RAID on a machine."""

    uuid = ObjectField.Checked("uuid", check(str), check(str))

    level = ObjectField.Checked(
        "level", to(RaidLevel), readonly=True)
    size = ObjectField.Checked(
        "size", check(int), check(int), readonly=True)

    devices = DevicesField("devices")
    spare_devices = DevicesField("spare_devices")
    virtual_device = ObjectFieldRelated(
        "virtual_device", "BlockDevice", reverse=None, readonly=True)

    def __repr__(self):
        return super(Raid, self).__repr__(
            fields={"name", "level", "size"})

    async def delete(self):
        """Delete this RAID."""
        await self._handler.delete(
            system_id=self.node.system_id, id=self.id)


class RaidsType(ObjectType):
    """Metaclass for `Raids`."""

    async def read(cls, node):
        """Get list of `Raid`'s for `node`."""
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
            level: Union[RaidLevel, str],
            devices: Iterable[Union[BlockDevice, Partition]], *,
            name: str = None, uuid: str = None,
            spare_devices: Iterable[Union[BlockDevice, Partition]]):
        """
        Create a RAID on a Node.

        :param node: Node to create the interface on.
        :type node: `Node` or `str`
        :param level: RAID level.
        :type level: `RaidLevel`
        :param devices: Mixed list of block devices or partitions to create
            the RAID from.
        :type devices: iterable of mixed type of `BlockDevice` or `Partition`
        :param name: Name of the RAID (optional).
        :type name: `str`
        :param uuid: The UUID for the RAID (optional).
        :type uuid: `str`
        :param spare_devices: Mixed list of block devices or partitions to add
            as spare devices on the RAID.
        :type spare_devices: iterable of mixed type of `BlockDevice` or
            `Partition`
        """
        if isinstance(level, RaidLevel):
            level = level.value
        params = {
            'level': str(level),
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

        spare_block_devices = []
        spare_partitions = []
        for idx, device in enumerate(spare_devices):
            if isinstance(device, BlockDevice):
                spare_block_devices.append(device.id)
            elif isinstance(device, Partition):
                spare_partitions.append(device.id)
            else:
                raise TypeError(
                    "spare_devices[%d] must be a BlockDevice or "
                    "Partition, not %s" % type(device).__name__)
        if len(spare_block_devices) > 0:
            params['spare_devices'] = spare_block_devices
        if len(spare_partitions) > 0:
            params['spare_partitions'] = spare_partitions

        if name is not None:
            params['name'] = name
        if uuid is not None:
            params['uuid'] = uuid
        return cls._object(await cls._handler.create(**params))


class Raids(ObjectSet, metaclass=RaidsType):
    """The set of RAIDs on a machine."""

    @property
    def by_name(self):
        """Return mapping of name to `Raid`."""
        return {
            raid.name: raid
            for raid in self
        }

    def get_by_name(self, name):
        """Return a `Raid` by its name."""
        return self.by_name[name]
