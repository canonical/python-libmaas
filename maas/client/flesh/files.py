"""Commands for files."""

__all__ = [
    "register",
]

from . import (
    OriginPagedTableCommand,
    tables,
)


class cmd_files(OriginPagedTableCommand):
    """List files."""

    def execute(self, origin, options, target):
        table = tables.FilesTable()
        return table.render(target, origin.Files.read())


def register(parser):
    """Register profile commands with the given parser."""
    cmd_files.register(parser)
