"""Objects for devices."""

__all__ = [
    "Device",
    "Devices",
]

import typing

from .nodes import (
    Node,
    Nodes,
    NodesType,
    NodeTypeMeta,
)
from .zones import Zone


class DevicesType(NodesType):
    """Metaclass for `Devices`."""

    async def create(
            cls,
            mac_addresses: typing.Sequence[str],
            hostname: str = None,
            domain: typing.Union[int, str] = None,
            zone: typing.Union[str, Zone] = None):
        """Create a new device.

        :param mac_addresses: The MAC address(es) of the device (required).
        :type mac_addresses: sequence of `str`
        :param hostname: The hostname for the device (optional).
        :type hostname: `str`
        :param domain: The domain for the device (optional).
        :type domain: `int` or `str`
        :param zone: The zone for the device (optional).
        :type zone: `Zone` or `str`

        """
        params = {
            'mac_addresses': mac_addresses,
        }
        if hostname is not None:
            params['hostname'] = hostname
        if domain is not None:
            params['domain'] = domain
        if zone is not None:
            if isinstance(zone, Zone):
                params["zone"] = zone.name
            elif isinstance(zone, str):
                params["zone"] = zone
            else:
                raise TypeError(
                    "zone must be a str or Zone, not %s" % type(zone).__name__)
        return cls._object(await cls._handler.create(**params))


class Devices(Nodes, metaclass=DevicesType):
    """The set of devices stored in MAAS."""


class DeviceType(NodeTypeMeta):
    """Metaclass for `Device`."""


class Device(Node, metaclass=DeviceType):
    """A device stored in MAAS."""
