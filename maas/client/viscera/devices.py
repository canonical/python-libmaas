"""Objects for devices."""

__all__ = [
    "Device",
    "Devices",
]

from .nodes import (
    Node,
    Nodes,
    NodesType,
    NodeTypeMeta,
)


class DevicesType(NodesType):
    """Metaclass for `Devices`."""


class Devices(Nodes, metaclass=DevicesType):
    """The set of devices stored in MAAS."""


class DeviceType(NodeTypeMeta):
    """Metaclass for `Device`."""


class Device(Node, metaclass=DeviceType):
    """A device stored in MAAS."""
