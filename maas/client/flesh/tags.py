"""Commands for tags."""

__all__ = [
    "register",
]

from . import (
    OriginTableCommand,
    tables,
)


class cmd_list_tags(OriginTableCommand):
    """List tags."""

    def execute(self, origin, options, target):
        table = tables.TagsTable()
        print(table.render(target, origin.Tags.read()))


def register(parser):
    """Register profile commands with the given parser."""
    cmd_list_tags.register(parser)
