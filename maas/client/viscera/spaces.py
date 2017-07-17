"""Objects for spaces."""

__all__ = [
    "Space",
    "Spaces",
]

from . import (
    check,
    check_optional,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
)


class SpacesType(ObjectType):
    """Metaclass for `spaces`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))


class Spaces(ObjectSet, metaclass=SpacesType):
    """The set of spaces on a fabric."""


class SpaceType(ObjectType):
    """Metaclass for `space`."""

    async def read(cls, id: int):
        """Get a `Space` by its `id`."""
        data = await cls._handler.read(id=id)
        return cls(data)


class Space(Object, metaclass=SpaceType):
    """A space in a fabric."""

    id = ObjectField.Checked(
        "id", check(int), readonly=True)
    subnets = ObjectField.Checked(
        "subnets", check(list), check(list))
    name = ObjectField.Checked(
        "name", check_optional(str), check_optional(str))
