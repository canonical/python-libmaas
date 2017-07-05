"""Objects for ipranges."""

__all__ = [
    "IPRanges",
    "IPRange",
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
from .subnets import Subnet
from typing import Union

TYPE = type


class IPRangesType(ObjectType):
    """Metaclass for `IPRanges`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))

    async def create(cls, *, start_ip: str, end_ip: str, type: str,
                     comment: str=None, subnet: Union[int, Subnet]=None):
        """
        Create a `IPRange` in MAAS.

        :param name: The name of the `IPRange` (optional, will be given a
        default value if not specified).
        :type name: `str`
        :param description: A description of the `IPRange` (optional).
        :type description: `str`
        :param class_type: The class type of the `IPRange` (optional).
        :type class_type: `str`
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
        "type", check(str), readonly=True)
    comment = ObjectField.Checked(
        "comment", check(str))
    subnet = ObjectFieldRelated("subnet", "Subnet", readonly=True, pk=0)

    async def delete(self):
        """Delete this IPRange."""
        await self._handler.delete(id=self.id)
