"""Objects for fabrics."""

__all__ = [
    "Fabrics",
    "Fabric",
]

from . import (
    check,
    check_optional,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
)


class FabricsType(ObjectType):
    """Metaclass for `Fabrics`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))

    async def create(cls, name: str, description: str, class_type: str):
        """
        Create a `Fabric` in MAAS.

        :param name: The name of the `Fabric`.
        :type name: `str`
        :param description: A description of the `Fabric`.
        :type description: `str`
        :param class_type: The class type of the `Fabric`.
        :type class_type: `str`
        :returns: The created Fabric
        :rtype: `Fabric`
        """
        return cls._object(await cls._handler.create(
            name=name,
            description=description,
            class_type=class_type,
        ))



class Fabrics(ObjectSet, metaclass=FabricsType):
    """The set of Fabrics stored in MAAS."""


class FabricType(ObjectType):

    async def read(cls, id: int):
        """Get a `Fabric` by its `id`."""
        data = await cls._handler.read(id=id)
        return cls(data)

    async def delete(cls, id: int):
        """Delete a `Fabric`"""
        await cls._handler.delete(id=id)

    async def get_default_fabric(cls):
        """
        Get the 'default' Fabric for the MAAS.
        """
        data = await cls._handler.read(id=0)
        return cls(data)


class Fabric(Object, metaclass=FabricType):
    """A Fabric."""
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
    class_type = ObjectField.Checked(
        "class_type", check_optional(str), readonly=True
    )
