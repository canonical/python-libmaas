"""Commands for subnets."""

__all__ = [
    "register",
]

from http import HTTPStatus

from . import (
    CommandError,
    OriginPagedTableCommand,
    tables,
)
from ..bones import CallError
from ..utils.maas_async import asynchronous


class cmd_subnets(OriginPagedTableCommand):
    """List subnets."""

    def __init__(self, parser):
        super(cmd_subnets, self).__init__(parser)
        parser.add_argument("--minimal", action="store_true", help=(
            "Output only the subnet names."))

    @asynchronous
    async def load_object_sets(self, origin):
        subnets = origin.Subnets.read()
        fabrics = origin.Fabrics.read()
        return await subnets, await fabrics

    def execute(self, origin, options, target):
        visible_columns = None
        if options.minimal:
            visible_columns = ('name',)
        subnets, fabrics = self.load_object_sets(origin)
        table = tables.SubnetsTable(
            visible_columns=visible_columns, fabrics=fabrics)
        return table.render(target, subnets)


class cmd_subnet(OriginPagedTableCommand):
    """Details of a subnet."""

    def __init__(self, parser):
        super(cmd_subnet, self).__init__(parser)
        parser.add_argument("name", nargs=1, help=(
            "Name of the subnet."))

    def execute(self, origin, options, target):
        try:
            subnet = origin.Subnet.read(options.name[0])
        except CallError as error:
            if error.status == HTTPStatus.NOT_FOUND:
                raise CommandError(
                    "Unable to find subnet %s." % options.name[0])
            else:
                raise
        table = tables.SubnetDetail(fabrics=origin.Fabrics.read())
        return table.render(target, subnet)


def register(parser):
    """Register commands with the given parser."""
    cmd_subnets.register(parser)
    cmd_subnet.register(parser)
