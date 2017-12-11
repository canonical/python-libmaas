"""Base object for all filesystem group objects."""

__all__ = [
    "FilesystemGroup",
]

from typing import Sequence

from . import (
    check,
    Object,
    ObjectField,
    ObjectFieldRelated,
    ObjectFieldRelatedSet,
    ObjectSet,
    undefined,
)
from ..enum import BlockDeviceType


def get_device_object(origin, datum):
    device_type = datum.get('type')
    if device_type in [
            BlockDeviceType.PHYSICAL.value, BlockDeviceType.VIRTUAL.value]:
        return origin.BlockDevice(datum)
    elif device_type == 'partition':
        return origin.Partition(datum)
    else:
        raise ValueError('Unknown devices type: %s' % device_type)


class FilesystemGroupDevices(ObjectSet):
    """Devices that make up a `FilesystemGroup`."""


class DevicesField(ObjectFieldRelatedSet):
    """Field for `FilesystemGroupDevices`."""

    def __init__(self, name):
        """Create a `DevicesField`.

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
        bound = getattr(instance._origin, "FilesystemGroupDevices")
        return bound((
            get_device_object(instance._origin, item)
            for item in datum
            ))


class DeviceField(ObjectFieldRelated):
    """Field that returns either `BlockDevice` or `Partition`."""

    def __init__(self, name, readonly=False):
        """Create a `DevicesField`.

        :param name: The name of the field. This is the name that's used to
            store the datum in the MAAS-side data dictionary.
        """
        super(ObjectFieldRelated, self).__init__(
            name, default=undefined, readonly=readonly)

    def datum_to_value(self, instance, datum):
        """Convert a given MAAS-side datum to a Python-side value.

        :param instance: The `Object` instance on which this field is
            currently operating. This method should treat it as read-only, for
            example to perform validation with regards to other fields.
        :param datum: The MAAS-side datum to validate and convert into a
            Python-side value.
        :return: A set of `cls` from the given datum.
        """
        return get_device_object(instance._origin, datum)


class FilesystemGroup(Object):
    """A filesystem group on a machine.

    Used by `CacheSet`, `Bcache`, `Raid`, and `VolumeGroup`. Never use
    directly.
    """

    node = ObjectFieldRelated(
        "system_id", "Node", readonly=True, pk=0)
    id = ObjectField.Checked(
        "id", check(int), readonly=True, pk=1)
    name = ObjectField.Checked(
        "name", check(str), check(str), alt_pk=1)
