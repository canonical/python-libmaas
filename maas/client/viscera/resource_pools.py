"""Objects for resource pools."""

__all__ = [
    "ResourcePool",
    "ResourcePools",
]

from . import (
    check,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
)


class ResourcePoolsType(ObjectType):
    """Metaclass for `ResorucePools`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))

    async def create(cls, name: str, description: str = None):
        """
        Create a `ResourcePool` in MAAS.

        :param name: The name of the `ResourcePool`.
        :type name: `str`
        :param description: A description of the `ResourcePool`.
        :type description: `str`
        :returns: The created `ResourcePool`
        :rtype: `ResourcePool`
        """
        params = {'name': name}
        if description is not None:
            params['description'] = description
        return cls._object(await cls._handler.create(**params))


class ResourcePools(ObjectSet, metaclass=ResourcePoolsType):
    """The set of resource pools stored in MAAS."""


class ResourcePoolType(ObjectType):

    async def read(cls, id):
        data = await cls._handler.read(id=id)
        return cls(data)


class ResourcePool(Object, metaclass=ResourcePoolType):
    """A resource pool stored in MAAS."""

    id = ObjectField.Checked(
        "id", check(int), readonly=True, pk=True)

    name = ObjectField.Checked("name", check(str), check(str))
    description = ObjectField.Checked(
        "description", check(str), check(str))

    def __repr__(self):
        return super(ResourcePool, self).__repr__(
            fields={"name", "description"})

    async def delete(self):
        """
        Deletes the `ResourcePool` from MAAS.
        """
        return await self._handler.delete(id=self.id)
