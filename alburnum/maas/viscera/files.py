"""Objects for files."""

__all__ = [
    "File",
    "Files",
]

from . import (
    check,
    Disabled,
    Object,
    ObjectSet,
    ObjectType,
    ObjectTypedField,
)


class FilesType(ObjectType):
    """Metaclass for `Files`."""

    def __iter__(cls):
        return map(cls._object, cls._handler.list())

    def read(cls):
        return list(cls)

    list = Disabled("list", "read")  # API is malformed in MAAS server.


class Files(ObjectSet, metaclass=FilesType):
    """The set of files stored in MAAS."""


class File(Object):
    """A file stored in MAAS."""

    filename = ObjectTypedField(
        "filename", check(str), readonly=True)
