"""Objects for vlans."""

__all__ = [
    "VLAN",
    "VLANs",
]

from . import (
    check,
    check_optional,
    Object,
    ObjectField,
    ObjectFieldRelated,
    ObjectSet,
    ObjectType,
)


class VLANsType(ObjectType):
    """Metaclass for `VLANs`."""


class VLANs(ObjectSet, metaclass=VLANsType):
    """The set of VLANs on a fabric."""


class VLANType(ObjectType):
    """Metaclass for `VLAN`."""


class VLAN(Object, metaclass=VLANType):
    """A VLAN in a fabric."""

    id = ObjectField.Checked(
        "id", check(int), readonly=True)
    name = ObjectField.Checked(
        "name", check_optional(str), check_optional(str))
    fabric = ObjectFieldRelated(
        "fabric_id", "Fabric", readonly=True)
    vid = ObjectField.Checked(
        "vid", check(int), check(int))
    mtu = ObjectField.Checked(
        "mtu", check(int), check(int))
    space = ObjectFieldRelated(
        "space", "Space")

    relay_vlan = ObjectFieldRelated(
        "relay_vlan", "VLAN")
    dhcp_on = ObjectField.Checked(
        "dhcp_on", check(bool), check(bool))
    # primary_rack
    # secondary_rack

    external_dhcp = ObjectField.Checked(
        "external_dhcp", check_optional(str), readonly=True)

    def __repr__(self):
        return super(VLAN, self).__repr__(
            fields={"name", "vid"})
