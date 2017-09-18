"""Commands for users."""

__all__ = [
    "register",
]

from . import (
    OriginPagedTableCommand,
    tables,
)


class cmd_users(OriginPagedTableCommand):
    """List users."""

    def execute(self, origin, options, target):
        table = tables.UsersTable()
        return table.render(target, origin.Users.read())


def register(parser):
    """Register profile commands with the given parser."""
    cmd_users.register(parser)
