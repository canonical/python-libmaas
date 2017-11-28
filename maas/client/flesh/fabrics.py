"""Commands for fabrics."""

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
from ..utils.async import asynchronous


class cmd_fabrics(OriginPagedTableCommand):
    """List fabrics."""

    def __init__(self, parser):
        super(cmd_fabrics, self).__init__(parser)
        parser.add_argument("--minimal", action="store_true", help=(
            "Output only the fabric names."))

    @asynchronous
    async def load_object_sets(self, origin):
        fabrics = origin.Fabrics.read()
        subnets = origin.Subnets.read()
        return await fabrics, await subnets

    def execute(self, origin, options, target):
        visible_columns = None
        if options.minimal:
            visible_columns = ('name',)
        fabrics, subnets = self.load_object_sets(origin)
        table = tables.FabricsTable(
            visible_columns=visible_columns,
            subnets=subnets)
        return table.render(target, fabrics)


class cmd_fabric(OriginPagedTableCommand):
    """Details of a fabric."""

    def __init__(self, parser):
        super(cmd_fabric, self).__init__(parser)
        parser.add_argument("name", nargs=1, help=(
            "Name of the fabric."))

    @asynchronous
    async def load_object_sets(self, origin):
        fabrics = origin.Fabrics.read()
        subnets = origin.Subnets.read()
        return await fabrics, await subnets

    def execute(self, origin, options, target):
        try:
            fabric = origin.Fabric.read(options.name[0])
        except CallError as error:
            if error.status == HTTPStatus.NOT_FOUND:
                raise CommandError(
                    "Unable to find fabric %s." % options.name[0])
            else:
                raise
        fabrics, subnets = self.load_object_sets(origin)
        table = tables.FabricDetail(fabrics=fabrics, subnets=subnets)
        return table.render(target, fabric)


def register(parser):
    """Register commands with the given parser."""
    cmd_fabrics.register(parser)
    cmd_fabric.register(parser)
