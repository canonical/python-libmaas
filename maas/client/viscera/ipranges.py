"""Objects for ipranges."""

__all__ = [
    "IPRanges",
    "IPRange",
]

from . import (
    check,
    Object,
    ObjectField,
    ObjectFieldRelated,
    ObjectSet,
    ObjectType,
    to,
)
from .subnets import Subnet
from ..enum import IPRangeType
from typing import Union

TYPE = type


class IPRangesType(ObjectType):
    """Metaclass for `IPRanges`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))

    async def create(
            cls, start_ip: str, end_ip: str, *,
            type: IPRangeType=IPRangeType.RESERVED,
            comment: str=None, subnet: Union[Subnet, int]=None):
        """
        Create a `IPRange` in MAAS.

        :param start_ip: First IP address in the range (required).
        :type start_ip: `str`
        :parma end_ip: Last IP address in the range (required).
        :type end_ip: `str`
        :param type: Type of IP address range (optional).
        :type type: `IPRangeType`
        :param comment: Reason for the IP address range (optional).
        :type comment: `str`
        :param subnet: Subnet the IP address range should be created on
            (optional). By default MAAS will calculate the correct subnet
            based on the `start_ip` and `end_ip`.
        :type subnet: `Subnet` or `int`
        :returns: The created IPRange
        :rtype: `IPRange`
        """
        params = {
            'start_ip': start_ip,
            'end_ip': end_ip,
            'type': type,
        }
        if comment is not None:
            params["comment"] = comment
        if subnet is not None:
            if isinstance(subnet, Subnet):
                params["subnet"] = subnet.id
            elif isinstance(subnet, int):
                params["subnet"] = subnet
            else:
                raise TypeError(
                    "subnet must be Subnet or int, not %s" % (
                        TYPE(subnet).__class__))
        return cls._object(await cls._handler.create(**params))


class IPRanges(ObjectSet, metaclass=IPRangesType):
    """The set of IPRanges stored in MAAS."""


class IPRangeType(ObjectType):
    """Metaclass for `IPRange`."""

    async def read(cls, id: int):
        """Get a `IPRange` by its `id`."""
        data = await cls._handler.read(id=id)
        return cls(data)


class IPRange(Object, metaclass=IPRangeType):
    """A IPRange."""

    id = ObjectField.Checked(
        "id", check(int), readonly=True, pk=True)
    start_ip = ObjectField.Checked(
        "start_ip", check(str))
    end_ip = ObjectField.Checked(
        "end_ip", check(str))
    type = ObjectField.Checked(
        "type", to(IPRangeType), readonly=True)
    comment = ObjectField.Checked(
        "comment", check(str))
    subnet = ObjectFieldRelated("subnet", "Subnet", readonly=True, pk=0)

    async def delete(self):
        """Delete this IPRange."""
        await self._handler.delete(id=self.id)
