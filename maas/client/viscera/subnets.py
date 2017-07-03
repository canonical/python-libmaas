"""Objects for subnets."""

__all__ = [
    "Subnets",
    "Subnet",
]

from typing import Union

from . import (
    check,
    Object,
    ObjectField,
    ObjectFieldRelated,
    ObjectSet,
    ObjectType,
)
from .fabrics import Fabric
from .vlans import Vlan


class SubnetsType(ObjectType):
    """Metaclass for `Subnets`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))

    async def create(cls, *, cidr: str, name: str=None, description: str=None,
                     fabric: Union[Fabric, int]=None,
                     vlan: Union[Vlan, int]=None,
                     vid: int=None, gateway_ip: str=None, rdns_mode: str=None,
                     dns_servers: str=None):
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
        if isinstance(fabric, int):
            params["fabric"] = fabric
        elif isinstance(fabric, Fabric):
            params["fabric"] = fabric.id
        elif fabric is not None:
            raise TypeError(
                "fabric must be Fabric or int, not %s" % (
                    type(fabric).__class__))
        if isinstance(vlan, int):
            params["vlan"] = vlan
        elif isinstance(vlan, Vlan):
            params["vlan"] = vlan.id
        elif vlan is not None:
            raise TypeError(
                "vlan must be Vlan or int, not %s" % (
                    type(vlan).__class__))

        if vid is not None:
            assert(vlan is None)
            params["vid"] = vid
        if gateway_ip is not None:
            params["gateway_ip"] = gateway_ip
        if rdns_mode is not None:
            params["rdns_mode"] = rdns_mode
        if dns_servers is not None:
            params["dns_servers"] = dns_servers
        if name is not None:
            params["name"] = name
        if description is not None:
            params["description"] = description
        return cls._object(await cls._handler.create(**params))


class Subnets(ObjectSet, metaclass=SubnetsType):
    """The set of Subnets stored in MAAS."""


class SubnetType(ObjectType):
    """Metaclass for `Subnet`"""
    async def read(cls, id: int):
        """Get a `Subnet` by its `id`."""
        data = await cls._handler.read(id=id)
        return cls(data)


class Subnet(Object, metaclass=SubnetType):
    """A Subnet."""
    id = ObjectField.Checked(
        "id", check(int), readonly=True, pk=True)
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
    vlan = ObjectFieldRelated("vlan", "Vlan")
    space = ObjectField.Checked(
        "space", check(str),
    )
    active_discovery = ObjectField.Checked(
        "active_discovery", check(bool),
    )
    allow_proxy = ObjectField.Checked(
        "allow_proxy", check(bool),
    )
    managed = ObjectField.Checked(
        "managed", check(bool),
    )
    gateway_ip = ObjectField.Checked(
        "gateway_ip", check(str),
    )
    rdns_mode = ObjectField.Checked(
        "rdns_mode", check(int),
    )
    dns_servers = ObjectField.Checked(
        "dns_servers", check(list),
    )

    async def delete(self):
        """Delete this Subnet."""
        await self._handler.delete(id=self.id)
