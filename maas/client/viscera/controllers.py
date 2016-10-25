"""Objects for region and rack controllers."""

__all__ = [
    "RackController",
    "RackControllers",
]

import base64
from typing import (
    List,
    Union,
)

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

    def __iter__(cls):
        return map(cls._object, cls._handler.read())

    def read(cls):
        return cls(cls)


class RackControllerNotFound(Exception):
    """Rack-controller was not found."""


class RackControllers(ObjectSet, metaclass=RackControllersType):
    """The set of rack-controllers stored in MAAS."""


class RackControllerType(ObjectType):

    def read(cls, system_id):
        data = cls._handler.read(system_id=system_id)
        return cls(data)


class RackController(Object, metaclass=RackControllerType):
    """A rack-controller stored in MAAS."""

    architecture = ObjectField.Checked(
        "architecture", check_optional(str), check_optional(str))
    boot_disk = ObjectField.Checked(
        "boot_disk", check_optional(str), check_optional(str))
    cpus = ObjectField.Checked(
        "cpu_count", check(int), check(int))
    disable_ipv4 = ObjectField.Checked(
        "disable_ipv4", check(bool), check(bool))
    distro_series = ObjectField.Checked(
        "distro_series", check(str), check(str))
    hostname = ObjectField.Checked(
        "hostname", check(str), check(str))
    hwe_kernel = ObjectField.Checked(
        "hwe_kernel", check_optional(str), check_optional(str))
    ip_addresses = ObjectField.Checked(
        "ip_addresses", check(List[str]), readonly=True)
    memory = ObjectField.Checked(
        "memory", check(int), check(int))
    min_hwe_kernel = ObjectField.Checked(
        "min_hwe_kernel", check_optional(str), check_optional(str))

    # blockdevice_set
    # interface_set
    # macaddress_set
    # netboot
    # osystem
    # owner
    # physicalblockdevice_set

    # TODO: Use an enum here.
    power_state = ObjectField.Checked(
        "power_state", check(str), readonly=True)

    # power_type
    # pxe_mac
    # resource_uri
    # routers
    # status
    # storage

    status = ObjectField.Checked(
        "status", check(int), readonly=True)
    status_action = ObjectField.Checked(
        "substatus_action", check_optional(str), readonly=True)
    status_message = ObjectField.Checked(
        "substatus_message", check_optional(str), readonly=True)
    status_name = ObjectField.Checked(
        "substatus_name", check(str), readonly=True)

    # swap_size

    system_id = ObjectField.Checked(
        "system_id", check(str), readonly=True)
    tags = ObjectField.Checked(
        "tag_names", check(List[str]), readonly=True)

    # virtualblockdevice_set

    zone = zones.ZoneField(
        "zone", readonly=True)

    # def __repr__(self):
    #     return super(RackController, self).__repr__(
    #         fields={"system_id", "hostname"})
