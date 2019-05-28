"""Objects for nodes."""

__all__ = [
    "Node",
    "Nodes",
]

from collections import Sequence
import typing

from . import (
    check,
    Object,
    ObjectField,
    ObjectFieldRelated,
    ObjectFieldRelatedSet,
    ObjectSet,
    ObjectType,
    to,
)
from ..enum import (
    NodeType,
    PowerState,
)


def normalize_hostname(hostname):
    """Strips the FQDN from the hostname, since hostname is unique in MAAS."""
    if hostname:
        return hostname.split('.', 1)[0]
    return hostname


def map_tag_name_to_dict(instance, value):
    """Convert a tag name into a dictionary for Tag."""
    return {
        'name': value,
        '__incomplete__': True
    }


class NodesType(ObjectType):
    """Metaclass for `Nodes`."""

    async def read(cls, *, hostnames: typing.Sequence[str] = None):
        """List nodes.

        :param hostnames: Sequence of hostnames to only return.
        :type hostnames: sequence of `str`
        """
        params = {}
        if hostnames:
            params["hostname"] = [
                normalize_hostname(hostname)
                for hostname in hostnames
            ]
        data = await cls._handler.read(**params)
        return cls(map(cls._object, data))


class Nodes(ObjectSet, metaclass=NodesType):
    """The set of nodes stored in MAAS."""


class NodeTypeMeta(ObjectType):
    """Metaclass for `Node`."""

    async def read(cls, system_id):
        data = await cls._handler.read(system_id=system_id)
        return cls(data)


class Node(Object, metaclass=NodeTypeMeta):
    """A node stored in MAAS."""

    domain = ObjectFieldRelated("domain", "Domain")
    fqdn = ObjectField.Checked(
        "fqdn", check(str), readonly=True)
    hostname = ObjectField.Checked(
        "hostname", check(str), check(str))
    interfaces = ObjectFieldRelatedSet("interface_set", "Interfaces")
    ip_addresses = ObjectField.Checked(  # List[str]
        "ip_addresses", check(Sequence), readonly=True)
    node_type = ObjectField.Checked(
        "node_type", to(NodeType), readonly=True)
    owner = ObjectFieldRelated("owner", "User")
    power_state = ObjectField.Checked(
        "power_state", to(PowerState), readonly=True)
    power_type = ObjectField.Checked("power_type", check(str))
    pool = ObjectFieldRelated("pool", "ResourcePool", use_data_setter=True)
    system_id = ObjectField.Checked(
        "system_id", check(str), readonly=True, pk=True)
    tags = ObjectFieldRelatedSet(
        "tag_names", "Tags", reverse=None, map_func=map_tag_name_to_dict)
    zone = ObjectFieldRelated("zone", "Zone")

    def __repr__(self):
        return super(Node, self).__repr__(
            fields={"system_id", "hostname"})

    def as_machine(self):
        """Convert to a `Machine` object.

        `node_type` must be `NodeType.MACHINE`.
        """
        if self.node_type != NodeType.MACHINE:
            raise ValueError(
                'Cannot convert to `Machine`, node_type is not a machine.')
        return self._origin.Machine(self._data)

    def as_device(self):
        """Convert to a `Device` object.

        `node_type` must be `NodeType.DEVICE`.
        """
        if self.node_type != NodeType.DEVICE:
            raise ValueError(
                'Cannot convert to `Device`, node_type is not a device.')
        return self._origin.Device(self._data)

    def as_rack_controller(self):
        """Convert to a `RackController` object.

        `node_type` must be `NodeType.RACK_CONTROLLER` or
        `NodeType.REGION_AND_RACK_CONTROLLER`.
        """
        if self.node_type not in [
                NodeType.RACK_CONTROLLER, NodeType.REGION_AND_RACK_CONTROLLER]:
            raise ValueError(
                'Cannot convert to `RackController`, node_type is not a '
                'rack controller.')
        return self._origin.RackController(self._data)

    def as_region_controller(self):
        """Convert to a `RegionController` object.

        `node_type` must be `NodeType.REGION_CONTROLLER` or
        `NodeType.REGION_AND_RACK_CONTROLLER`.
        """
        if self.node_type not in [
                NodeType.REGION_CONTROLLER,
                NodeType.REGION_AND_RACK_CONTROLLER]:
            raise ValueError(
                'Cannot convert to `RegionController`, node_type is not a '
                'region controller.')
        return self._origin.RegionController(self._data)

    async def get_power_parameters(self):
        """Get the power paramters for this node."""
        data = await self._handler.power_parameters(system_id=self.system_id)
        return data

    async def set_power(
            self, power_type: str,
            power_parameters: typing.Mapping[str, typing.Any] = {}):
        """Set the power type and power parameters for this node."""
        data = await self._handler.update(
            system_id=self.system_id, power_type=power_type,
            power_parameters=power_parameters)
        self.power_type = data['power_type']

    async def save(self):
        # the resource pool uses the name in the API, not the id. The field is
        # defined with use_data_setter=True, so the value in self._changed_data
        # is the full data dict, not just the id.
        if 'pool' in self._changed_data:
            self._changed_data['pool'] = self._changed_data['pool']['name']
        return await super().save()

    async def delete(self):
        """Deletes the node from MAAS."""
        await self._handler.delete(system_id=self.system_id)
