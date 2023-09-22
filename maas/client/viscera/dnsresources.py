"""Objects for dnsresources."""

__all__ = ["DNSResource", "DNSResources"]

from . import (
    check,
    check_optional,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
    ObjectFieldRelatedSet,
)


class DNSResourceType(ObjectType):
    """Metaclass for `DNSResources`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))


class DNSResources(ObjectSet, metaclass=DNSResourceType):
    """The set of dnsresources stored in MAAS."""


class DNSResourceType(ObjectType):
    async def read(cls, id):
        data = await cls._handler.read(id=id)
        return cls(data)


class DNSResource(Object, metaclass=DNSResourceType):
    """A dnsresource stored in MAAS."""

    id = ObjectField.Checked("id", check(int), readonly=True, pk=True)
    address_ttl = ObjectField.Checked(
        "address_ttl", check_optional(int), check_optional(int)
    )
    fqdn = ObjectField.Checked("fqdn", check(str), check(str))
    ip_addresses = ObjectFieldRelatedSet("ip_addresses", "IPAddresses")
    resource_records = ObjectFieldRelatedSet("resource_records", "DNSResourceRecords")

    def __repr__(self):
        return super(DNSResource, self).__repr__(
            fields={"address_ttl", "fqdn", "ip_addresses", "resource_records"}
        )
