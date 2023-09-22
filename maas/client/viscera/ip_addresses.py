"""Objects for ipaddresses."""

__all__ = ["IPAddress", "IPAddresses"]

from . import (
    check,
    parse_timestamp,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
    ObjectFieldRelatedSet,
    ObjectFieldRelated,
    OriginObjectRef,
)


class IPAddressType(ObjectType):
    """Metaclass for `IPAddresses`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))


class IPAddresses(ObjectSet, metaclass=IPAddressType):
    """The set of ipaddresses stored in MAAS."""

    _object = OriginObjectRef(name="IPAddress")


class IPAddress(Object):
    """An ipaddress stored in MAAS."""

    alloc_type = ObjectField.Checked("alloc_type", check(int), check(int))
    alloc_type_name = ObjectField.Checked("alloc_type_name", check(str), check(str))
    created = ObjectField.Checked("created", parse_timestamp, readonly=True)
    ip = ObjectField.Checked("ip", check(str))
    owner = ObjectFieldRelated("owner", "User")
    interface_set = ObjectFieldRelatedSet("interface_set", "Interfaces")
    subnet = ObjectFieldRelated("subnet", "Subnet", readonly=True, default=None)

    def __repr__(self):
        return super(IPAddress, self).__repr__(
            fields={
                "alloc_type",
                "alloc_type_name",
                "created",
                "ip",
                "owner",
                "interface_set",
                "subnet",
            }
        )
