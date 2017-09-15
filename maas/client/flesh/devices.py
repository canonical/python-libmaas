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

    def execute(self, origin, options, target):
        table = tables.DevicesTable()
        return table.render(target, origin.Devices.read())


def register(parser):
    """Register commands with the given parser."""
    cmd_devices.register(parser)
