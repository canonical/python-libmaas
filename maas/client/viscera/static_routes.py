"""Objects for static_routes."""

__all__ = [
    "StaticRoutes",
    "StaticRoute",
]

from . import (
    check,
    Object,
    ObjectField,
    ObjectFieldRelated,
    ObjectSet,
    ObjectType,
)
from .subnets import Subnet
from typing import Union


class StaticRoutesType(ObjectType):
    """Metaclass for `StaticRoutes`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))

    async def create(cls, destination: Union[int, Subnet],
                     source: Union[int, Subnet], gateway_ip: str, metric: int):
        """
        Create a `StaticRoute` in MAAS.

        :param name: The name of the `StaticRoute` (optional, will be given a
        default value if not specified).
        :type name: `str`
        :param description: A description of the `StaticRoute` (optional).
        :type description: `str`
        :param class_type: The class type of the `StaticRoute` (optional).
        :type class_type: `str`
        :returns: The created StaticRoute
        :rtype: `StaticRoute`
        """
        params = {
            "gateway_ip": gateway_ip,
            "metric": metric,
        }
        if isinstance(source, Subnet):
            params["source"] = source.id
        elif isinstance(source, int):
            params["source"] = source
        if isinstance(destination, Subnet):
            params["destination"] = destination.id
        elif isinstance(destination, int):
            params["destination"] = destination
        return cls._object(await cls._handler.create(**params))


class StaticRoutes(ObjectSet, metaclass=StaticRoutesType):
    """The set of StaticRoutes stored in MAAS."""


class StaticRouteType(ObjectType):
    """Metaclass for `StaticRoute`."""
    async def read(cls, id: int):
        """Get a `StaticRoute` by its `id`."""
        data = await cls._handler.read(id=id)
        return cls(data)


class StaticRoute(Object, metaclass=StaticRouteType):
    """A StaticRoute."""

    id = ObjectField.Checked(
        "id", check(int), readonly=True, pk=True)
    destination = ObjectFieldRelated("destination", "Subnet")
    source = ObjectFieldRelated("source", "Subnet")
    gateway_ip = ObjectField.Checked(
        "gateway_ip", check(str),
    )
    metric = ObjectField.Checked(
        "metric", check(int),
    )

    async def delete(self):
        """Delete this StaticRoute."""
        await self._handler.delete(id=self.id)
