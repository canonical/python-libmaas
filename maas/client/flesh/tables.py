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

from ..viscera.controllers import (
    RackController,
    RegionController,
)
from ..viscera.devices import Device
from ..viscera.machines import Machine
from .tabular import (
    Column,
    RenderTarget,
    Table,
)


class NodeTypeColumn(Column):

    DEVICE = 1
    MACHINE = 2
    RACK = 3
    REGION = 4

    GLYPHS = {
        DEVICE: Color("."),
        MACHINE: Color("{autoblue}m{/autoblue}"),
        RACK: Color("{yellow}c{/yellow}"),
        REGION: Color("{automagenta}C{/automagenta}"),
    }

    def render(self, target, num):
        glyph = self.GLYPHS[num]
        if target == RenderTarget.pretty:
            return glyph
        else:
            return glyph.value_no_colors


class NodeArchitectureColumn(Column):

    def render(self, target, architecture):
        if target in (RenderTarget.pretty, RenderTarget.plain):
            if architecture is None:
                architecture = "-"
            elif len(architecture) == 0:
                architecture = "-"
            elif architecture.isspace():
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
                    colour, data.capitalize(), colour))
            else:
                return data.capitalize()
        elif target == RenderTarget.plain:
            return super().render(target, data.capitalize())
        else:
            return super().render(target, data)


class NodesTable(Table):

    def __init__(self):
        super().__init__(
            NodeTypeColumn("type", ""),
            Column("hostname", "Hostname"),
            Column("system_id", "System ID"),
            NodeArchitectureColumn("architecture", "Architecture"),
            NodeCPUsColumn("cpus", "#CPUs"),
            NodeMemoryColumn("memory", "RAM"),
            NodeStatusNameColumn("status", "Status"),
            NodePowerColumn("power", "Power"),
        )

    @classmethod
    def data_for(cls, node):
        if isinstance(node, Device):
            return (
                NodeTypeColumn.DEVICE,
                node.hostname,
                node.system_id,
                "-",
                None,
                None,
                "-",
                "-",
            )
        elif isinstance(node, Machine):
            return (
                NodeTypeColumn.MACHINE,
                node.hostname,
                node.system_id,
                node.architecture,
                node.cpus,
                node.memory,
                node.status_name,
                node.power_state,
            )
        elif isinstance(node, RackController):
            return (
                NodeTypeColumn.RACK,
                node.hostname,
                node.system_id,
                node.architecture,
                node.cpus,
                node.memory,
                "—",  # status_name
                node.power_state,
            )
        elif isinstance(node, RegionController):
            return (
                NodeTypeColumn.REGION,
                node.hostname,
                node.system_id,
                node.architecture,
                node.cpus,
                node.memory,
                "—",  # status_name
                node.power_state,
            )
        else:
            raise TypeError(
                "Cannot extract data from %r (%s)"
                % (node, type(node).__name__))

    def render(self, target, nodes):
        data = map(self.data_for, nodes)
        data = sorted(data, key=itemgetter(0, 1))
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


class ProfileAnonymousColumn(Column):

    def render(self, target, is_anonymous):
        if target in (RenderTarget.pretty, RenderTarget.plain):
            return "Yes" if is_anonymous else "No"
        else:
            return super().render(target, is_anonymous)


class ProfileDefaultColumn(Column):

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
            Column("name", "Profile name"),
            Column("url", "URL"),
            ProfileAnonymousColumn("is_anonymous", "Anonymous?"),
            ProfileDefaultColumn("is_default", "Default?"),
        )

    def render(self, target, profiles):
        default = profiles.default
        default_name = None if default is None else default.name
        data = (
            (profile.name, profile.url, (profile.credentials is None),
             (profile.name == default_name))
            for profile in (profiles.load(name) for name in profiles)
        )
        data = sorted(data, key=itemgetter(0))
        return super().render(target, data)
