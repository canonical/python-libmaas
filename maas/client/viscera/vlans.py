"""Objects for vlans."""

__all__ = [
    "Vlan",
    "Vlans",
]

from operator import attrgetter
from typing import Union

from . import (
    check,
    check_optional,
    Object,
    ObjectField,
    ObjectFieldRelated,
    ObjectSet,
    ObjectType,
)
from .controllers import RackController
from .fabrics import Fabric
from .spaces import Space


class VlanType(ObjectType):
    """Metaclass for `Vlan`."""

    async def read(cls, fabric: Union[Fabric, int], vid: int):
        """Get `Vlan` by `vid`.

        :param fabric: Fabric to get the VLAN from.
        :type fabric: `Fabric` or `int`
        :param vid: VID of VLAN.
        :type vid: `int`
        """
        if isinstance(fabric, int):
            fabric_id = fabric
        elif isinstance(fabric, Fabric):
            fabric_id = fabric.id
        else:
            raise TypeError(
                "fabric must be a Fabric or int, not %s"
                % type(fabric).__name__)
        data = await cls._handler.read(fabric_id=fabric_id, vid=vid)
        return cls(data, {"fabric_id": fabric_id})


class Vlan(Object, metaclass=VlanType):
    """A VLAN in a fabric."""

    id = ObjectField.Checked(
        "id", check(int), readonly=True)

    fabric = ObjectFieldRelated(
        "fabric_id", "Fabric", readonly=True, pk=0)
    vid = ObjectField.Checked(
        "vid", check(int), check(int), pk=1)

    name = ObjectField.Checked(
        "name", check_optional(str), check_optional(str))
    mtu = ObjectField.Checked(
        "mtu", check(int), check(int))
    space = ObjectFieldRelated("space", "Space")

    relay_vlan = ObjectFieldRelated("relay_vlan", "Vlan")
    dhcp_on = ObjectField.Checked(
        "dhcp_on", check(bool), check(bool))
    primary_rack = ObjectFieldRelated("primary_rack", "RackController")
    secondary_rack = ObjectFieldRelated("secondary_rack", "RackController")

    external_dhcp = ObjectField.Checked(
        "external_dhcp", check_optional(str), readonly=True)

    # space

    def __repr__(self):
        return super(Vlan, self).__repr__(
            fields={"name", "vid"})

    async def delete(self):
        """Delete this VLAN."""
        # Since the VID can be changed for the VLAN, we always use the vid
        # from the original data. That way if the user changes the vid the
        # delete still works, until the VLAN has been saved.
        await self._handler.delete(
            fabric_id=self.fabric.id, vid=self._orig_data['vid'])


class VlansType(ObjectType):
    """Metaclass for `Vlans`."""

    async def read(cls, fabric: Union[Fabric, int]):
        """Get list of `Vlan`'s for `fabric`.

        :param fabric: Fabric to get all VLAN's for.
        :type fabric: `Fabric` or `int`
        """
        if isinstance(fabric, int):
            fabric_id = fabric
        elif isinstance(fabric, Fabric):
            fabric_id = fabric.id
        else:
            raise TypeError(
                "fabric must be a Fabric or int, not %s"
                % type(fabric).__name__)
        data = await cls._handler.read(fabric_id=fabric_id)
        return cls(
            cls._object(
                item, local_data={"fabric_id": fabric_id})
            for item in data)

    async def create(
            cls, fabric: Union[Fabric, int], vid: int, *,
            name: str=None, description: str=None, mtu: int=None,
            relay_vlan: Union[Vlan, int]=None, dhcp_on: bool=False,
            primary_rack: Union[RackController, str]=None,
            secondary_rack: Union[RackController, str]=None,
            space: Union[Space, int]=None):
        """
        Create a `Vlan` in MAAS.

        :param fabric: Fabric to create the VLAN on.
        :type fabric: `Fabric` or `int`
        :param vid: VID for the VLAN.
        :type vid: `int`
        :param name: The name of the VLAN (optional).
        :type name: `str`
        :param description: A description of the VLAN (optional).
        :type description: `str`
        :param mtu: The MTU for VLAN (optional, default of 1500 will be used).
        :type mtu: `int`
        :param relay_vlan: VLAN to relay this VLAN through.
        :type relay_vlan: `Vlan` or `int`
        :param dhcp_on: True turns the DHCP on, false keeps the DHCP off. True
            requires that `primary_rack` is also set.
        :type dhcp_on: `bool`
        :param primary_rack: Primary rack controller to run the DCHP
            service on.
        :type primary_rack: `RackController` or `int`
        :parma secondary_rack: Secondary rack controller to run the DHCP
            service on. This will enable HA operation of the DHCP service.
        :type secondary_rack: `RackController` or `int`
        :returns: The created VLAN.
        :rtype: `Vlan`
        """
        params = {}
        if isinstance(fabric, int):
            params['fabric_id'] = fabric
        elif isinstance(fabric, Fabric):
            params['fabric_id'] = fabric.id
        else:
            raise TypeError(
                "fabric must be Fabric or int, not %s" % (
                    type(fabric).__class__))
        params['vid'] = vid
        if name is not None:
            params['name'] = name
        if description is not None:
            params['description'] = description
        if mtu is not None:
            params['mtu'] = mtu
        if relay_vlan is not None:
            if isinstance(relay_vlan, int):
                params['relay_vlan'] = relay_vlan
            elif isinstance(relay_vlan, Vlan):
                params['relay_vlan'] = relay_vlan.id
            else:
                raise TypeError(
                    "relay_vlan must be Vlan or int, not %s" % (
                        type(relay_vlan).__class__))
        params['dhcp_on'] = dhcp_on
        if primary_rack is not None:
            if isinstance(primary_rack, str):
                params['primary_rack'] = primary_rack
            elif isinstance(primary_rack, RackController):
                params['primary_rack'] = primary_rack.system_id
            else:
                raise TypeError(
                    "primary_rack must be RackController or str, not %s" % (
                        type(primary_rack).__class__))
        if secondary_rack is not None:
            if isinstance(secondary_rack, str):
                params['secondary_rack'] = secondary_rack
            elif isinstance(secondary_rack, RackController):
                params['secondary_rack'] = secondary_rack.system_id
            else:
                raise TypeError(
                    "secondary_rack must be RackController or str, not %s" % (
                        type(secondary_rack).__class__))
        if space is not None:
            if isinstance(space, int):
                params['space'] = space
            elif isinstance(space, Space):
                params['space'] = space.id
            else:
                raise TypeError(
                    "space must be Space or int, not %s" % (
                        type(space).__class__))
        return cls._object(await cls._handler.create(**params))


class Vlans(ObjectSet, metaclass=VlansType):
    """The set of VLAN's on a fabric."""

    def get_default(self):
        """Return the default VLAN from the set."""
        length = len(self)
        if length == 0:
            return None
        elif length == 1:
            return self[0]
        else:
            return sorted(self, key=attrgetter('id'))[0]
