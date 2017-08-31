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
    ObjectFieldRelatedSet,
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


def map_nic_name_to_dict(instance, value):
    """Convert a name of interface into a dictionary.

    `parents` and `children` just hold a list of interface names. This is need
    so instead they can return a `ObjectSet`.

    '__incomplete__' is set so the object knows that the data passed is
    incomplete data.
    """
    return {
        'system_id': instance._data['system_id'],
        'name': value,
        '__incomplete__': True
    }


class Interface(Object, metaclass=InterfaceType):
    """A interface on a machine."""

    node = ObjectFieldRelated(
        "system_id", "Node", readonly=True, pk=0)
    id = ObjectField.Checked(
        "id", check(int), readonly=True, pk=1)
    type = ObjectField.Checked(
        "type", check(str), readonly=True)
    name = ObjectField.Checked(
        "name", check(str), check(str), alt_pk=1)
    mac_address = ObjectField.Checked(
        "mac_address", check(str), check(str))
    enabled = ObjectField.Checked(
        "enabled", check(bool), check(bool))
    effective_mtu = ObjectField.Checked(
        "effective_mtu", check(int), readonly=True)
    tags = ObjectField.Checked(
        "tags", check(list), check(list))
    params = ObjectField.Checked(
        "params", check(dict), check(dict))
    parents = ObjectFieldRelatedSet(
        "parents", "Interfaces", reverse=None,
        map_func=map_nic_name_to_dict)
    children = ObjectFieldRelatedSet(
        "children", "Interfaces", reverse=None,
        map_func=map_nic_name_to_dict)
    vlan = ObjectFieldRelated("vlan", "Vlan", reverse=None)

    # links
    # discovered

    def __repr__(self):
        return super(Interface, self).__repr__(
            fields={"name", "mac_address"})
