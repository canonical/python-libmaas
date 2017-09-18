"""Commands for tags."""

__all__ = [
    "register",
]

from . import (
    OriginPagedTableCommand,
    tables,
)


class cmd_tags(OriginPagedTableCommand):
    """List tags."""

    def execute(self, origin, options, target):
        table = tables.TagsTable()
        return table.render(target, origin.Tags.read())


def register(parser):
    """Register profile commands with the given parser."""
    cmd_tags.register(parser)
