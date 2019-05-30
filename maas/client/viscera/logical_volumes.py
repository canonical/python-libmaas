"""Objects for logical volumes."""

__all__ = [
    "LogicalVolume",
    "LogicalVolumes",
]

from typing import Iterable

from .block_devices import (
    BlockDevice,
    BlockDevices,
    BlockDevicesType,
    BlockDeviceTypeMeta,
)
from .volume_groups import VolumeGroup
from ..utils import remove_None


class LogicalVolumesType(BlockDevicesType):
    """Metaclass for `LogicalVolumes`."""

    def bind(cls, origin, handler, handlers, *, name=None):
        # LogicalVolumes is just a wrapper over BlockDevices. So the
        # `BlockDevices` handler is binded instead of an empty handler.
        handler = handlers.get("BlockDevices")
        return super(LogicalVolumesType, cls).bind(origin, handler, handlers)

    async def create(
            cls, volume_group: VolumeGroup, name: str, size: int,
            *, uuid: str = None, tags: Iterable[str] = None):
        """
        Create a logical volume on the volume group.

        :param volume_group: Volume group to create the logical volume on.
        :type node: `VolumeGroup`
        :param name: The name for the logical volume.
        :type name: `str`
        :param size: The size of the logical volume in bytes.
        :type size: `int`
        :param uuid: UUID of the logical volume.
        :type uuid: `str`
        :param tags: List of tags to add to the logical volume.
        :type tags: sequence of `str`
        """
        if not isinstance(volume_group, VolumeGroup):
            raise TypeError(
                'volume_group must be a VolumeGroup, not %s' % (
                    type(volume_group).__name__))

        params = {
            'system_id': volume_group.node.system_id,
            'id': volume_group.id,
        }
        if not name:
            raise ValueError("name must be provided.")
        if not size or size < 0:
            raise ValueError("size must be provided and greater than zero.")

        params.update(remove_None({
            'name': name,
            'size': size,
            'uuid': uuid,
        }))
        data = await volume_group._handler.create_logical_volume(**params)
        # Create logical volume doesn't return a full block device object.
        # Load the logical volume using the block device endpoint, ensures that
        # all the data present to access the fields.
        bd_handler = getattr(cls._origin, "BlockDevice")._handler
        volume = cls._object(await bd_handler.read(
            system_id=data['system_id'], id=data['id']))
        if tags:
            volume.tags = tags
            await volume.save()
        return volume


class LogicalVolumes(BlockDevices, metaclass=LogicalVolumesType):
    """The set of logical volumes on a volume group."""


class LogicalVolumeType(BlockDeviceTypeMeta):
    """Metaclass for `LogicalVolume`."""

    def bind(cls, origin, handler, handlers, *, name=None):
        # LogicalVolume is just a wrapper over BlockDevice. So the
        # `BlockDevice` handler is binded instead of an empty handler.
        handler = handlers.get("BlockDevice")
        return super(LogicalVolumeType, cls).bind(origin, handler, handlers)


class LogicalVolume(BlockDevice, metaclass=LogicalVolumeType):
    """A logical volume on a volume group."""

    def __repr__(self):
        return super(BlockDevice, self).__repr__(
            name="LogicalVolume",
            fields={"name", })
