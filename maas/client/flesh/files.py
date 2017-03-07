"""Commands for files."""

__all__ = [
    "register",
]

from . import (
    OriginTableCommand,
    tables,
)


class cmd_list_files(OriginTableCommand):
    """List files."""

    def execute(self, origin, options, target):
        table = tables.FilesTable()
        print(table.render(target, origin.Files.read()))


def register(parser):
    """Register profile commands with the given parser."""
    cmd_list_files.register(parser)
