"""Commands for nodes."""

__all__ = [
    "register",
]

from . import (
    OriginPagedTableCommand,
    tables,
)


class cmd_nodes(OriginPagedTableCommand):
    """List all nodes."""

    def execute(self, origin, options, target):
        table = tables.NodesTable()
        return table.render(target, origin.Nodes.read())


def register(parser):
    """Register commands with the given parser."""
    cmd_nodes.register(parser)
