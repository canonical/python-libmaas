"""Objects for subnets."""

__all__ = [
    "Subnet",
    "Subnets",
]

from . import (
    check,
    check_optional,
    Object,
    ObjectField,
    ObjectFieldRelated,
    ObjectSet,
    ObjectType,
)


class SubnetsType(ObjectType):
    """Metaclass for `subnets`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))


class Subnets(ObjectSet, metaclass=SubnetsType):
    """The set of subnets on a fabric."""


class SubnetType(ObjectType):
    """Metaclass for `subnet`."""

    async def read(cls, id: int):
        """Get a `Subnet` by its `id`."""
        data = await cls._handler.read(id=id)
        return cls(data)


class Subnet(Object, metaclass=SubnetType):
    """A subnet in a fabric."""

    id = ObjectField.Checked(
        "id", check(int), readonly=True)
    name = ObjectField.Checked(
        "name", check_optional(str), check_optional(str))
    description = ObjectField.Checked(
        "description", check_optional(str), check_optional(str))
    vlan = ObjectFieldRelated(
        "vlan_id", "VLAN", readonly=True)
    space = ObjectField.Checked(
        "space", check(str), check(str))
    cidr = ObjectField.Checked(
        "cidr", check(str), check(str))
    gateway_ip = ObjectField.Checked(
        "gateway_ip", check(str), check(str))
    rdns_mode = ObjectField.Checked(
        "rdns_mode", check(int), check(int))
    allow_proxy = ObjectField.Checked(
        "allow_proxy", check(bool), check(bool))
    dns_servers = ObjectField.Checked(
        "dns_servers", check(list), check(list))
