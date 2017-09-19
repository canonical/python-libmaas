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

    def __init__(self, parser):
        super(cmd_nodes, self).__init__(parser)
        parser.add_argument("hostname", nargs='*', help=(
            "Hostname of the node."))

    def execute(self, origin, options, target):
        hostnames = None
        if options.hostname:
            hostnames = options.hostname
        table = tables.NodesTable()
        return table.render(target, origin.Nodes.read(hostnames=hostnames))


def register(parser):
    """Register commands with the given parser."""
    cmd_nodes.register(parser)
