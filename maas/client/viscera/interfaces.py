"""Objects for interfaces."""

__all__ = [
    "Interface",
    "Interfaces",
]

from typing import Sequence, Union

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
from .nodes import Node
from .vlans import Vlan
from ..enum import InterfaceType
from ..utils.diff import calculate_dict_diff


def gen_parents(parents):
    """Generate the parents to send to the handler."""
    for idx, parent in enumerate(parents):
        if isinstance(parent, Interface):
            parent = parent.id
        elif isinstance(parent, int):
            pass
        else:
            raise TypeError(
                'parent[%d] must be Interface or int, not %s' % (
                    idx, type(parent).__class__))
        yield parent


def get_parent(parent):
    """Get the parent to send to the handler."""
    if isinstance(parent, Interface):
        return parent.id
    elif isinstance(parent, int):
        return parent
    else:
        raise TypeError(
            "parent must be Interface or int, not %s" % (
                type(parent).__class__))


class InterfaceTypeMeta(ObjectType):
    """Metaclass for `Interface`."""

    async def read(cls, node, id):
        """Get `Interface` by `id`."""
        if isinstance(node, str):
            system_id = node
        elif isinstance(node, Node):
            system_id = node.system_id
        else:
            raise TypeError(
                "node must be a Node or str, not %s"
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


class Interface(Object, metaclass=InterfaceTypeMeta):
    """A interface on a machine."""

    node = ObjectFieldRelated(
        "system_id", "Node", readonly=True, pk=0)
    id = ObjectField.Checked(
        "id", check(int), readonly=True, pk=1)
    type = ObjectField.Checked(
        "type", to(InterfaceType), readonly=True)
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
    vlan = ObjectFieldRelated(
        "vlan", "Vlan", reverse=None, use_data_setter=True)

    # links
    # discovered

    def __repr__(self):
        return super(Interface, self).__repr__(
            fields={"name", "mac_address", "type"})

    async def save(self):
        """Save this interface."""
        if set(self.tags) != set(self._orig_data['tags']):
            self._changed_data['tags'] = ','.join(self.tags)
        self._changed_data.update(
            calculate_dict_diff(self._orig_data['params'], self.params))
        if 'vlan' in self._changed_data and self._changed_data['vlan']:
            # Update uses the ID of the VLAN, not the VLAN object.
            self._changed_data['vlan'] = self._changed_data['vlan']['id']
            if (self._orig_data['vlan'] and
                    'id' in self._orig_data['vlan'] and
                    self._changed_data['vlan'] == (
                        self._orig_data['vlan']['id'])):
                # VLAN didn't really change, the object was just set to the
                # same VLAN.
                del self._changed_data['vlan']
        await super(Interface, self).save()

    async def delete(self):
        """Delete this interface."""
        await self._handler.delete(
            system_id=self.node.system_id, id=self.id)


class InterfacesType(ObjectType):
    """Metaclass for `Interfaces`."""

    async def read(cls, node):
        """Get list of `Interface`'s for `node`."""
        if isinstance(node, str):
            system_id = node
        elif isinstance(node, Node):
            system_id = node.system_id
        else:
            raise TypeError(
                "node must be a Node or str, not %s"
                % type(node).__name__)
        data = await cls._handler.read(system_id=system_id)
        return cls(
            cls._object(
                item, local_data={"node_system_id": system_id})
            for item in data)

    async def create(
            cls, node: Union[Node, str],
            interface_type: InterfaceType=InterfaceType.PHYSICAL, *,
            name: str=None, mac_address: str=None, tags: Sequence[str]=None,
            vlan: Union[Vlan, int]=None, parent: Union[Interface, int]=None,
            parents: Sequence[Union[Interface, int]]=None, mtu: int=None,
            accept_ra: bool=None, autoconf: bool=None,
            bond_mode: str=None, bond_miimon: int=None,
            bond_downdelay: int=None, bond_updelay: int=None,
            bond_lacp_rate: str=None, bond_xmit_hash_policy: str=None,
            bridge_stp: bool=None, bridge_fd: int=None):
        """
        Create a `Interface` in MAAS.

        :param node: Node to create the interface on.
        :type node: `Node` or `str`
        :param interface_type: Type of interface to create (optional).
        :type interface_type: `InterfaceType`
        :param name: The name for the interface (optional).
        :type name: `str`
        :param tags: List of tags to add to the machine.
        :type tags: sequence of `str`
        :param mtu: The MTU for the interface (optional).
        :type mtu: `int`
        :param vlan: VLAN the interface is connected to (optional).
        :type vlan: `Vlan` or `int`
        :param accept_ra: True if the interface should accepted router
            advertisements. (optional)
        :type accept_ra: `bool`
        :param autoconf: True if the interface should auto configure.
        :type autoconf: `bool`

        Following parameters specific to physical interface.

        :param mac_address: The MAC address for the interface.
        :type mac_address: `str`

        Following parameters specific to a bond interface.

        :param parents: Parent interfaces that make up the bond.
        :type parents: sequence of `Interface` or `int`
        :param mac_address: MAC address to use for the bond (optional).
        :type mac_address: `str`
        :param bond_mode: The operating mode of the bond (optional).
        :type bond_mode: `str`
        :param bond_miimon: The link monitoring freqeuncy in
            milliseconds (optional).
        :type bond_miimon: `int`
        :param bond_downdelay: Specifies the time, in milliseconds, to wait
            before disabling a slave after a link failure has been detected
            (optional).
        :type bond_downdelay: `int`
        :param bond_updelay: Specifies the time, in milliseconds, to wait
            before enabling a slave after a link recovery has been detected.
        :type bond_updelay: `int`
        :param bond_lacp_rate: Option specifying the rate in which we'll ask
            our link partner to transmit LACPDU packets in 802.3ad
            mode (optional).
        :type bond_lacp_rate: `str`
        :param bond_xmit_hash_policy: The transmit hash policy to use for
            slave selection in balance-xor, 802.3ad, and tlb modes(optional).
        :type bond_xmit_hash_policy: `str`

        Following parameters specific to a VLAN interface.

        :param parent: Parent interface for this VLAN interface.
        :type parent: `Interface` or `int`

        Following parameters specific to a Bridge interface.

        :param parent: Parent interface for this bridge interface.
        :type parent: `Interface` or `int`
        :param mac_address: The MAC address for the interface (optional).
        :type mac_address: `str`
        :param bridge_stp: Turn spanning tree protocol on or off (optional).
        :type bridge_stp: `bool`
        :param bridge_fd: Set bridge forward delay to time seconds (optional).
        :type bridge_fd: `int`

        :returns: The created Interface.
        :rtype: `Interface`
        """
        params = {}
        if isinstance(node, str):
            params['system_id'] = node
        elif isinstance(node, Node):
            params['system_id'] = node.system_id
        else:
            raise TypeError(
                'node must be Node or str, not %s' % (
                    type(node).__name__))

        if name is not None:
            params['name'] = name
        if tags is not None:
            params['tags'] = tags
        if mtu is not None:
            params['mtu'] = mtu
        if vlan is not None:
            if isinstance(vlan, Vlan):
                params['vlan'] = vlan.id
            elif isinstance(vlan, int):
                params['vlan'] = vlan
            else:
                raise TypeError(
                    'vlan must be Vlan or int, not %s' % (
                        type(vlan).__name__))
        if accept_ra is not None:
            params['accept_ra'] = accept_ra
        if autoconf is not None:
            params['autoconf'] = autoconf

        handler = None
        if not isinstance(interface_type, InterfaceType):
            raise TypeError(
                'interface_type must be InterfaceType, not %s' % (
                    type(interface_type).__name__))
        if interface_type == InterfaceType.PHYSICAL:
            handler = cls._handler.create_physical
            if mac_address:
                params['mac_address'] = mac_address
            else:
                raise ValueError(
                    'mac_address required for physical interface')
        elif interface_type == InterfaceType.BOND:
            handler = cls._handler.create_bond
            if parent is not None:
                raise ValueError("use parents not parent for bond interface")
            if not isinstance(parents, Sequence):
                raise TypeError(
                    'parents must be a sequence, not %s' % (
                        type(parents).__name__))
            if len(parents) == 0:
                raise ValueError(
                    'at least one parent required for bond interface')
            params['parents'] = list(gen_parents(parents))
            if not name:
                raise ValueError('name is required for bond interface')
            if mac_address is not None:
                params['mac_address'] = mac_address
            if bond_mode is not None:
                params['bond_mode'] = bond_mode
            if bond_miimon is not None:
                params['bond_miimon'] = bond_miimon
            if bond_downdelay is not None:
                params['bond_downdelay'] = bond_downdelay
            if bond_updelay is not None:
                params['bond_updelay'] = bond_updelay
            if bond_lacp_rate is not None:
                params['bond_lacp_rate'] = bond_lacp_rate
            if bond_xmit_hash_policy is not None:
                params['bond_xmit_hash_policy'] = bond_xmit_hash_policy
        elif interface_type == InterfaceType.VLAN:
            handler = cls._handler.create_vlan
            if parents is not None:
                raise ValueError("use parent not parents for VLAN interface")
            if parent is None:
                raise ValueError("parent is required for VLAN interface")
            params['parent'] = get_parent(parent)
            if vlan is None:
                raise ValueError("vlan is required for VLAN interface")
        elif interface_type == InterfaceType.BRIDGE:
            handler = cls._handler.create_bridge
            if parents is not None:
                raise ValueError("use parent not parents for bridge interface")
            if parent is None:
                raise ValueError("parent is required for bridge interface")
            params['parent'] = get_parent(parent)
            if not name:
                raise ValueError('name is required for bridge interface')
            if mac_address is not None:
                params['mac_address'] = mac_address
            if bridge_stp is not None:
                params['bridge_stp'] = bridge_stp
            if bridge_fd is not None:
                params['bridge_fd'] = bridge_fd
        else:
            raise ValueError(
                "cannot create an interface of type: %s" % interface_type)

        return cls._object(await handler(**params))


class Interfaces(ObjectSet, metaclass=InterfacesType):
    """The set of interfaces on a machine."""
