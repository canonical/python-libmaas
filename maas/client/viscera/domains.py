"""Objects for domains."""

__all__ = [
    "Domain",
    "Domains",
]

from . import (
    check,
    check_optional,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
)


class DomainType(ObjectType):
    """Metaclass for `Domains`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))

    async def create(
            cls, name: str, authoritative: bool = True, ttl: int = None):
        """
        Create a `Domain` in MAAS.

        :param name: The name of the `Domain`.
        :type name: `str`
        :param authoritative: Whether the domain is authoritative.
        :type authoritative: `bool`
        :param ttl: Optional TTL for the domain.
        :type ttl: `int`
        :returns: The created `Domain`
        :rtype: `Domain`
        """
        params = {'name': name, 'authoritative': authoritative}
        if ttl is not None:
            params['ttl'] = ttl
        return cls._object(await cls._handler.create(**params))


class Domains(ObjectSet, metaclass=DomainType):
    """The set of domains stored in MAAS."""


class DomainType(ObjectType):

    async def read(cls, id):
        data = await cls._handler.read(id=id)
        return cls(data)


class Domain(Object, metaclass=DomainType):
    """A domain stored in MAAS."""

    id = ObjectField.Checked(
        "id", check(int), readonly=True, pk=True)
    name = ObjectField.Checked("name", check(str), check(str))
    authoritative = ObjectField.Checked(
        "authoritative", check_optional(bool), check_optional(bool))
    ttl = ObjectField.Checked(
        "ttl", check_optional(int), check_optional(int))

    def __repr__(self):
        return super(Domain, self).__repr__(
            fields={"name", "authoritative", "ttl"})

    async def delete(self):
        """
        Deletes the `domain` from MAAS.
        """
        return await self._handler.delete(id=self.id)
