"""Commands for listing things."""

__all__ = [
    "register_as",
]

from . import (
    OriginTableCommand,
    tables,
)


class cmd_nodes(OriginTableCommand):
    """List nodes."""

    def execute(self, origin, options, target):
        table = tables.NodesTable()
        print(table.render(target, origin.Nodes))


class cmd_tags(OriginTableCommand):
    """List tags."""

    def execute(self, origin, options, target):
        table = tables.TagsTable()
        print(table.render(target, origin.Tags))


class cmd_files(OriginTableCommand):
    """List files."""

    def execute(self, origin, options, target):
        table = tables.FilesTable()
        print(table.render(target, origin.Files))


class cmd_users(OriginTableCommand):
    """List users."""

    def execute(self, origin, options, target):
        table = tables.UsersTable()
        print(table.render(target, origin.Users))


def register_as(name, parser):
    """Register profile commands with the given parser."""
    parser = parser.subparsers.add_parser(
        name, help="List files, tags, nodes, etc.",
        description="List.", epilog="")

    cmd_nodes.register(parser)
    cmd_tags.register(parser)
    cmd_files.register(parser)
    cmd_users.register(parser)
