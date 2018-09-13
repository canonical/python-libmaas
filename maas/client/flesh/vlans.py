"""Commands for vlans."""

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


class cmd_vlans(OriginPagedTableCommand):
    """List vlans."""

    def __init__(self, parser):
        super(cmd_vlans, self).__init__(parser)
        parser.add_argument("fabric", nargs=1, help=(
            "Name of the fabric."))
        parser.add_argument("--minimal", action="store_true", help=(
            "Output only the VIDs."))

    @asynchronous
    async def load_object_sets(self, origin):
        fabrics = origin.Fabrics.read()
        subnets = origin.Subnets.read()
        return await fabrics, await subnets

    def execute(self, origin, options, target):
        visible_columns = None
        if options.minimal:
            visible_columns = ('vid',)
        try:
            fabric = origin.Fabric.read(options.fabric[0])
        except CallError as error:
            if error.status == HTTPStatus.NOT_FOUND:
                raise CommandError(
                    "Unable to find fabric %s." % options.fabric[0])
            else:
                raise
        fabrics, subnets = self.load_object_sets(origin)
        table = tables.VlansTable(
            visible_columns=visible_columns,
            fabrics=fabrics, subnets=subnets)
        return table.render(
            target, fabric.vlans)


class cmd_vlan(OriginPagedTableCommand):
    """Details of a vlan."""

    def __init__(self, parser):
        super(cmd_vlan, self).__init__(parser)
        parser.add_argument("fabric", nargs=1, help=(
            "Name of the fabric."))
        parser.add_argument("vid", nargs=1, help=(
            "VID of the VLAN."))

    @asynchronous
    async def load_object_sets(self, origin):
        fabrics = origin.Fabrics.read()
        subnets = origin.Subnets.read()
        return await fabrics, await subnets

    def get_vlan(self, vlans, vid):
        for vlan in vlans:
            if vlan.vid == vid:
                return vlan
        for vlan in vlans:
            if vlan.id == vid:
                return vlan

    def execute(self, origin, options, target):
        try:
            fabric = origin.Fabric.read(options.fabric[0])
        except CallError as error:
            if error.status == HTTPStatus.NOT_FOUND:
                raise CommandError(
                    "Unable to find fabric %s." % options.fabric[0])
            else:
                raise
        vlan_id = options.vid[0]
        if vlan_id != 'untagged':
            try:
                vlan_id = int(vlan_id)
            except ValueError:
                vlan = None
            else:
                vlan = self.get_vlan(fabric.vlans, options.vid[0])
        else:
            vlan = fabric.vlans.get_default()
        if vlan is None:
            raise CommandError(
                "Unable to find VLAN %s on fabric %s." % (
                    options.vid[0], options.fabric[0]))
        fabrics, subnets = self.load_object_sets(origin)
        table = tables.VlanDetail(fabrics=fabrics, subnets=subnets)
        return table.render(target, vlan)


def register(parser):
    """Register commands with the given parser."""
    cmd_vlans.register(parser)
    cmd_vlan.register(parser)
