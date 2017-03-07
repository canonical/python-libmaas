"""Objects for devices."""

__all__ = [
    "Device",
    "Devices",
]

from collections import Sequence

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

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))


class Devices(ObjectSet, metaclass=DevicesType):
    """The set of devices stored in MAAS."""


class DeviceType(ObjectType):

    async def read(cls, system_id):
        data = await cls._handler.read(system_id=system_id)
        return cls(data)


class Device(Object, metaclass=DeviceType):
    """A device stored in MAAS."""

    hostname = ObjectField.Checked(
        "hostname", check(str), check(str))
    ip_addresses = ObjectField.Checked(  # List[str]
        "ip_addresses", check(Sequence), readonly=True)

    # owner
    # resource_uri

    system_id = ObjectField.Checked(
        "system_id", check(str), readonly=True)
    tags = ObjectField.Checked(  # List[str]
        "tag_names", check(Sequence), readonly=True)
    zone = zones.ZoneField(
        "zone", readonly=True)

    def __repr__(self):
        return super(Device, self).__repr__(
            fields={"system_id", "hostname"})
