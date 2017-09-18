"""Tables for representing information from MAAS."""

__all__ = [
    "FilesTable",
    "NodesTable",
    "ProfilesTable",
    "TagsTable",
    "UsersTable",
]

from operator import itemgetter

from colorclass import Color

from ..enum import NodeType
from .tabular import (
    Column,
    RenderTarget,
    Table,
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
        "on": "autogreen",
        # "off": "",  # White.
        "error": "autored",
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


class NodesTable(Table):

    def __init__(self):
        super().__init__(
            Column("hostname", "Hostname"),
            NodeTypeColumn("node_type", "Type"),
        )

    def render(self, target, nodes):
        data = (
            (node.hostname, node.node_type)
            for node in nodes
        )
        data = sorted(data, key=itemgetter(0))
        return super().render(target, data)


class MachinesTable(Table):

    def __init__(self):
        super().__init__(
            Column("hostname", "Hostname"),
            NodePowerColumn("power", "Power"),
            NodeStatusNameColumn("status", "Status"),
            NodeArchitectureColumn("architecture", "Arch"),
            NodeCPUsColumn("cpus", "#CPUs"),
            NodeMemoryColumn("memory", "RAM"),
        )

    def render(self, target, machines):
        data = (
            (
                machine.hostname,
                machine.power_state,
                machine.status_name,
                machine.architecture,
                machine.cpus,
                machine.memory,
            )
            for machine in machines
        )
        data = sorted(data, key=itemgetter(0))
        return super().render(target, data)


class DevicesTable(Table):

    def __init__(self):
        super().__init__(
            Column("hostname", "Hostname"),
            Column("ip_addresses", "IP addresses"),
        )

    def render(self, target, devices):
        data = (
            (
                device.hostname,
                [
                    link.ip_address
                    for interface in device.interfaces
                    for link in interface.links
                    if link.ip_address
                ]
            )
            for device in devices
        )
        data = sorted(data, key=itemgetter(0))
        return super().render(target, data)


class ControllersTable(Table):

    def __init__(self):
        super().__init__(
            Column("hostname", "Hostname"),
            NodeTypeColumn("node_type", "Type"),
            NodeArchitectureColumn("architecture", "Arch"),
            NodeCPUsColumn("cpus", "#CPUs"),
            NodeMemoryColumn("memory", "RAM"),
        )

    def render(self, target, controllers):
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
        data = sorted(data, key=itemgetter(0))
        return super().render(target, data)


class TagsTable(Table):

    def __init__(self):
        super().__init__(
            Column("name", "Tag name"),
            Column("definition", "Definition"),
            Column("kernel_opts", "Kernel options"),
            Column("comment", "Comment"),
        )

    def render(self, target, tags):
        data = (
            (tag.name, tag.definition, tag.kernel_opts, tag.comment)
            for tag in tags
        )
        data = sorted(data, key=itemgetter(0))
        return super().render(target, data)


class FilesTable(Table):

    def __init__(self):
        super().__init__(
            Column("filename", "File name"),
        )

    def render(self, target, files):
        data = ((f.filename,) for f in files)
        data = sorted(data, key=itemgetter(0))
        return super().render(target, data)


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

    def render(self, target, users):
        data = ((user.username,) for user in users)
        data = sorted(data, key=itemgetter(0))
        return super().render(target, data)


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

    def render(self, target, profiles):
        default = profiles.default
        default_name = None if default is None else default.name
        data = (
            (profile.name, profile.url, (profile.name == default_name))
            for profile in (profiles.load(name) for name in profiles)
        )
        data = sorted(data, key=itemgetter(0))
        return super().render(target, data)
