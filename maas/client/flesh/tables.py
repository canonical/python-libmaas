"""Tables for representing information from MAAS."""

__all__ = [
    "FilesTable",
    "NodesTable",
    "ProfilesTable",
    "TagsTable",
    "UsersTable",
]

from operator import (
    attrgetter,
    itemgetter
)

from colorclass import Color

from ..enum import (
    InterfaceType,
    NodeType,
    PowerState,
    RDNSMode,
)
from .tabular import (
    Column,
    RenderTarget,
    Table,
    DetailTable,
    NestedTableColumn,
)


class NodeTypeColumn(Column):

    nice_names = {
        NodeType.MACHINE: "Machine",
        NodeType.DEVICE: "Device",
        NodeType.RACK_CONTROLLER: "Rackd",
        NodeType.REGION_CONTROLLER: "Regiond",
        NodeType.REGION_AND_RACK_CONTROLLER: "Regiond+rackd",
    }

    def render(self, target, node_type):
        if target in (RenderTarget.pretty, RenderTarget.plain):
            node_type = self.nice_names[node_type]
        else:
            node_type = node_type.value
        return super().render(target, node_type)


class NodeArchitectureColumn(Column):

    def render(self, target, architecture):
        if target in (RenderTarget.pretty, RenderTarget.plain):
            if architecture:
                if architecture.endswith('/generic'):
                    architecture = architecture[:-8]
            else:
                architecture = "-"
        return super().render(target, architecture)


class NodeCPUsColumn(Column):

    def render(self, target, cpus):
        # `cpus` is a count of CPUs.
        if target in (RenderTarget.pretty, RenderTarget.plain):
            if cpus is None:
                cpus = "-"
            elif cpus == 0.0:
                cpus = "-"
        return super().render(target, cpus)


class NodeMemoryColumn(Column):

    def render(self, target, memory):
        # `memory` is in MB.
        if target in (RenderTarget.pretty, RenderTarget.plain):
            if memory is None:
                memory = "-"
            elif memory == 0.0:
                memory = "-"
            elif memory < 1024.0:  # <1GB
                memory = "%0.1f MB" % (memory)
            elif memory < 1048576.0:  # <1TB
                memory = "%0.1f GB" % (memory / 1024.0)
            else:
                memory = "%0.1f TB" % (memory / 1048576.0)
        return super().render(target, memory)


class NodeStatusNameColumn(Column):

    colours = {
        # "New": "",  # White.
        "Commissioning": "autoyellow",
        "Failed commissioning": "autored",
        "Missing": "red",
        "Ready": "autogreen",
        "Reserved": "autoblue",
        "Allocated": "autoblue",
        "Deploying": "autoblue",
        "Deployed": "autoblue",
        # "Retired": "",  # White.
        "Broken": "autored",
        "Failed deployment": "autored",
        "Releasing": "autoblue",
        "Releasing failed": "autored",
        "Disk erasing": "autoblue",
        "Failed disk erasing": "autored",
    }

    def render(self, target, datum):
        if target == RenderTarget.pretty:
            if datum in self.colours:
                colour = self.colours[datum]
                return Color("{%s}%s{/%s}" % (
                    colour, datum, colour))
            else:
                return datum
        else:
            return super().render(target, datum)


class NodePowerColumn(Column):

    colours = {
        PowerState.ON: "autogreen",
        # PowerState.OFF: "",  # White.
        PowerState.ERROR: "autored",
    }

    def render(self, target, data):
        if target == RenderTarget.pretty:
            if data in self.colours:
                colour = self.colours[data]
                return Color("{%s}%s{/%s}" % (
                    colour, data.value.capitalize(), colour))
            else:
                return data.value.capitalize()
        elif target == RenderTarget.plain:
            return super().render(target, data.value.capitalize())
        else:
            return super().render(target, data.value)


class NodeInterfacesColumn(Column):

    def render(self, target, data):
        count = 0
        for interface in data:
            if interface.type == InterfaceType.PHYSICAL:
                count += 1
        return super().render(target, "%d physical" % count)


class NodeOwnerColumn(Column):

    def render(self, target, data):
        if data is None:
            return super().render(target, "(none)")
        else:
            return super().render(target, data.username)


class NodeImageColumn(Column):

    def render(self, target, data):
        if data:
            return super().render(target, data)
        else:
            return super().render(target, "(none)")


