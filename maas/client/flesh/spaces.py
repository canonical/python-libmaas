"""Commands for spaces."""

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


class cmd_spaces(OriginPagedTableCommand):
    """List spaces."""

    def __init__(self, parser):
        super(cmd_spaces, self).__init__(parser)
        parser.add_argument("--minimal", action="store_true", help=(
            "Output only the space names."))

    @asynchronous
    async def load_object_sets(self, origin):
        spaces = origin.Spaces.read()
        fabrics = origin.Fabrics.read()
        subnets = origin.Subnets.read()
        return await spaces, await fabrics, await subnets

    def execute(self, origin, options, target):
        visible_columns = None
        if options.minimal:
            visible_columns = ('name',)
        spaces, fabrics, subnets = self.load_object_sets(origin)
        table = tables.SpacesTable(
            visible_columns=visible_columns, fabrics=fabrics, subnets=subnets)
        return table.render(target, spaces)


class cmd_space(OriginPagedTableCommand):
    """Details of a space."""

    def __init__(self, parser):
        super(cmd_space, self).__init__(parser)
        parser.add_argument("name", nargs=1, help=(
            "Name of the space."))

    @asynchronous
    async def load_object_sets(self, origin):
        fabrics = origin.Fabrics.read()
        subnets = origin.Subnets.read()
        return await fabrics, await subnets

    def execute(self, origin, options, target):
        try:
            space = origin.Space.read(options.name[0])
        except CallError as error:
            if error.status == HTTPStatus.NOT_FOUND:
                raise CommandError(
                    "Unable to find space %s." % options.name[0])
            else:
                raise
        fabrics, subnets = self.load_object_sets(origin)
        table = tables.SpaceDetail(fabrics=fabrics, subnets=subnets)
        return table.render(target, space)


def register(parser):
    """Register commands with the given parser."""
    cmd_spaces.register(parser)
    cmd_space.register(parser)
