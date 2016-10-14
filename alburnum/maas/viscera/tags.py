"""Objects for tags."""

__all__ = [
    "Tag",
    "Tags",
]

from . import (
    check,
    check_optional,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
)


class TagsType(ObjectType):
    """Metaclass for `Tags`."""

    def __iter__(cls):
        return map(cls._object, cls._handler.read())

    def create(cls, name, *, comment="", definition="", kernel_opts=""):
        data = cls._handler.new(
            name=name, comment=comment, definition=definition,
            kernel_opts=kernel_opts)
        return cls._object(data)

    def read(cls):
        return cls(cls)


class Tags(ObjectSet, metaclass=TagsType):
    """The set of tags."""


class Tag(Object):
    """A tag."""

    name = ObjectField.Checked(
        "name", check(str), readonly=True)
    comment = ObjectField.Checked(
        "comment", check(str), check(str), default="")
    definition = ObjectField.Checked(
        "definition", check(str), check(str), default="")
    kernel_opts = ObjectField.Checked(
        "kernel_opts", check_optional(str), check_optional(str),
        default=None)