class NodeZoneColumn(Column):

    def render(self, target, data):
        return super().render(target, data.name)


class NodesTable(Table):

    def __init__(self):
        super().__init__(
            Column("hostname", "Hostname"),
            NodeTypeColumn("node_type", "Type"),
        )

    def get_rows(self, target, nodes):
        data = (
            (node.hostname, node.node_type)
            for node in nodes
        )
        return sorted(data, key=itemgetter(0))


class MachinesTable(Table):

    def __init__(self):
        super().__init__(
            Column("hostname", "Hostname"),
            NodePowerColumn("power", "Power"),
            NodeStatusNameColumn("status", "Status"),
            NodeOwnerColumn("owner", "Owner"),
            NodeArchitectureColumn("architecture", "Arch"),
            NodeCPUsColumn("cpus", "#CPUs"),
            NodeMemoryColumn("memory", "RAM"),
        )

    def get_rows(self, target, machines):
        data = (
            (
                machine.hostname,
                machine.power_state,
                machine.status_name,
                machine.owner,
                machine.architecture,
                machine.cpus,
                machine.memory,
            )
            for machine in machines
        )
        return sorted(data, key=itemgetter(0))


class MachineDetail(DetailTable):

    def __init__(self, with_type=False):
        self.with_type = with_type
        columns = [
            Column("hostname", "Hostname"),
            NodeStatusNameColumn("status", "Status"),
            NodeImageColumn("image", "Image"),
            NodePowerColumn("power", "Power"),
            Column("power_type", "Power Type"),
            NodeArchitectureColumn("architecture", "Arch"),
            NodeCPUsColumn("cpus", "#CPUs"),
            NodeMemoryColumn("memory", "RAM"),
            NodeInterfacesColumn("interfaces", "Interfaces"),
            Column("ip_addresses", "IP addresses"),
            NodeZoneColumn("zone", "Zone"),
            NodeOwnerColumn("owner", "Owner"),
            Column("tags", "Tags"),
        ]
        if with_type:
            columns.insert(1, NodeTypeColumn("node_type", "Type"))
        super().__init__(*columns)

    def get_rows(self, target, machine):
        data = [
            machine.hostname,
            machine.status_name,
            machine.distro_series,
            machine.power_state,
            machine.power_type,
            machine.architecture,
            machine.cpus,
            machine.memory,
            machine.interfaces,
            [
                link.ip_address
                for interface in machine.interfaces
                for link in interface.links
                if link.ip_address
            ],
            machine.zone,
            machine.owner,
            machine.tags,
        ]
        if self.with_type:
            data.insert(1, machine.node_type)
        return data


class DevicesTable(Table):

    def __init__(self):
        super().__init__(
            Column("hostname", "Hostname"),
            NodeOwnerColumn("owner", "Owner"),
            Column("ip_addresses", "IP addresses"),
        )

    def get_rows(self, target, devices):
        data = (
            (
                device.hostname,
                device.owner,
                [
                    link.ip_address
                    for interface in device.interfaces
                    for link in interface.links
                    if link.ip_address
                ]
            )
            for device in devices
        )
        return sorted(data, key=itemgetter(0))


class DeviceDetail(DetailTable):

    def __init__(self, with_type=False):
        self.with_type = with_type
        columns = [
            Column("hostname", "Hostname"),
            NodeInterfacesColumn("interfaces", "Interfaces"),
            Column("ip_addresses", "IP addresses"),
            NodeOwnerColumn("owner", "Owner"),
            Column("tags", "Tags"),
        ]
        if with_type:
            columns.insert(1, NodeTypeColumn("node_type", "Type"))
        super().__init__(*columns)

    def get_rows(self, target, device):
        data = [
            device.hostname,
            device.interfaces,
            [
                link.ip_address
                for interface in device.interfaces
                for link in interface.links
                if link.ip_address
            ],
            device.owner,
            device.tags,
        ]
        if self.with_type:
            data.insert(1, device.node_type)
        return data


class ControllersTable(Table):

    def __init__(self):
        super().__init__(
            Column("hostname", "Hostname"),
            NodeTypeColumn("node_type", "Type"),
            NodeArchitectureColumn("architecture", "Arch"),
            NodeCPUsColumn("cpus", "#CPUs"),
            NodeMemoryColumn("memory", "RAM"),
        )

    def get_rows(self, target, controllers):
        data = (
            (
                controller.hostname,
                controller.node_type,
                controller.architecture,
                controller.cpus,
                controller.memory,
            )
            for controller in controllers
        )
        return sorted(data, key=itemgetter(0))


