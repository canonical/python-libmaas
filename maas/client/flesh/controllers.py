"""Commands for controllers."""

__all__ = [
    "register",
]

import asyncio
from itertools import chain

from . import (
    CommandError,
    OriginPagedTableCommand,
    tables,
)
from ..enum import NodeType
from ..utils.async import asynchronous


class cmd_controllers(OriginPagedTableCommand):
    """List controllers."""

    def __init__(self, parser):
        super(cmd_controllers, self).__init__(parser)
        parser.add_argument("hostname", nargs='*', help=(
            "Hostname of the controller."))

    @asynchronous
    async def execute(self, origin, options, target):
        hostnames = None
        if options.hostname:
            hostnames = options.hostname

        controller_sets = await asyncio.gather(
            origin.RackControllers.read(hostnames=hostnames),
            origin.RegionControllers.read(hostnames=hostnames))
        controllers = {
            controller.system_id: controller
            for controller in chain.from_iterable(controller_sets)
        }
        table = tables.ControllersTable()
        return table.render(target, controllers.values())


class cmd_controller(OriginPagedTableCommand):
    """Details of a controller."""

    def __init__(self, parser):
        super(cmd_controller, self).__init__(parser)
        parser.add_argument("hostname", nargs=1, help=(
            "Hostname of the controller."))

    def execute(self, origin, options, target):
        nodes = origin.Nodes.read(hostnames=options.hostname)
        if len(nodes) == 0:
            raise CommandError(
                "Unable to find controller %s." % options.hostname[0])
        node = nodes[0]
        if node.node_type == NodeType.RACK_CONTROLLER:
            table = tables.ControllerDetail()
            node = node.as_rack_controller()
        elif node.node_type == NodeType.REGION_CONTROLLER:
            table = tables.ControllerDetail()
            node = node.as_region_controller()
        elif node.node_type == NodeType.REGION_AND_RACK_CONTROLLER:
            table = tables.ControllerDetail()
            node = node.as_rack_controller()
        else:
            raise CommandError(
                "Unable to find controller %s." % options.hostname[0])
        return table.render(target, node)


def register(parser):
    """Register commands with the given parser."""
    cmd_controllers.register(parser)
    cmd_controller.register(parser)
