"""Objects for tags."""

__all__ = [
    "Tag",
    "Tags",
]

from . import (
    check,
    check_optional,
    Disabled,
    Object,
    ObjectSet,
    ObjectType,
    ObjectTypedField,
)


class TagsType(ObjectType):
    """Metaclass for `Tags`."""

    def __iter__(cls):
        return map(cls._object, cls._handler.list())

    def create(cls, name, *, comment="", definition="", kernel_opts=""):
        data = cls._handler.new(
            name=name, comment=comment, definition=definition,
            kernel_opts=kernel_opts)
        return cls._object(data)

    new = Disabled("new", "create")  # API is malformed in MAAS server.

    def read(cls):
        return cls(cls)

    list = Disabled("list", "read")  # API is malformed in MAAS server.


class Tags(ObjectSet, metaclass=TagsType):
    """The set of tags."""


class Tag(Object):
    """A tag."""

    name = ObjectTypedField(
        "name", check(str), readonly=True)
    comment = ObjectTypedField(
        "comment", check(str), check(str), default="")
    definition = ObjectTypedField(
        "definition", check(str), check(str), default="")
    kernel_opts = ObjectTypedField(
        "kernel_opts", check_optional(str), check_optional(str),
        default=None)
