"""Objects for boot resources."""

__all__ = [
    "BootResource",
    "BootResources",
]

from typing import Mapping

from . import (
    check,
    check_optional,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
    parse_timestamp,
)


class BootResourceMappingType(ObjectType):
    """Metaclass for `BootResourceSet` and `BootResourceFile`."""

    def mapping(cls, data):
        """Convert `data` mapping to mapping for class."""
        if not isinstance(data, Mapping):
            raise TypeError(
                "data must be a mapping, not %s"
                % type(data).__name__)
        return {
            key: cls(value)
            for key, value in data.items()
        }


class BootResourceFile(Object, metaclass=BootResourceMappingType):
    """A boot resource file."""

    filename = ObjectField.Checked(
        "filename", check(str), readonly=True)
    filetype = ObjectField.Checked(
        "filetype", check(str), readonly=True)
    size = ObjectField.Checked(
        "size", check(int), readonly=True)
    sha256 = ObjectField.Checked(
        "sha256", check(str), readonly=True)
    complete = ObjectField.Checked(
        "complete", check(bool), readonly=True)


class BootResourceSet(Object, metaclass=BootResourceMappingType):
    """A boot resource set."""

    version = ObjectField.Checked(
        "version", check(str), readonly=True)
    size = ObjectField.Checked(
        "size", check(int), readonly=True)
    label = ObjectField.Checked(
        "label", check(str), readonly=True)
    complete = ObjectField.Checked(
        "complete", check(bool), readonly=True)
    files = ObjectField.Checked(
        "files", BootResourceFile.mapping, default={})


class BootResourcesType(ObjectType):
    """Metaclass for `BootResources`."""

    def __iter__(cls):
        return map(cls._object, cls._handler.read())


class BootResources(ObjectSet, metaclass=BootResourcesType):
    """The set of boot resources."""

    @classmethod
    def read(cls):
        """Get list of `BootResource`'s."""
        return cls(cls)


class BootResourceType(ObjectType):

    def read(cls, id):
        """Get `BootResource` by `id`."""
        data = cls._handler.read(id=id)
        return cls(data)


class BootResource(Object, metaclass=BootResourceType):
    """A boot resource."""

    id = ObjectField.Checked(
        "id", check(int), readonly=True)
    type = ObjectField.Checked(
        "type", check(str), check(str))
    name = ObjectField.Checked(
        "name", check(str), check(str))
    architecture = ObjectField.Checked(
        "architecture", check(str), check(str))
    subarches = ObjectField.Checked(
        "subarches", check_optional(str), check_optional(str), default=None)
    sets = ObjectField.Checked(
        "sets", BootResourceSet.mapping, default={})

    def __repr__(self):
        return super(BootResource, self).__repr__(
            fields={"type", "name", "architecture"})

    def delete(self):
        """Delete boot resource."""
        self._handler.delete(id=self.id)
