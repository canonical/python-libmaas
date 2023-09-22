"""Objects for dnsresourcerecords."""

__all__ = ["DNSResourceRecord", "DNSResourceRecords"]

from . import check, check_optional, Object, ObjectField, ObjectSet, ObjectType


class DNSResourceRecordType(ObjectType):
    """Metaclass for `DNSResourceRecords`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))


class DNSResourceRecords(ObjectSet, metaclass=DNSResourceRecordType):
    """The set of dnsresourcerecords stored in MAAS."""


class DNSResourceRecordType(ObjectType):
    async def read(cls, id):
        data = await cls._handler.read(id=id)
        return cls(data)


class DNSResourceRecord(Object, metaclass=DNSResourceRecordType):
    """A dnsresourcerecord stored in MAAS."""

    id = ObjectField.Checked("id", check(int), readonly=True, pk=True)
    ttl = ObjectField.Checked("ttl", check_optional(int), check_optional(int))
    rrtype = ObjectField.Checked("rrtype", check(str), check(str))
    rrdata = ObjectField.Checked("rrdata", check(str), check(str))
    fqdn = ObjectField.Checked("fqdn", check(str), check(str))

    def __repr__(self):
        return super(DNSResourceRecord, self).__repr__(
            fields={"ttl", "rrtype", "rrdata", "fqdn"}
        )
