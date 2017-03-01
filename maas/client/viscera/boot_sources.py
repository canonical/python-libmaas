"""Objects for boot sources."""

__all__ = [
    "BootSource",
    "BootSources",
]

from . import (
    check,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
    parse_timestamp,
)
from ..utils import coalesce


class BootSourcesType(ObjectType):
    """Metaclass for `BootSources`."""

    async def create(cls, url, *, keyring_filename=None, keyring_data=None):
        """Create a new `BootSource`.

        :param url: The URL for the boot source.
        :param keyring_filename: The path to the keyring file on the server.
        :param keyring_data: The GPG keyring data, binary. as a file-like
            object. For example: an open file handle in binary mode, or an
            instance of `io.BytesIO`.
        """
        data = await cls._handler.create(
            url=url, keyring_filename=coalesce(keyring_filename, ""),
            keyring_data=coalesce(keyring_data, ""))
        return cls._object(data)

    async def read(cls):
        """Get list of `BootSource`'s."""
        data = await cls._handler.read()
        return cls(map(cls._object, data))


class BootSources(ObjectSet, metaclass=BootSourcesType):
    """The set of boot sources."""


class BootSourceType(ObjectType):

    async def read(cls, id):
        """Get `BootSource` by `id`."""
        data = await cls._handler.read(id=id)
        return cls(data)


class BootSource(Object, metaclass=BootSourceType):
    """A boot source."""

    id = ObjectField.Checked(
        "id", check(int), readonly=True)
    url = ObjectField.Checked(
        "url", check(str), check(str))
    keyring_filename = ObjectField.Checked(
        "keyring_filename", check(str), check(str), default="")
    keyring_data = ObjectField.Checked(
        "keyring_data", check(str), check(str), default="")
    created = ObjectField.Checked(
        "created", parse_timestamp, readonly=True)
    updated = ObjectField.Checked(
        "updated", parse_timestamp, readonly=True)

    def __repr__(self):
        return super(BootSource, self).__repr__(
            fields={"url", "keyring_filename", "keyring_data"})

    async def delete(self):
        """Delete boot source."""
        await self._handler.delete(id=self.id)
