"""Objects for devices."""

__all__ = [
    "Device",
    "Devices",
]

from typing import List

from . import (
    check,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
    zones,
)


class DevicesType(ObjectType):
    """Metaclass for `Devices`."""

    def __iter__(cls):
        return map(cls._object, cls._handler.read())

    def read(cls):
        return cls(cls)


class DeviceNotFound(Exception):
    """Device was not found."""


class Devices(ObjectSet, metaclass=DevicesType):
    """The set of devices stored in MAAS."""


class DeviceType(ObjectType):

    def read(cls, system_id):
        data = cls._handler.read(system_id=system_id)
        return cls(data)


class Device(Object, metaclass=DeviceType):
    """A device stored in MAAS."""

    hostname = ObjectField.Checked(
        "hostname", check(str), check(str))
    ip_addresses = ObjectField.Checked(
        "ip_addresses", check(List[str]), readonly=True)

    # owner
    # resource_uri

    system_id = ObjectField.Checked(
        "system_id", check(str), readonly=True)
    tags = ObjectField.Checked(
        "tag_names", check(List[str]), readonly=True)
    zone = zones.ZoneField(
        "zone", readonly=True)

    def __repr__(self):
        return super(Device, self).__repr__(
            fields={"system_id", "hostname"})
