"""Commands for users."""

__all__ = [
    "register",
]

from . import (
    OriginTableCommand,
    tables,
)


class cmd_list_users(OriginTableCommand):
    """List users."""

    def execute(self, origin, options, target):
        table = tables.UsersTable()
        print(table.render(target, origin.Users.read()))


def register(parser):
    """Register profile commands with the given parser."""
    cmd_list_users.register(parser)
