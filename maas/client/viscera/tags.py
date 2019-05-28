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
from .nodes import Node


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

    @classmethod
    def Managed(cls, manager, field, items):
        """Create a custom `Tags` that is managed by a related `Node.`

        :param manager: The manager of the `ObjectSet`. This is the `Object`
            that manages this set of objects.
        :param field: The field on the `manager` that created this managed
            `ObjectSet`.
        :param items: The items in the `ObjectSet`.
        """
        if not isinstance(manager, Node):
            raise TypeError(
                "manager must be instance of Node, not %s",
                type(manager).__name__)

        async def add(self, tag: Tag):
            """Add `tag` to node.

            :param tag: Tag to add to the node.
            :type tag: `Tag`.
            """
            if not isinstance(tag, Tag):
                raise TypeError(
                    "tag must be instance of Tag, not %s", type(tag).__name__)
            await tag._handler.update_nodes(
                name=tag.name, add=manager.system_id)
            if tag.name not in manager._data[field.name]:
                manager._data[field.name] += [tag.name]

        async def remove(self, tag: Tag):
            """Remove `tag` from node.

            :param tag: Tag to from the node.
            :type tag: `Tag`.
            """
            if not isinstance(tag, Tag):
                raise TypeError(
                    "tag must be instance of Tag, not %s", type(tag).__name__)
            await tag._handler.update_nodes(
                name=tag.name, remove=manager.system_id)
            manager._data[field.name] = [
                tag_name
                for tag_name in manager._data[field.name]
                if tag_name != tag.name
            ]

        attrs = {
            "add": add,
            "remove": remove,
        }
        cls = type(
            "%s.Managed#%s" % (
                cls.__name__, manager.__class__.__name__), (cls,), attrs)
        return cls(items)


class TagType(ObjectType):

    async def read(cls, name):
        data = await cls._handler.read(name=name)
        return cls(data)


class Tag(Object, metaclass=TagType):
    """A tag."""

    name = ObjectField.Checked(
        "name", check(str), readonly=True, pk=True)
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
