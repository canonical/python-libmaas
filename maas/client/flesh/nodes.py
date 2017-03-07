"""Commands for nodes."""

__all__ = [
    "register",
]

import asyncio
from itertools import chain
from time import sleep

from . import (
    colorized,
    CommandError,
    OriginTableCommand,
    tables,
)
from .. import utils
from ..utils.async import asynchronous


class cmd_allocate_machine(OriginTableCommand):
    """Allocate a machine."""

    def __init__(self, parser):
        super(cmd_allocate_machine, self).__init__(parser)
        parser.add_argument("--hostname")
        parser.add_argument("--architecture")
        parser.add_argument("--cpus", type=int)
        parser.add_argument("--memory", type=float)
        parser.add_argument("--tags", default="")

    def allocate(self, origin, options):
        return origin.Machines.allocate(
            hostname=options.hostname, architecture=options.architecture,
            cpus=options.cpus, memory=options.memory,
            tags=options.tags.split())

    def execute(self, origin, options, target):
        machine = self.allocate(origin, options)
        table = tables.NodesTable()
        print(table.render(target, [machine]))


class cmd_launch_machine(cmd_allocate_machine):
    """Allocate and deploy a machine."""

    def __init__(self, parser):
        super(cmd_launch_machine, self).__init__(parser)
        parser.add_argument(
            "--wait", type=int, default=0, help=(
                "Number of seconds to wait for deploy to complete."))

    def execute(self, origin, options, target):
        machine = self.allocate(origin, options)
        table = tables.NodesTable()

        print(colorized("{automagenta}DEPLOYING:{/automagenta}"))
        print(table.render(target, [machine]))

        with utils.Spinner():
            machine = machine.deploy()
            for elapsed, remaining, wait in utils.retries(options.wait, 1.0):
                if machine.status_name == "Deploying":
                    sleep(wait)
                    machine = origin.Machine.read(system_id=machine.system_id)
                else:
                    break

        if machine.status_name == "Deployed":
            print(colorized("{autogreen}DEPLOYED:{/autogreen}"))
            print(table.render(target, [machine]))
        else:
            print(colorized("{autored}FAILED TO DEPLOY:{/autored}"))
            print(table.render(target, [machine]))
            raise CommandError("Machine was not deployed.")


class cmd_release_machine(OriginTableCommand):
    """Release a machine."""

    def __init__(self, parser):
        super(cmd_release_machine, self).__init__(parser)
        parser.add_argument("--system-id", required=True)
        parser.add_argument(
            "--wait", type=int, default=0, help=(
                "Number of seconds to wait for release to complete."))

    def execute(self, origin, options, target):
        machine = origin.Machine.read(system_id=options.system_id)
        machine = machine.release()

        with utils.Spinner():
            for elapsed, remaining, wait in utils.retries(options.wait, 1.0):
                if machine.status_name == "Releasing":
                    sleep(wait)
                    machine = origin.Machine.read(system_id=machine.system_id)
                else:
                    break

        table = tables.NodesTable()
        print(table.render(target, [machine]))

        if machine.status_name != "Ready":
            raise CommandError("Machine was not released.")


class cmd_list_nodes(OriginTableCommand):
    """List machine, devices, rack & region controllers."""

    def __init__(self, parser):
        super(cmd_list_nodes, self).__init__(parser)
        parser.add_argument(
            "--all", action="store_true", default=False,
            help="Show all (machines, devices, rack & region controllers).")
        parser.add_argument(
            "--devices", action="store_true", default=False,
            help="Show devices.")
        parser.add_argument(
            "--machines", action="store_true", default=False,
            help="Show machines.")
        parser.add_argument(
            "--rack-controllers", action="store_true", default=False,
            help="Show rack-controllers.")
        parser.add_argument(
            "--region-controllers", action="store_true", default=False,
            help="Show region controllers.")

    @asynchronous
    async def execute(self, origin, options, target):
        nodesets = []

        if options.all or options.devices:
            nodesets.append(origin.Devices)
        if options.all or options.machines:
            nodesets.append(origin.Machines)
        if options.all or options.rack_controllers:
            nodesets.append(origin.RackControllers)
        if options.all or options.region_controllers:
            nodesets.append(origin.RegionControllers)

        if len(nodesets) == 0:
            nodesets.append(origin.Machines)

        # Don't make more than two concurrent requests to MAAS.
        semaphore = asyncio.Semaphore(2)

        async def read(nodeset):
            async with semaphore:
                return await nodeset.read()

        nodesets = await asyncio.gather(*map(read, nodesets))
        nodes = chain.from_iterable(nodesets)

        nodes = list(nodes)

        table = tables.NodesTable()
        print(table.render(target, nodes))


def register(parser):
    """Register commands with the given parser."""
    cmd_list_nodes.register(parser, "list")
    cmd_allocate_machine.register(parser, "allocate")
    cmd_launch_machine.register(parser, "launch")
    cmd_release_machine.register(parser, "release")
