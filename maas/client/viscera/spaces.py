"""Objects for spaces."""

__all__ = [
    "Spaces",
    "Space",
]

from . import (
    check,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
)


class SpacesType(ObjectType):
    """Metaclass for `Spaces`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))

    async def create(
            cls, *, name: str=None, description: str=None):
        """
        Create a `Space` in MAAS.

        :param name: The name of the `Space` (optional, will be given a
        default value if not specified).
        :type name: `str`
        :param description: A description of the `Space` (optional).
        :type description: `str`
        :returns: The created Space
        :rtype: `Space`
        """
        params = {}
        if name is not None:
            params["name"] = name
        if description is not None:
            params["description"] = description
        return cls._object(await cls._handler.create(**params))


class Spaces(ObjectSet, metaclass=SpacesType):
    """The set of Spaces stored in MAAS."""


class SpaceType(ObjectType):

    _default_space_id = 0

    async def get_default(cls):
        """Get the 'default' Space for the MAAS."""
        data = await cls._handler.read(id=cls._default_space_id)
        return cls(data)

    async def read(cls, id: int):
        """Get a `Space` by its `id`."""
        data = await cls._handler.read(id=id)
        return cls(data)


class Space(Object, metaclass=SpaceType):
    """A Space."""

    id = ObjectField.Checked("id", check(int), readonly=True, pk=True)
    name = ObjectField.Checked("name", check(str), readonly=True)

    # description is allowed in the create call and displayed in the UI
    # but never returned by the API.

    async def delete(self):
        """Delete this Space."""
        if self.id == self._origin.Space._default_space_id:
            raise DeleteDefaultSpace("Cannot delete default space.")
        await self._handler.delete(id=self.id)


class DeleteDefaultSpace(Exception):
    """Default space cannot be deleted."""
