"""Objects for subnets."""

__all__ = [
    "Subnets",
    "Subnet",
]

from typing import (
    Sequence,
    Union,
)

from . import (
    check,
    check_optional,
    Object,
    ObjectField,
    ObjectFieldRelated,
    ObjectSet,
    ObjectType,
    to,
)
from .vlans import Vlan
from ..enum import RDNSMode


class SubnetsType(ObjectType):
    """Metaclass for `Subnets`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))

    async def create(
            cls, cidr: str, vlan: Union[Vlan, int]=None, *,
            name: str=None, description: str=None,
            gateway_ip: str=None, rdns_mode: RDNSMode=None,
            dns_servers: Union[Sequence[str], str]=None,
            managed: bool=None):
        """
        Create a `Subnet` in MAAS.

        :param cidr: The cidr of the `Subnet` (required).
        :type cidr: `str`
        :param vlan: The VLAN of the `Subnet` (required).
        :type vlan: `Vlan`
        :param name: The name of the `Subnet` (optional, will be given a
        default value if not specified).
        :type name: `str`
        :param description: A description of the `Subnet` (optional).
        :type description: `str`
        :param gateway_ip: The gateway IP address for the `Subnet` (optional).
        :type gateway_ip: `str`
        :param rdns_mode: The reverse DNS mode for the `Subnet` (optional).
        :type rdns_mode: `RDNSMode`
        :param managed: Whether the `Subnet` is managed by MAAS (optional).
        :type managed: `bool`
        :returns: The created Subnet
        :rtype: `Subnet`
        """
        params = {
            "cidr": cidr
        }

        if isinstance(vlan, int):
            params["vlan"] = vlan
        elif isinstance(vlan, Vlan):
            params["vlan"] = vlan.id
        else:
            raise TypeError(
                "vlan must be Vlan or int, not %s" % (
                    type(vlan).__class__))
        if name is not None:
            params["name"] = name
        if description is not None:
            params["description"] = description
        if gateway_ip is not None:
            params["gateway_ip"] = gateway_ip
        if rdns_mode is not None:
            params["rdns_mode"] = rdns_mode
        if isinstance(dns_servers, Sequence):
            if len(dns_servers) > 0:
                params["dns_servers"] = ",".join(dns_servers)
        elif dns_servers is not None:
            params["dns_servers"] = dns_servers
        if managed is not None:
            params["managed"] = managed
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
        "cidr", check(str), readonly=True)
    name = ObjectField.Checked(
        "name", check(str), readonly=True)

    # description is allowed in the create call and displayed in the UI
    # but never returned by the API

    vlan = ObjectFieldRelated("vlan", "Vlan")

    # This should point to the space object and not just the string.
    space = ObjectField.Checked("space", check(str))

    active_discovery = ObjectField.Checked("active_discovery", check(bool))
    allow_proxy = ObjectField.Checked("allow_proxy", check(bool))
    managed = ObjectField.Checked("managed", check(bool))
    gateway_ip = ObjectField.Checked("gateway_ip", check_optional(str))
    rdns_mode = ObjectField.Checked("rdns_mode", to(RDNSMode))
    dns_servers = ObjectField.Checked("dns_servers", check(list))

    def __repr__(self):
        return super(Subnet, self).__repr__(
            fields={"cidr", "name", "vlan"})

    async def delete(self):
        """Delete this Subnet."""
        await self._handler.delete(id=self.id)
