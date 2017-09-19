"""Commands for devices."""

__all__ = [
    "register",
]

from . import (
    OriginPagedTableCommand,
    tables,
)


class cmd_devices(OriginPagedTableCommand):
    """List all devices."""

    def __init__(self, parser):
        super(cmd_devices, self).__init__(parser)
        parser.add_argument("hostname", nargs='*', help=(
            "Hostname of the device."))

    def execute(self, origin, options, target):
        hostnames = None
        if options.hostname:
            hostnames = options.hostname
        table = tables.DevicesTable()
        return table.render(target, origin.Devices.read(hostnames=hostnames))


def register(parser):
    """Register commands with the given parser."""
    cmd_devices.register(parser)
