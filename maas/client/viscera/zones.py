"""Objects for zones."""

__all__ = [
    "Zone",
    "ZoneField",
    "Zones",
]

from . import (
    check,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
)


class ZonesType(ObjectType):
    """Metaclass for `Zones`."""

    def __iter__(cls):
        return map(cls._object, cls._handler.read())

    def read(cls):
        return cls(cls)


class ZoneNotFound(Exception):
    """Zone was not found."""


class Zones(ObjectSet, metaclass=ZonesType):
    """The set of zones stored in MAAS."""


class ZoneType(ObjectType):

    def read(cls, name):
        data = cls._handler.read(name=name)
        return cls(data)


class Zone(Object, metaclass=ZoneType):
    """A zone stored in MAAS."""

    name = ObjectField.Checked(
        "name", check(str), check(str))
    description = ObjectField.Checked(
        "description", check(str), check(str))

    def __repr__(self):
        return super(Zone, self).__repr__(
            fields={"name", "description"})


class ZoneField(ObjectField):
    """An object field for a `Zone`."""

    def datum_to_value(self, instance, datum):
        return instance._origin.Zone(datum)
