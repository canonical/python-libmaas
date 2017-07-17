"""Objects for interfaces."""

__all__ = [
    "Interface",
    "Interfaces",
]

from . import (
    check,
    Object,
    ObjectField,
    ObjectFieldRelated,
    ObjectSet,
    ObjectType,
)
from .machines import Machine
from .devices import Device
from .controllers import (
    RackController,
    RegionController,
)


class InterfacesType(ObjectType):
    """Metaclass for `Interfaces`."""

    async def read(cls, node):
        """Get list of `Interface`'s for `node`."""
        if isinstance(node, str):
            system_id = node
        elif isinstance(
                node, (Device, Machine, RackController, RegionController)):
            system_id = node.system_id
        else:
            raise TypeError(
                "node must be a Machine or str, not %s"
                % type(node).__name__)
        data = await cls._handler.read(system_id=system_id)
        return cls(
            cls._object(
                item, local_data={"node_system_id": system_id})
            for item in data)


class Interfaces(ObjectSet, metaclass=InterfacesType):
    """The set of interfaces on a machine."""


class InterfaceType(ObjectType):
    """Metaclass for `Interface`."""

    async def read(cls, node, id):
        """Get `Interface` by `id`."""
        if isinstance(node, str):
            system_id = node
        elif isinstance(
                node, (Device, Machine, RackController, RegionController)):
            system_id = node.system_id
        else:
            raise TypeError(
                "node must be a Machine or str, not %s"
                % type(node).__name__)
        data = await cls._handler.read(system_id=system_id, id=id)
        return cls(data, {"node_system_id": system_id})


class Interface(Object, metaclass=InterfaceType):
    """A interface on a machine."""

    id = ObjectField.Checked(
        "id", check(int), readonly=True)
    type = ObjectField.Checked(
        "type", check(str), readonly=True)
    name = ObjectField.Checked(
        "name", check(str), check(str))
    mac_address = ObjectField.Checked(
        "mac_address", check(str), check(str))
    enabled = ObjectField.Checked(
        "enabled", check(bool), check(bool))
    effective_mtu = ObjectField.Checked(
        "effective_mtu", check(int), readonly=True)

    vlan = ObjectFieldRelated("vlan", "Vlan", reverse=None)

    # parents
    # links
    # vlan
    # discovered
    # tags
    # children
    # params

    def __repr__(self):
        return super(Interface, self).__repr__(
            fields={"name", "mac_address"})
