"""Objects for subnets."""

__all__ = [
    "Subnets",
    "Subnet",
]

from . import (
    check,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
)


class SubnetsType(ObjectType):
    """Metaclass for `Subnets`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))

    async def create(cls, *, name: str=None,
                     description: str=None):
        """
        Create a `Subnet` in MAAS.

        :param name: The name of the `Subnet` (optional, will be given a
        default value if not specified).
        :type name: `str`
        :param description: A description of the `Subnet` (optional).
        :type description: `str`
        :returns: The created Subnet
        :rtype: `Subnet`
        """
        params = {}
        if name is not None:
            params["name"] = name
        if description is not None:
            params["description"] = description
        return cls._object(await cls._handler.create(**params))


class Subnets(ObjectSet, metaclass=SubnetsType):
    """The set of Subnets stored in MAAS."""


class SubnetType(ObjectType):

    async def read(cls, id: int):
        """Get a `Subnet` by its `id`."""
        data = await cls._handler.read(id=id)
        return cls(data)


class Subnet(Object, metaclass=SubnetType):
    """A Subnet."""
    id = ObjectField.Checked(
        "id", check(int), readonly=True
    )
    name = ObjectField.Checked(
        "name", check(str), readonly=True
    )
    """
    description is allowed in the create call and displayed in the UI
    but never returned by the API
    """
