"""Objects for volume groups."""

__all__ = [
    "VolumeGroup",
    "VolumeGroups",
]

from typing import Iterable, Sequence, Union

from . import (
    check,
    Object,
    ObjectField,
    ObjectFieldRelated,
    ObjectFieldRelatedSet,
    ObjectSet,
    ObjectType,
)
from .nodes import Node
from .block_devices import BlockDevice
from .partitions import Partition
from ..enum import BlockDeviceType


class VolumeGroupDevicesType(ObjectType):
    """Metaclass for `VolumeGroupDevices`."""

    def get_object(cls, datum):
        device_type = datum.get('type')
        if device_type in [
                BlockDeviceType.PHYSICAL.value, BlockDeviceType.VIRTUAL.value]:
            return cls._origin.BlockDevice(datum)
        elif device_type == 'partition':
            return cls._origin.Partition(datum)
        else:
            raise ValueError('Unknown devices type: %s' % device_type)


class VolumeGroupDevices(ObjectSet, metaclass=VolumeGroupDevicesType):
    """Devices that make up a `VolumeGroup`."""


class VolumeGroupDevicesField(ObjectFieldRelatedSet):
    """Field for `devices` in `VolumeGroup`."""

    def __init__(self, name):
        """Create a `VolumeGroupDevicesField`.

        :param name: The name of the field. This is the name that's used to
            store the datum in the MAAS-side data dictionary.
        """
        super(ObjectFieldRelatedSet, self).__init__(
            name, default=[], readonly=True)

    def datum_to_value(self, instance, datum):
        """Convert a given MAAS-side datum to a Python-side value.

        :param instance: The `Object` instance on which this field is
            currently operating. This method should treat it as read-only, for
            example to perform validation with regards to other fields.
        :param datum: The MAAS-side datum to validate and convert into a
            Python-side value.
        :return: A set of `cls` from the given datum.
        """
        if datum is None:
            return []
        if not isinstance(datum, Sequence):
            raise TypeError(
                "datum must be a sequence, not %s" % type(datum).__name__)
        # Get the class from the bound origin.
        bound = getattr(instance._origin, "VolumeGroupDevices")
        return bound(
            instance, self,
            (
                bound.get_object(item)
                for item in datum
            ))


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


class VolumeGroup(Object, metaclass=VolumeGroupType):
    """A volume group on a machine."""

    node = ObjectFieldRelated(
        "system_id", "Node", readonly=True, pk=0)
    id = ObjectField.Checked(
        "id", check(int), readonly=True, pk=1)
    name = ObjectField.Checked(
        "name", check(str), check(str), alt_pk=1)
    size = ObjectField.Checked(
        "size", check(int), check(int))

    available_size = ObjectField.Checked(
        "available_size", check(int), readonly=True)
    used_size = ObjectField.Checked(
        "used_size", check(int), readonly=True)

    devices = VolumeGroupDevicesField("devices")
    logical_volumes = ObjectFieldRelatedSet(
        "logical_volumes", "BlockDevices", reverse=None)

    def __repr__(self):
        return super(VolumeGroup, self).__repr__(
            fields={"name", "size"})

    async def save(self):
        """Save this volume group."""
        old_tags = list(self._orig_data['tags'])
        new_tags = list(self.tags)
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
            cls, node: Union[Node, str],
            devices: Iterable[Union[BlockDevice, Partition]],
            *, uuid: str=None):
        """
        Create a volume group on a Node.

        :param node: Node to create the interface on.
        :type node: `Node` or `str`
        :param devices: Mixed list of block devices or partitions to create
            the volume group from.
        :type devices: iterable of mixed type of `BlockDevice` or `Partition`
        :param uuid: The UUID for the volume group (optional).
        :type uuid: `str`
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
        """Return mapping of name of volume group to `VolumeGroup`."""
        return {
            vg.name: vg
            for vg in self
        }

    def get_by_name(self, name):
        """Return a `VolumeGroup` by its name."""
        return self.by_name[name]
