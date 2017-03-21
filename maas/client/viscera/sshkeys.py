"""Objects for SSH Keys."""

__all__ = [
    "SSHKeys",
    "SSHKey",
]

from . import (
    check,
    check_optional,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
)


class SSHKeysType(ObjectType):
    """Metaclass for `SSHKeys`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))

    async def create(cls, key: str):
        """
        Create an SSH key in MAAS with the content in `key`.

        :param key: The content of the SSH key
        :type key: `str`
        :returns: The created SSH key
        :rtype: `SSHKey`
        """
        return cls._object(await cls._handler.create(key=key))


class SSHKeys(ObjectSet, metaclass=SSHKeysType):
    """The set of SSH keys stored in MAAS."""


class SSHKeyType(ObjectType):

    async def read(cls, id: int):
        """Get an `SSHKey` by its `id`."""
        data = await cls._handler.read(id=id)
        return cls(data)


class SSHKey(Object, metaclass=SSHKeyType):
    """An SSH key."""
    id = ObjectField.Checked(
        "id", check(int), readonly=True
    )
    key = ObjectField.Checked(
        "key", check(str), readonly=True
    )
    keysource = ObjectField.Checked(
        "keysource", check_optional(str), readonly=True,
    )
