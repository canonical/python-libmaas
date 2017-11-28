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

    async def create(
            cls, name, *, comment=None, definition=None, kernel_opts=None):
        params = {
            "name": name,
        }
        if comment is not None:
            params["comment"] = comment
        if definition is not None:
            params["definition"] = definition
        if kernel_opts is not None:
            params["kernel_opts"] = kernel_opts
        data = await cls._handler.create(**params)
        return cls._object(data)

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))


class Tags(ObjectSet, metaclass=TagsType):
    """The set of tags."""


class TagType(ObjectType):

    async def read(cls, name):
        data = await cls._handler.read(name=name)
        return cls(data)


class Tag(Object, metaclass=TagType):
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

    async def delete(self):
        """
        Deletes the `Tag` from MAAS.
        """
        return await self._handler.delete(name=self.name)
