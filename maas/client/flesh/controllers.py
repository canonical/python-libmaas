"""Commands for controllers."""

__all__ = [
    "register",
]

import asyncio
from itertools import chain

from . import (
    OriginPagedTableCommand,
    tables,
)
from ..utils.async import asynchronous


class cmd_controllers(OriginPagedTableCommand):
    """List all controllers."""

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


def register(parser):
    """Register commands with the given parser."""
    cmd_controllers.register(parser)
