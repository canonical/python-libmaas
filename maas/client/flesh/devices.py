"""Commands for devices."""

__all__ = [
    "register",
]

from . import (
    CommandError,
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


class cmd_device(OriginPagedTableCommand):
    """Details of a device."""

    def __init__(self, parser):
        super(cmd_device, self).__init__(parser)
        parser.add_argument("hostname", nargs=1, help=(
            "Hostname of the device."))

    def execute(self, origin, options, target):
        devices = origin.Devices.read(hostnames=options.hostname)
        if len(devices) == 0:
            raise CommandError(
                "Unable to find device %s." % options.hostname[0])
        device = devices[0]
        table = tables.DeviceDetail()
        return table.render(target, device)


def register(parser):
    """Register commands with the given parser."""
    cmd_devices.register(parser)
    cmd_device.register(parser)
