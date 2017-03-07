"""Objects for boot source selections."""

__all__ = [
    "BootSourceSelection",
    "BootSourceSelections",
]

from collections import Sequence

from . import (
    check,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
)
from .boot_sources import BootSource


class BootSourceSelectionsType(ObjectType):
    """Metaclass for `BootSourceSelections`."""

    async def create(
            cls, boot_source, os, release, *,
            arches=None, subarches=None, labels=None):
        """Create a new `BootSourceSelection`."""
        if not isinstance(boot_source, BootSource):
            raise TypeError(
                "boot_source must be a BootSource, not %s"
                % type(boot_source).__name__)
        if arches is None:
            arches = ['*']
        if subarches is None:
            subarches = ['*']
        if labels is None:
            labels = ['*']
        data = await cls._handler.create(
            boot_source_id=boot_source.id,
            os=os, release=release, arches=arches, subarches=subarches,
            labels=labels)
        return cls._object(data, {"boot_source_id": boot_source.id})

    async def read(cls, boot_source):
        """Get list of `BootSourceSelection`'s."""
        if not isinstance(boot_source, BootSource):
            raise TypeError(
                "boot_source must be a BootSource, not %s"
                % type(boot_source).__name__)
        data = await cls._handler.read(boot_source_id=boot_source.id)
        return cls(
            cls._object(item, local_data={"boot_source_id": boot_source.id})
            for item in data)


class BootSourceSelections(ObjectSet, metaclass=BootSourceSelectionsType):
    """The set of boot source selections."""


class BootSourceSelectionType(ObjectType):

    async def read(cls, boot_source, id):
        """Get `BootSourceSelection` by `id`."""
        if not isinstance(boot_source, BootSource):
            raise TypeError(
                "boot_source must be a BootSource, not %s"
                % type(boot_source).__name__)
        data = await cls._handler.read(boot_source_id=boot_source.id, id=id)
        return cls(data, {"boot_source_id": boot_source.id})


class BootSourceSelection(Object, metaclass=BootSourceSelectionType):
    """A boot source selection."""

    # Only client-side. Classes in this file place `boot_source_id` on
    # the object using `local_data`.
    boot_source_id = ObjectField.Checked(
        "boot_source_id", check(int), readonly=True)

    id = ObjectField.Checked(
        "id", check(int), readonly=True)
    os = ObjectField.Checked(
        "os", check(str), check(str))
    release = ObjectField.Checked(
        "release", check(str), check(str))
    arches = ObjectField.Checked(  # List[str]
        "arches", check(Sequence), check(Sequence))
    subarches = ObjectField.Checked(  # List[str]
        "subarches", check(Sequence), check(Sequence))
    labels = ObjectField.Checked(  # List[str]
        "labels", check(Sequence), check(Sequence))

    def __repr__(self):
        return super(BootSourceSelection, self).__repr__(
            fields={"os", "release", "arches", "subarches", "labels"})

    async def delete(self):
        """Delete boot source selection."""
        await self._handler.delete(
            boot_source_id=self.boot_source_id, id=self.id)
