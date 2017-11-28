"""Commands for nodes."""

__all__ = [
    "register",
]

from . import (
    CommandError,
    OriginPagedTableCommand,
    tables,
)
from ..enum import NodeType


class cmd_nodes(OriginPagedTableCommand):
    """List nodes."""

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


class cmd_node(OriginPagedTableCommand):
    """Details of a node."""

    def __init__(self, parser):
        super(cmd_node, self).__init__(parser)
        parser.add_argument("hostname", nargs=1, help=(
            "Hostname of the node."))

    def execute(self, origin, options, target):
        nodes = origin.Nodes.read(hostnames=options.hostname)
        if len(nodes) == 0:
            raise CommandError(
                "Unable to find node %s." % options.hostname[0])
        node = nodes[0]
        if node.node_type == NodeType.MACHINE:
            table = tables.MachineDetail(with_type=True)
            node = node.as_machine()
        elif node.node_type == NodeType.DEVICE:
            table = tables.DeviceDetail(with_type=True)
            node = node.as_device()
        elif node.node_type == NodeType.RACK_CONTROLLER:
            table = tables.ControllerDetail()
            node = node.as_rack_controller()
        elif node.node_type == NodeType.REGION_CONTROLLER:
            table = tables.ControllerDetail()
            node = node.as_region_controller()
        elif node.node_type == NodeType.REGION_AND_RACK_CONTROLLER:
            table = tables.ControllerDetail()
            node = node.as_rack_controller()
        return table.render(target, node)


def register(parser):
    """Register commands with the given parser."""
    cmd_nodes.register(parser)
    cmd_node.register(parser)
