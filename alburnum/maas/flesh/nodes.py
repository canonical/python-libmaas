"""Commands for nodes."""

__all__ = [
    "register",
]

from time import sleep

from . import (
    colorized,
    CommandError,
    OriginTableCommand,
    tables,
)
from .. import utils


class cmd_acquire_node(OriginTableCommand):
    """Acquire a node."""

    def __init__(self, parser):
        super(cmd_acquire_node, self).__init__(parser)
        parser.add_argument("--hostname")
        parser.add_argument("--architecture")
        parser.add_argument("--cpus", type=int)
        parser.add_argument("--memory", type=float)
        parser.add_argument("--tags", default="")

    def acquire(self, origin, options):
        return origin.Nodes.acquire(
            hostname=options.hostname, architecture=options.architecture,
            cpus=options.cpus, memory=options.memory,
            tags=options.tags.split())

    def execute(self, origin, options, target):
        node = self.acquire(origin, options)
        table = tables.NodesTable()
        print(table.render(target, [node]))


class cmd_launch_node(cmd_acquire_node):
    """Acquire and deploy a node."""

    def __init__(self, parser):
        super(cmd_launch_node, self).__init__(parser)
        parser.add_argument(
            "--wait", type=int, default=0, help=(
                "Number of seconds to wait for deploy to complete."))

    def execute(self, origin, options, target):
        node = self.acquire(origin, options)
        table = tables.NodesTable()

        print(colorized("{automagenta}DEPLOYING:{/automagenta}"))
        print(table.render(target, [node]))

        with utils.Spinner():
            node = node.start()
            for elapsed, remaining, wait in utils.retries(options.wait, 1.0):
                if node.substatus_name == "Deploying":
                    sleep(wait)
                    node = origin.Node.read(system_id=node.system_id)
                else:
                    break

        if node.substatus_name == "Deployed":
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
                if node.substatus_name == "Releasing":
                    sleep(wait)
                    node = origin.Node.read(system_id=node.system_id)
                else:
                    break

        table = tables.NodesTable()
        print(table.render(target, [node]))

        if node.substatus_name != "Ready":
            raise CommandError("Node was not released.")


class cmd_list_nodes(OriginTableCommand):
    """List nodes."""

    def execute(self, origin, options, target):
        table = tables.NodesTable()
        print(table.render(target, origin.Nodes))


def register(parser):
    """Register commands with the given parser."""
    cmd_acquire_node.register(parser["acquire"], "node")
    cmd_launch_node.register(parser["launch"], "node")
    cmd_release_node.register(parser["release"], "node")
    cmd_list_nodes.register(parser["list"], "nodes")
