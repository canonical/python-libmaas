"""Objects for region and rack controllers."""

__all__ = [
    "RackController",
    "RackControllers",
    "RegionController",
    "RegionControllers",
]

from collections import Sequence

from . import (
    check,
    check_optional,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
    zones,
)


class RackControllersType(ObjectType):
    """Metaclass for `RackControllers`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))


class RackControllers(ObjectSet, metaclass=RackControllersType):
    """The set of rack-controllers stored in MAAS."""


class RackControllerType(ObjectType):

    async def read(cls, system_id):
        data = await cls._handler.read(system_id=system_id)
        return cls(data)


class RackController(Object, metaclass=RackControllerType):
    """A rack-controller stored in MAAS."""

    architecture = ObjectField.Checked(
        "architecture", check_optional(str), check_optional(str))
    cpus = ObjectField.Checked(
        "cpu_count", check(int), check(int))
    distro_series = ObjectField.Checked(
        "distro_series", check(str), check(str))

    # domain

    fqdn = ObjectField.Checked(
        "fqdn", check(str), check(str))
    hostname = ObjectField.Checked(
        "hostname", check(str), check(str))

    # interface_set

    ip_addresses = ObjectField.Checked(  # List[str]
        "ip_addresses", check(Sequence), readonly=True)
    memory = ObjectField.Checked(
        "memory", check(int), check(int))

    # node_type
    # node_type_name
    # osystem

    # TODO: Use an enum here.
    power_state = ObjectField.Checked(
        "power_state", check(str), readonly=True)

    # power_type
    # service_set
    # status_action
    # swap_size

    system_id = ObjectField.Checked(
        "system_id", check(str), readonly=True)

    zone = zones.ZoneField(
        "zone", readonly=True)

    def __repr__(self):
        return super(RackController, self).__repr__(
            fields={"system_id", "hostname"})


class RegionControllersType(ObjectType):
    """Metaclass for `RegionControllers`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))


class RegionControllers(ObjectSet, metaclass=RegionControllersType):
    """The set of region-controllers stored in MAAS."""


class RegionControllerType(ObjectType):

    async def read(cls, system_id):
        data = await cls._handler.read(system_id=system_id)
        return cls(data)


class RegionController(Object, metaclass=RegionControllerType):
    """A region-controller stored in MAAS."""

    architecture = ObjectField.Checked(
        "architecture", check_optional(str), check_optional(str))
    cpus = ObjectField.Checked(
        "cpu_count", check(int), check(int))
    distro_series = ObjectField.Checked(
        "distro_series", check(str), check(str))

    # domain

    fqdn = ObjectField.Checked(
        "fqdn", check(str), check(str))
    hostname = ObjectField.Checked(
        "hostname", check(str), check(str))

    # interface_set

    ip_addresses = ObjectField.Checked(  # List[str]
        "ip_addresses", check(Sequence), readonly=True)
    memory = ObjectField.Checked(
        "memory", check(int), check(int))

    # node_type
    # node_type_name
    # osystem

    # TODO: Use an enum here.
    power_state = ObjectField.Checked(
        "power_state", check(str), readonly=True)

    # power_type
    # service_set
    # status_action
    # swap_size

    system_id = ObjectField.Checked(
        "system_id", check(str), readonly=True)

    zone = zones.ZoneField(
        "zone", readonly=True)

    def __repr__(self):
        return super(RegionController, self).__repr__(
            fields={"system_id", "hostname"})
