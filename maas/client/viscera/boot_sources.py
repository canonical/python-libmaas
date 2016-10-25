"""Objects for boot sources."""

__all__ = [
    "BootSource",
    "BootSources",
]

from . import (
    check,
    check_optional,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
    parse_timestamp,
)


class BootSourcesType(ObjectType):
    """Metaclass for `BootSources`."""

    def __iter__(cls):
        return map(cls._object, cls._handler.read())

    def create(cls, url, *, keyring_filename=None, keyring_data=None):
        """Create a new `BootSource`."""
        if (not url.endswith(".json") and
                keyring_filename is None and
                keyring_data is None):
            raise ValueError(
                "Either keyring_filename and keyring_data must be set when "
                "providing a signed source.")
        data = cls._handler.create(
            url=url,
            keyring_filename=(
                "" if keyring_filename is None else keyring_filename),
            keyring_data=(
                "" if keyring_data is None else keyring_data))
        return cls._object(data)


class BootSources(ObjectSet, metaclass=BootSourcesType):
    """The set of boot sources."""

    @classmethod
    def read(cls):
        """Get list of `BootSource`'s."""
        return cls(cls)


class BootSourceType(ObjectType):

    def read(cls, id):
        """Get `BootSource` by `id`."""
        data = cls._handler.read(id=id)
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

    def delete(self):
        """Delete boot source."""
        self._handler.delete(id=self.id)
