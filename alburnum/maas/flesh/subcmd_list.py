"""Commands for listing things."""

__all__ = [
    "register",
]

from . import (
    OriginTableCommand,
    tables,
)


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


def register(parser):
    """Register profile commands with the given parser."""
    cmd_files.register(parser["list"], "files")
    cmd_tags.register(parser["list"], "tags")
    cmd_users.register(parser["list"], "users")
