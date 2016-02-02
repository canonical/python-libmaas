"""Commands for nodes."""

__all__ = [
    "register",
]

from itertools import chain
from time import sleep

from . import (
    colorized,
    CommandError,
    OriginTableCommand,
    tables,
)
from .. import utils


class cmd_allocate_node(OriginTableCommand):
    """Allocate a node."""

    def __init__(self, parser):
        super(cmd_allocate_node, self).__init__(parser)
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
        node = self.allocate(origin, options)
        table = tables.NodesTable()
        print(table.render(target, [node]))


class cmd_launch_node(cmd_allocate_node):
    """Allocate and deploy a node."""

    def __init__(self, parser):
        super(cmd_launch_node, self).__init__(parser)
        parser.add_argument(
            "--wait", type=int, default=0, help=(
                "Number of seconds to wait for deploy to complete."))

    def execute(self, origin, options, target):
        node = self.allocate(origin, options)
        table = tables.NodesTable()

        print(colorized("{automagenta}DEPLOYING:{/automagenta}"))
        print(table.render(target, [node]))

        with utils.Spinner():
            node = node.start()
            for elapsed, remaining, wait in utils.retries(options.wait, 1.0):
                if node.status_name == "Deploying":
                    sleep(wait)
                    node = origin.Node.read(system_id=node.system_id)
                else:
                    break

        if node.status_name == "Deployed":
            print(colorized("{autogreen}DEPLOYED:{/autogreen}"))
            print(table.render(target, [node]))
        else:
            print(colorized("{autored}FAILED TO DEPLOY:{/autored}"))
            print(table.render(target, [node]))
            raise CommandError("Node was not deployed.")


class cmd_release_node(OriginTableCommand):
    """Release a node."""

    def __init__(self, parser):
        super(cmd_release_node, self).__init__(parser)
        parser.add_argument("--system-id", required=True)
        parser.add_argument(
            "--wait", type=int, default=0, help=(
                "Number of seconds to wait for release to complete."))

    def execute(self, origin, options, target):
        node = origin.Node.read(system_id=options.system_id)
        node = node.release()

        with utils.Spinner():
            for elapsed, remaining, wait in utils.retries(options.wait, 1.0):
                if node.status_name == "Releasing":
                    sleep(wait)
                    node = origin.Node.read(system_id=node.system_id)
                else:
                    break

        table = tables.NodesTable()
        print(table.render(target, [node]))

        if node.status_name != "Ready":
            raise CommandError("Node was not released.")


class cmd_list_nodes(OriginTableCommand):
    """Show nodes."""

    def __init__(self, parser):
        super(cmd_list_nodes, self).__init__(parser)
        parser.add_argument(
            "--all", action="store_true", default=False,
            help="Show all (machines, devices, racks, and regions).")
        parser.add_argument(
            "--devices", action="store_true", default=False,
            help="Show devices.")
        parser.add_argument(
            "--machines", action="store_true", default=False,
            help="Show machines.")
        parser.add_argument(
            "--racks", action="store_true", default=False,
            help="Show racks.")
        parser.add_argument(
            "--regions", action="store_true", default=False,
            help="Show regions.")

    def execute(self, origin, options, target):
        nodes = []

        # if options.all or options.devices:
        #     nodes.append(origin.Devices)
        if options.all or options.machines:
            nodes.append(origin.Machines)
        # if options.all or options.racks:
        #     nodes.append(origin.Racks)
        # if options.all or options.regions:
        #     nodes.append(origin.Regions)

        if len(nodes) == 0:
            nodes.append(origin.Machines)

        nodes = chain.from_iterable(nodes)
        table = tables.NodesTable()
        print(table.render(target, nodes))


def register(parser):
    """Register commands with the given parser."""
    cmd_allocate_node.register(parser, "allocate")
    cmd_launch_node.register(parser, "launch")
    cmd_release_node.register(parser, "release")
    cmd_list_nodes.register(parser, "list")