class ControllerDetail(DetailTable):

    def __init__(self):
        super().__init__(
            Column("hostname", "Hostname"),
            NodeTypeColumn("node_type", "Type"),
            NodeArchitectureColumn("architecture", "Arch"),
            NodeCPUsColumn("cpus", "#CPUs"),
            NodeMemoryColumn("memory", "RAM"),
            NodeInterfacesColumn("interfaces", "Interfaces"),
            NodeZoneColumn("zone", "Zone"),
        )

    def get_rows(self, target, controller):
        return (
            controller.hostname,
            controller.node_type,
            controller.architecture,
            controller.cpus,
            controller.memory,
            controller.interfaces,
            controller.zone,
        )


class TagsTable(Table):

    def __init__(self):
        super().__init__(
            Column("name", "Tag name"),
            Column("definition", "Definition"),
            Column("kernel_opts", "Kernel options"),
            Column("comment", "Comment"),
        )

    def get_rows(self, target, tags):
        data = (
            (tag.name, tag.definition, tag.kernel_opts, tag.comment)
            for tag in tags
        )
        return sorted(data, key=itemgetter(0))


class FilesTable(Table):

    def __init__(self):
        super().__init__(
            Column("filename", "File name"),
        )

    def get_rows(self, target, files):
        data = ((f.filename,) for f in files)
        return sorted(data, key=itemgetter(0))


class UserIsAdminColumn(Column):

    yes, no = "Yes", "Np"
    yes_pretty = Color("{autogreen}Yes{/autogreen}")

    def render(self, target, is_admin):
        if target is RenderTarget.plain:
            return self.yes if is_admin else self.no
        elif target is RenderTarget.pretty:
            return self.yes_pretty if is_admin else self.no
        else:
            return super().render(target, is_admin)


class UsersTable(Table):

    def __init__(self):
        super().__init__(
            Column("username", "User name"),
            Column("email", "Email address"),
            UserIsAdminColumn("is_admin", "Admin?"),
        )

    def get_rows(self, target, users):
        data = ((user.username,) for user in users)
        return sorted(data, key=itemgetter(0))


class ProfileActiveColumn(Column):

    def render(self, target, is_anonymous):
        if target is RenderTarget.pretty:
            return "✓" if is_anonymous else " "
        elif target is RenderTarget.plain:
            return "X" if is_anonymous else " "
        else:
            return super().render(target, is_anonymous)


class ProfilesTable(Table):

    def __init__(self):
        super().__init__(
            Column("name", "Profile"),
            Column("url", "URL"),
            ProfileActiveColumn("is_default", "Active"),
        )

    def get_rows(self, target, profiles):
        default = profiles.default
        default_name = None if default is None else default.name
        data = (
            (profile.name, profile.url, (profile.name == default_name))
            for profile in (profiles.load(name) for name in profiles)
        )
        return sorted(data, key=itemgetter(0))


class VIDColumn(Column):

    def render(self, target, data):
        vlan, vlans = data, data._data['fabric'].vlans
        vlans = sorted(vlans, key=attrgetter('id'))
        if vlans[0] == vlan:
            if vlan.vid == 0:
                data = "untagged"
            else:
                data = "untagged (%d)" % vlan.vid
        else:
            data = vlan.vid
        return super().render(target, data)


class DHCPColumn(Column):

    def render(self, target, vlan):
        if vlan.dhcp_on:
            if vlan.primary_rack:
                if vlan.secondary_rack:
                    text = "HA Enabled"
                else:
                    text = "Enabled"
            if target == RenderTarget.pretty:
                text = Color("{autogreen}%s{/autogreen}") % text
        elif vlan.relay_vlan:
            text = "Relayed via %s.%s" % (vlan.fabric.name, vlan.vid)
            if target == RenderTarget.pretty:
                text = Color("{autoblue}%s{/autoblue}") % text
        else:
            text = "Disabled"
        return super().render(target, text)


class SpaceNameColumn(Column):

    def render(self, target, space):
        name = space.name
        if name == "undefined":
            name = "(undefined)"
        return super().render(target, name)


class SubnetNameColumn(Column):

    def render(self, target, subnet):
        name = subnet.cidr
        if subnet.name and subnet.name != name:
            name = "%s (%s)" % (name, subnet.name)
        return super().render(target, name)


