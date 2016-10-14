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

    def __iter__(cls):
        return map(cls._object, cls._handler.read())

    def read(cls):
        return cls(cls)


class Files(ObjectSet, metaclass=FilesType):
    """The set of files stored in MAAS."""


class File(Object):
    """A file stored in MAAS."""

    filename = ObjectField.Checked(
        "filename", check(str), readonly=True)
