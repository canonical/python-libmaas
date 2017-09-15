"""Commands for machines."""

__all__ = [
    "register",
]

from time import sleep

from . import (
    colorized,
    CommandError,
    OriginTableCommand,
    OriginPagedTableCommand,
    tables,
)
from .. import utils


class cmd_machines(OriginPagedTableCommand):
    """List all machines."""

    def execute(self, origin, options, target):
        table = tables.MachinesTable()
        return table.render(target, origin.Machines.read())


class cmd_allocate(OriginTableCommand):
    """Allocate a machine."""

    def __init__(self, parser):
        super(cmd_allocate, self).__init__(parser)
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


class cmd_launch(cmd_allocate):
    """Allocate and deploy a machine."""

    def __init__(self, parser):
        super(cmd_launch, self).__init__(parser)
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


class cmd_release(OriginTableCommand):
    """Release a machine."""

    def __init__(self, parser):
        super(cmd_release, self).__init__(parser)
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


def register(parser):
    """Register commands with the given parser."""
    cmd_machines.register(parser)
    cmd_allocate.register(parser)
    cmd_launch.register(parser)
    cmd_release.register(parser)
