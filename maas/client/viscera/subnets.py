"""Objects for subnets."""

__all__ = [
    "Subnets",
    "Subnet",
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
    """Metaclass for `Subnets`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))

    async def create(cls, *, cidr: str, name: str=None,
                     description: str=None):
        """
        Create a `Subnet` in MAAS.

        :param cidr: The cidr of the `Subnet` (required).
        :type cidr: `str`
        :param name: The name of the `Subnet` (optional, will be given a
        default value if not specified).
        :type name: `str`
        :param description: A description of the `Subnet` (optional).
        :type description: `str`
        :returns: The created Subnet
        :rtype: `Subnet`
        """
        params = {
            "cidr": cidr
        }
        if name is not None:
            params["name"] = name
        if description is not None:
            params["description"] = description
        return cls._object(await cls._handler.create(**params))


class Subnets(ObjectSet, metaclass=SubnetsType):
    """The set of Subnets stored in MAAS."""


class SubnetType(ObjectType):
    """Metaclass for `Subnet`"""
    async def read(cls):
        """Get a `Subnet`."""
        data = await cls._handler.read()
        return cls(data)


class Subnet(Object, metaclass=SubnetType):
    """A Subnet."""
    cidr = ObjectField.Checked(
        "cidr", check(str), readonly=True
    )
    name = ObjectField.Checked(
        "name", check(str), readonly=True
    )
    """
    description is allowed in the create call and displayed in the UI
    but never returned by the API
    """
    vlan = ObjectFieldRelated(
        "vlan", "Vlan")
    fabric = ObjectFieldRelated(
        "fabric", "Fabric")
    name = ObjectField.Checked(
        "vid", check_optional(int)
    )
    space = ObjectFieldRelated(
        "space", "Space")
    gateway_ip = ObjectField.Checked(
        "gateway_ip", check(str),
    )
    rdns_mode = ObjectField.Checked(
        "rdns_mode", check(int),
    )
    dns_servers = ObjectField.Checked(
        "dns_servers", check(str),
    )