class SubnetActiveColumn(Column):

    def render(self, target, active):
        if active:
            text = "Active"
        else:
            text = "Disabled"
        if target == RenderTarget.pretty and active:
            text = Color('{autogreen}Active{/autogreen}')
        return super().render(target, text)


class SubnetRDNSModeColumn(Column):

    def render(self, target, mode):
        if mode == RDNSMode.DISABLED:
            text = "Disabled"
        else:
            if mode == RDNSMode.ENABLED:
                text = "Enabled"
            elif mode == RDNSMode.RFC2317:
                text = "Enabled w/ RFC 2317"
            if target == RenderTarget.pretty:
                text = Color("{autogreen}%s{/autogreen}") % text
        return super().render(target, text)


class SubnetsTable(Table):

    def __init__(self, *, visible_columns=None, fabrics=None):
        self.fabrics = fabrics
        super().__init__(
            SubnetNameColumn("name", "Subnet"),
            VIDColumn("vid", "VID"),
            Column("fabric", "Fabric"),
            SpaceNameColumn("space", "Space"),
            visible_columns=visible_columns
        )

    def get_vlan(self, vlan):
        fabric = self.get_fabric(vlan.fabric)
        for fabric_vlan in fabric.vlans:
            if fabric_vlan.id == vlan.id:
                return fabric_vlan

    def get_fabric(self, unloaded_fabric):
        for fabric in self.fabrics:
            if fabric.id == unloaded_fabric.id:
                return fabric

    def get_rows(self, target, subnets):
        return (
            (
                subnet,
                self.get_vlan(subnet.vlan),
                self.get_fabric(subnet.vlan.fabric).name,
                subnet.vlan.space,
            )
            for subnet in sorted(subnets, key=attrgetter('cidr'))
        )


class SubnetDetail(DetailTable):

    def __init__(self, *, fabrics=None):
        self.fabrics = fabrics
        super().__init__(
            Column("name", "Name"),
            Column("cidr", "CIDR"),
            Column("gateway_ip", "Gateway IP"),
            Column("dns", "DNS"),
            VIDColumn("vid", "VID"),
            Column("fabric", "Fabric"),
            SpaceNameColumn("space", "Space"),
            SubnetActiveColumn("managed", "Managed allocation"),
            SubnetActiveColumn("allow_proxy", "Allow proxy"),
            SubnetActiveColumn("active_discovery", "Active discovery"),
            SubnetRDNSModeColumn("rdns_mode", "Reverse DNS mode"),
        )

    def get_vlan(self, vlan):
        fabric = self.get_fabric(vlan.fabric)
        for fabric_vlan in fabric.vlans:
            if fabric_vlan.id == vlan.id:
                return fabric_vlan

    def get_fabric(self, unloaded_fabric):
        for fabric in self.fabrics:
            if fabric.id == unloaded_fabric.id:
                return fabric

    def get_rows(self, target, subnet):
        return (
            subnet.name,
            subnet.cidr,
            subnet.gateway_ip,
            subnet.dns_servers,
            self.get_vlan(subnet.vlan),
            self.get_fabric(subnet.vlan.fabric).name,
            subnet.vlan.space,
            subnet.managed,
            subnet.allow_proxy,
            subnet.active_discovery,
            subnet.rdns_mode,
        )


class VlansTable(Table):

    def __init__(self, *, visible_columns=None, fabrics=None, subnets=None):
        self.subnets = subnets
        super().__init__(
            VIDColumn("vid", "VID"),
            DHCPColumn("dhcp", "DHCP"),
            SpaceNameColumn("space", "Space"),
            NestedTableColumn("subnets", "Subnets", SubnetsTable, None, {
                'visible_columns': ('name',),
                'fabrics': fabrics,
            }),
            visible_columns=visible_columns
        )

    def get_subnets(self, vlan):
        """Return the subnets for the `vlan`."""
        return vlan._origin.Subnets([
            subnet
            for subnet in self.subnets
            if subnet.vlan.id == vlan.id
        ])

    def get_rows(self, target, vlans):
        return (
            (
                vlan,
                vlan,
                vlan.space,
                self.get_subnets(vlan)
            )
            for vlan in sorted(vlans, key=attrgetter('vid'))
        )


