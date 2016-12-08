"""Objects for files."""

__all__ = [
    "File",
    "Files",
]

from . import (
    check,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
)


class FilesType(ObjectType):
    """Metaclass for `Files`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))


class Files(ObjectSet, metaclass=FilesType):
    """The set of files stored in MAAS."""


class File(Object):
    """A file stored in MAAS."""

    filename = ObjectField.Checked(
        "filename", check(str), readonly=True)
