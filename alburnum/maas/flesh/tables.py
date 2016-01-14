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

from .tabular import (
    Column,
    RenderTarget,
    Table,
)


class NodeMemoryColumn(Column):

    def render(self, target, memory):
        # `memory` is in MB.
        if target in (RenderTarget.pretty, RenderTarget.plain):
            if memory < 1024.0:  # <1GB
                memory = "%0.1f MB" % (memory)
            elif memory < 1048576.0:  # <1TB
                memory = "%0.1f GB" % (memory / 1024.0)
            else:
                memory = "%0.1f TB" % (memory / 1048576.0)
        return super().render(target, memory)


class NodeSubStatusNameColumn(Column):

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
            Column("hostname", "Hostname"),
            Column("system_id", "System ID"),
            Column("architecture", "Architecture"),
            Column("cpus", "#CPUs"),
            NodeMemoryColumn("memory", "RAM"),
            NodeSubStatusNameColumn("status", "Status"),
            NodePowerColumn("power", "Power"),
        )

    def render(self, target, nodes):
        data = (
            (node.hostname, node.system_id, node.architecture, node.cpus,
             node.memory, node.substatus_name, node.power_state)
            for node in nodes
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


class ProfileAnonymousColumn(Column):

    def render(self, target, is_anonymous):
        if target in (RenderTarget.pretty, RenderTarget.plain):
            return "Yes" if is_anonymous else "No"
        else:
            return super().render(target, is_anonymous)


class ProfilesTable(Table):

    def __init__(self):
        super().__init__(
            Column("name", "Profile name"),
            Column("url", "URL"),
            ProfileAnonymousColumn("is_anonymous", "Anonymous?"),
        )

    def render(self, target, profiles):
        data = (
            (profile.name, profile.url, profile.credentials is None)
            for profile in (profiles.load(name) for name in profiles)
        )
        data = sorted(data, key=itemgetter(0))
        return super().render(target, data)