class VlanDetail(DetailTable):

    def __init__(self, *, fabrics=None, subnets=None):
        self.fabrics = fabrics
        self.subnets = subnets
        super().__init__(
            VIDColumn("vid", "VID"),
            Column("name", "Name"),
            Column("fabric", "Fabric"),
            Column("mtu", "MTU"),
            DHCPColumn("dhcp", "DHCP"),
            Column("primary_rack", "Primary rack"),
            Column("secondary_rack", "Secondary rack"),
            SpaceNameColumn("space", "Space"),
            NestedTableColumn("subnets", "Subnets", SubnetsTable, None, {
                'visible_columns': ('name',),
                'fabrics': fabrics,
            }),
        )

    def get_fabric(self, vlan):
        for fabric in self.fabrics:
            if fabric.id == vlan.fabric.id:
                return fabric

    def get_subnets(self, vlan):
        """Return the subnets for the `vlan`."""
        return vlan._origin.Subnets([
            subnet
            for subnet in self.subnets
            if subnet.vlan.id == vlan.id
        ])

    def get_rows(self, target, vlan):
        primary_rack = vlan.primary_rack
        if primary_rack is not None:
            primary_rack.refresh()
        secondary_rack = vlan.secondary_rack
        if secondary_rack is not None:
            secondary_rack.refresh()
        return (
            vlan,
            vlan.name,
            self.get_fabric(vlan).name,
            vlan.mtu,
            vlan,
            primary_rack.hostname if primary_rack else None,
            secondary_rack.hostname if secondary_rack else None,
            vlan.space,
            self.get_subnets(vlan)
        )


class FabricsTable(Table):

    def __init__(self, *, visible_columns=None, subnets=None):
        super().__init__(
            Column("name", "Fabric"),
            NestedTableColumn(
                "vlans", "VLANs", VlansTable, None, {'subnets': subnets}),
            visible_columns=visible_columns
        )

    def get_rows(self, target, fabrics):
        self['vlans'].table_kwargs['fabrics'] = fabrics
        return (
            (
                fabric.name,
                fabric.vlans
            )
            for fabric in sorted(fabrics, key=attrgetter('id'))
        )


class FabricDetail(DetailTable):

    def __init__(self, *, fabrics=None, subnets=None):
        super().__init__(
            Column("name", "Name"),
            NestedTableColumn(
                "vlans", "VLANs", VlansTable, None, {
                    'fabrics': fabrics,
                    'subnets': subnets}),
        )

    def get_rows(self, target, fabric):
        return (
            fabric.name,
            fabric.vlans,
        )


class SpacesTable(Table):

    def __init__(self, *, visible_columns=None, fabrics=None, subnets=None):
        self.fabrics = fabrics
        super().__init__(
            SpaceNameColumn("name", "Space"),
            NestedTableColumn(
                "vlans", "VLANs", VlansTable, None, {
                    'visible_columns': ('vid', 'dhcp', 'subnets'),
                    'fabrics': fabrics,
                    'subnets': subnets}),
            visible_columns=visible_columns
        )

    def get_fabric(self, vlan):
        for fabric in self.fabrics:
            for fabric_vlan in fabric.vlans:
                if fabric_vlan.id == vlan.id:
                    return fabric

    def get_vlans(self, vlans):
        for vlan in vlans:
            vlan._data['fabric'] = self.get_fabric(vlan)
        return vlans

    def get_rows(self, target, spaces):
        return (
            (
                space,
                self.get_vlans(space.vlans)
            )
            for space in sorted(spaces, key=attrgetter('name'))
        )


class SpaceDetail(DetailTable):

    def __init__(self, *, fabrics=None, subnets=None):
        self.fabrics = fabrics
        super().__init__(
            SpaceNameColumn("name", "Space"),
            NestedTableColumn(
                "vlans", "VLANs", VlansTable, None, {
                    'visible_columns': ('vid', 'dhcp', 'subnets'),
                    'fabrics': fabrics,
                    'subnets': subnets}),
        )

    def get_fabric(self, vlan):
        for fabric in self.fabrics:
            for fabric_vlan in fabric.vlans:
                if fabric_vlan.id == vlan.id:
                    return fabric

    def get_vlans(self, vlans):
        for vlan in vlans:
            vlan._data['fabric'] = self.get_fabric(vlan)
        return vlans

    def get_rows(self, target, space):
        return (
            space,
            self.get_vlans(space.vlans)
        )
