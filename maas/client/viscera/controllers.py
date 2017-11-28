"""Objects for region and rack controllers."""

__all__ = [
    "RackController",
    "RackControllers",
    "RegionController",
    "RegionControllers",
]

from . import (
    check,
    check_optional,
    ObjectField,
    to,
)
from .nodes import (
    Node,
    Nodes,
    NodesType,
    NodeTypeMeta,
)
from ..enum import PowerState


class RackControllersType(NodesType):
    """Metaclass for `RackControllers`."""


class RackControllers(Nodes, metaclass=RackControllersType):
    """The set of rack-controllers stored in MAAS."""


class RackControllerType(NodeTypeMeta):
    """Metaclass for `RackController`."""


class RackController(Node, metaclass=RackControllerType):
    """A rack-controller stored in MAAS."""

    architecture = ObjectField.Checked(
        "architecture", check_optional(str), check_optional(str))
    cpus = ObjectField.Checked(
        "cpu_count", check(int), check(int))
    distro_series = ObjectField.Checked(
        "distro_series", check(str), check(str))
    memory = ObjectField.Checked(
        "memory", check(int), check(int))
    osystem = ObjectField.Checked(
        "osystem", check(str), readonly=True)
    power_state = ObjectField.Checked(
        "power_state", to(PowerState), readonly=True)

    # power_type
    # service_set
    # swap_size


class RegionControllersType(NodesType):
    """Metaclass for `RegionControllers`."""


class RegionControllers(Nodes, metaclass=RegionControllersType):
    """The set of region-controllers stored in MAAS."""


class RegionControllerType(NodeTypeMeta):
    """Metaclass for `RegionController`."""


class RegionController(Node, metaclass=RegionControllerType):
    """A region-controller stored in MAAS."""

    architecture = ObjectField.Checked(
        "architecture", check_optional(str), check_optional(str))
    cpus = ObjectField.Checked(
        "cpu_count", check(int), check(int))
    distro_series = ObjectField.Checked(
        "distro_series", check(str), check(str))
    memory = ObjectField.Checked(
        "memory", check(int), check(int))
    osystem = ObjectField.Checked(
        "osystem", check(str), readonly=True)
    power_state = ObjectField.Checked(
        "power_state", to(PowerState), readonly=True)

    # power_type
    # service_set
    # swap_size
