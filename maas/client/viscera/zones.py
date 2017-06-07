"""Objects for zones."""

__all__ = [
    "Zone",
    "Zones",
]

from . import (
    check,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
)


class ZonesType(ObjectType):
    """Metaclass for `Zones`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))

    async def create(cls, name: str, description: str=None):
        """
        Create a `Zone` in MAAS.

        :param name: The name of the `Zone`.
        :type name: `str`
        :param description: A description of the `Zone`.
        :type description: `str`
        :returns: The create `Zone`
        :rtype: `Zone`
        """
        params = {'name': name}
        if description is not None:
            params['description'] = description
        return cls._object(await cls._handler.create(**params))


class Zones(ObjectSet, metaclass=ZonesType):
    """The set of zones stored in MAAS."""


class ZoneType(ObjectType):

    async def read(cls, name):
        data = await cls._handler.read(name=name)
        return cls(data)


class Zone(Object, metaclass=ZoneType):
    """A zone stored in MAAS."""

    id = ObjectField.Checked(
        "id", check(int), readonly=True)

    name = ObjectField.Checked(
        "name", check(str), check(str), pk=True)
    description = ObjectField.Checked(
        "description", check(str), check(str))

    def __repr__(self):
        return super(Zone, self).__repr__(
            fields={"name", "description"})

    async def delete(self):
        """
        Deletes the `Zone` from MAAS.
        """
        return await self._handler.delete(name=self.name)
