"""Commands for machines."""

__all__ = [
    "register",
]

import asyncio
import base64
import os

from . import (
    colorized,
    CommandError,
    OriginCommand,
    OriginPagedTableCommand,
    tables,
)
from .. import utils
from ..enum import NodeStatus
from ..utils.async import asynchronous


def validate_file(parser, arg):
    """Validates that `arg` is a valid file."""
    if not os.path.isfile(arg):
        parser.error("%s is not a file." % arg)
    return arg


def base64_file(filepath):
    """Read from `filepath` and convert to base64."""
    with open(filepath, 'rb') as stream:
        return base64.b64encode(stream.read())


class cmd_machines(OriginPagedTableCommand):
    """List all machines."""

    def __init__(self, parser):
        super(cmd_machines, self).__init__(parser)
        parser.add_argument("hostname", nargs='*', help=(
            "Hostname of the machine."))

    def execute(self, origin, options, target):
        hostnames = None
        if options.hostname:
            hostnames = options.hostname

        table = tables.MachinesTable()
        return table.render(target, origin.Machines.read(hostnames=hostnames))


class cmd_allocate(OriginCommand):
    """Allocate an available machine.

    Parameters can be used to allocate a machine that possesses
    certain characteristics.  All the parameters are optional and when
    multiple parameters are provided, they are combined using 'AND'
    semantics.

    Most parameters map to greater than or equal matching (e.g. --cpus 2, will
    match any available machine with 2 or more cpus). MAAS uses a cost
    algorithm to pick the machine based on the parameters that has the lowest
    usage costs to the remaining availablilty of machines.

    Parameter details:

    --disk

      The machine must have a disk present that is at least X GB in size and
      have the specified tags. The format of the parameter is:

      [<label>:]<size>[(<tag>[,<tag>])]

      Size is specified in GB. Tags map to the tags on the disk. When tags are
      included the disk must be at least X GB in size and have the specified
      tags. Label is only used in the resulting acquired machine to provide a
      mapping between the disk parameter and the disk on the machine that
      matched that parameter.

    --interface

      Machines must have one or more interfaces. The format of the parameter
      is:

      [<label>:]<key>=<value>[,<key2>=<value2>[,...]]

      Each key can be one of the following:

      - id: Matches an interface with the specific id
      - fabric: Matches an interface attached to the specified fabric.
      - fabric_class: Matches an interface attached to a fabric
        with the specified class.
      - ip: Matches an interface with the specified IP address
        assigned to it.
      - mode: Matches an interface with the specified mode. (Currently,
        the only supported mode is "unconfigured".)
      - name: Matches an interface with the specified name.
        (For example, "eth0".)
      - hostname: Matches an interface attached to the node with
        the specified hostname.
      - subnet: Matches an interface attached to the specified subnet.
      - space: Matches an interface attached to the specified space.
      - subnet_cidr: Matches an interface attached to the specified
        subnet CIDR. (For example, "192.168.0.0/24".)
      - type: Matches an interface of the specified type. (Valid
        types: "physical", "vlan", "bond", "bridge", or "unknown".)
      - vlan: Matches an interface on the specified VLAN.
      - vid: Matches an interface on a VLAN with the specified VID.
      - tag: Matches an interface tagged with the specified tag.

    --subnet

      The machine must be configured to acquire an address
      in the specified subnet, have a static IP address in the specified
      subnet, or have been observed to DHCP from the specified subnet
      during commissioning time (which implies that it *could* have an
      address on the specified subnet).

      Subnets can be specified by one of the following criteria:

      - <id>: match the subnet by its 'id' field
      - fabric:<fabric-spec>: match all subnets in a given fabric.
      - ip:<ip-address>: Match the subnet containing <ip-address> with
        the with the longest-prefix match.
      - name:<subnet-name>: Match a subnet with the given name.
      - space:<space-spec>: Match all subnets in a given space.
      - vid:<vid-integer>: Match a subnet on a VLAN with the specified
        VID. Valid values range from 0 through 4094 (inclusive). An
        untagged VLAN can be specified by using the value "0".
      - vlan:<vlan-spec>: Match all subnets on the given VLAN.

      Note that (as of this writing), the 'fabric', 'space', 'vid', and
      'vlan' specifiers are only useful for the 'not_spaces' version of
      this constraint, because they will most likely force the query
      to match ALL the subnets in each fabric, space, or VLAN, and thus
      not return any nodes. (This is not a particularly useful behavior,
      so may be changed in the future.)

      If multiple subnets are specified, the machine must be associated
      with all of them.
    """

    def __init__(
            self, parser, with_hostname=True, with_comment=True,
            with_dry_run=True):
        super(cmd_allocate, self).__init__(parser)
        if with_hostname:
            parser.add_argument("hostname", nargs='?', help=(
                "Hostname of the machine."))
        parser.add_argument("--arch", nargs="*", help=(
            "Architecture(s) of the desired machine (e.g. 'i386/generic', "
            "'amd64', 'armhf/highbank', etc.)"))
        parser.add_argument("--cpus", type=int, help=(
            "Minimum number of CPUs for the desired machine."))
        parser.add_argument("--disk", nargs="*", help=(
            "Disk(s) the desired machine must match."))
        parser.add_argument("--fabric", nargs="*", help=(
            "Fabric(s) the desired machine must be connected to."))
        parser.add_argument("--interface", nargs="*", help=(
            "Interface(s) the desired machine must match."))
        parser.add_argument("--memory", type=float, help=(
            "Minimum amount of memory (expressed in MB) for the desired "
            "machine."))
        parser.add_argument("--pod", help=(
            "Pod the desired machine must be located in."))
        parser.add_argument("--pod-type", help=(
            "Pod type the desired machine must be located in."))
        parser.add_argument("--subnet", nargs="*", help=(
            "Subnet(s) the desired machine must be linked to."))
        parser.add_argument("--tag", nargs="*", help=(
            "Tags the desired machine must match."))
        parser.add_argument("--zone", help=(
            "Zone the desired machine must be located in."))
        parser.add_argument("--not-fabric", nargs="*", help=(
            "Fabric(s) the desired machine must NOT be connected to."))
        parser.add_argument("--not-subnet", nargs="*", help=(
            "Subnets(s) the desired machine must NOT be linked to."))
        parser.add_argument("--not-tag", nargs="*", help=(
            "Tags the desired machine must NOT match."))
        parser.add_argument("--not-zone", nargs="*", help=(
            "Zone(s) the desired machine must NOT belong in."))
        parser.other.add_argument("--agent-name", help=(
            "Agent name to attach to the acquire machine."))
        if with_comment:
            parser.other.add_argument("--comment", help=(
                "Comment for the allocate event placed on machine."))
        parser.other.add_argument(
            "--bridge-all", action='store_true', default=None, help=(
                "Automatically create a bridge on all interfaces on the "
                "allocated machine."))
        parser.other.add_argument(
            "--bridge-stp", action='store_true', default=None, help=(
                "Turn spaning tree protocol on or off for the bridges created "
                "with --bridge-all."))
        parser.other.add_argument("--bridge-fd", type=int, help=(
            "Set the forward delay in seconds on the bridges created with "
            "--bridge-all."))
        if with_dry_run:
            parser.other.add_argument(
                "--dry-run", action='store_true', default=None, help=(
                    "Don't actually acquire the machine just return the "
                    "machine that would have been acquired."))

    @asynchronous
    async def allocate(self, origin, options):
        params = utils.remove_None({
            'hostname': options.hostname,
            'architectures': options.arch,
            'cpus': options.cpus,
            'memory': options.memory,
            'fabrics': options.fabric,
            'interfaces': options.interface,
            'pod': options.pod,
            'pod_type': options.pod_type,
            'subnets': options.subnet,
            'tags': options.tag,
            'not_fabrics': options.not_fabric,
            'not_subnets': options.not_subnet,
            'not_zones': options.not_zone,
            'agent_name': options.agent_name,
            'comment': options.comment,
            'bridge_all': options.bridge_all,
            'bridge_stp': options.bridge_stp,
            'bridge_fd': options.bridge_fd,
            'dry_run': getattr(options, 'dry_run', False),
        })
        return await origin.Machines.allocate(**params)

    def execute(self, origin, options):
        with utils.Spinner() as context:
            context.msg = colorized("{automagenta}Allocating{/automagenta}")
            machine = self.allocate(origin, options)
        print(colorized(
            "{autoblue}Allocated{/autoblue} %s") % machine.hostname)


class cmd_deploy(cmd_allocate):
    """Allocate and deploy machine."""

    def __init__(self, parser):
        super(cmd_deploy, self).__init__(
            parser, with_hostname=False, with_comment=False,
            with_dry_run=False)
        parser.add_argument("image", nargs='?', help=(
            "Image to deploy to the machine (e.g. ubuntu/xenial or "
            "just xenial)."))
        parser.add_argument("hostname", nargs='?', help=(
            "Hostname of the machine."))
        parser.add_argument(
            "--hwe-kernel", help=(
                "Hardware enablement kernel to use with the image. Only used "
                "when deploying Ubuntu."))
        parser.add_argument(
            "--user-data", metavar="FILE",
            type=lambda arg: validate_file(parser, arg),
            help=(
                "User data that gets run on the machine once it has "
                "deployed."))
        parser.add_argument(
            "--b64-user-data", metavar="BASE64", help=(
                "Base64 encoded string of the user data that gets run on the "
                "machine once it has deployed."))
        parser.other.add_argument("--comment", help=(
            "Comment for the deploy event placed on machine."))
        parser.other.add_argument(
            "--no-wait", action="store_true", help=(
                "Don't wait for the deploy to complete."))

    @asynchronous
    async def deploy(self, origin, options, context):
        user_data = None
        if options.user_data and options.b64_user_data:
            raise CommandError(
                "Cannot provide both --user-data and --b64-user-data.")
        if options.b64_user_data:
            user_data = options.b64_user_data
        if options.user_data:
            user_data = base64_file(options.user_data)
        deploy_options = utils.remove_None({
            'distro_series': options.image,
            'hwe_kernel': options.hwe_kernel,
            'user_data': user_data,
            'comment': options.comment,
            'wait': False,
        })
        if options.hostname:
            context.msg = colorized(
                "{autoblue}Allocating{/autoblue} %s") % (
                    options.hostname)
        else:
            context.msg = colorized("{autoblue}Searching{/autoblue}")
        machine = await self.allocate(origin, options)
        context.msg = colorized(
            "{autoblue}Deploying{/autoblue} %s") % machine.hostname
        machine = await machine.deploy(**deploy_options)
        if not options.no_wait:
            context.msg = colorized(
                "{autoblue}Deploying{/autoblue} %s on %s") % (
                    machine.distro_series, machine.hostname)
            while machine.status == NodeStatus.DEPLOYING:
                await asyncio.sleep(15)
                await machine.refresh()
        return machine

    def execute(self, origin, options):
        with utils.Spinner() as context:
            machine = self.deploy(origin, options, context)
        if machine.status == NodeStatus.FAILED_DEPLOYMENT:
            raise CommandError(
                "Deployment of %s on %s failed." % (
                    machine.distro_series, machine.hostname))
        elif machine.status == NodeStatus.DEPLOYED:
            print(colorized(
                "{autoblue}Deployed{/autoblue} %s on %s") % (
                    machine.distro_series, machine.hostname))
        elif machine.status == NodeStatus.DEPLOYING:
            print(colorized(
                "{autoblue}Deploying{/autoblue} %s on %s") % (
                    machine.distro_series, machine.hostname))
        else:
            raise CommandError(
                "Machine %s transitioned to an unexpected state of %s." % (
                    machine.hostname, machine.status_name))


class cmd_release(OriginCommand):
    """Release machine."""

    def __init__(self, parser):
        super(cmd_release, self).__init__(parser)
        parser.add_argument("hostname", nargs="*", help=(
            "Hostname of the machine to release."))
        parser.add_argument('--all', action='store_true', help=(
            "Release all machines owned by you."))
        parser.add_argument('--comment', help=(
            "Comment for the release event placed on machine."))
        parser.add_argument('--erase', action='store_true', help=(
            "Erase the disk when releasing."))
        parser.add_argument('--secure-erase', action='store_true', help=(
            "Use the drives secure erase feature if available on the disk."))
        parser.add_argument('--quick-erase', action='store_true', help=(
            "Wipe the just the beginning and end of the disk. "
            "This is not secure."))
        parser.other.add_argument(
            "--no-wait", action="store_true", help=(
                "Don't wait for the release to complete."))

    @asynchronous
    async def release(self, machines, params):

        async def _release(machine, params):
            """Prints the errors as the occur."""
            try:
                await machine.release(**params)
            except Exception as exc:
                print(colorized("{autored}Error:{/autored} %s") % str(exc))
                raise
            else:
                print(colorized(
                    "{autogreen}Released{/autogreen} %s") % machine.hostname)

        results = await asyncio.gather(*[
            _release(machine, params)
            for machine in machines
        ], return_exceptions=True)
        failures = [
            result
            for result in results
            if isinstance(result, Exception)
        ]
        if len(failures) > 0:
            return 1
        return 0

    def execute(self, origin, options):
        if options.hostname and options.all:
            raise CommandError("Cannot pass both hostname and --all.")
        if not options.hostname and not options.all:
            raise CommandError("Missing parameter hostname or --all.")
        params = utils.remove_None({
            'erase': options.erase,
            'secure_erase': options.secure_erase,
            'quick_erase': options.quick_erase,
            'wait': False if options.no_wait else True,
        })
        if options.all:
            me = origin.Users.whoami()
            machines = origin.Machines.read()
            machines = [
                machine
                for machine in machines
                if (machine.owner is not None and
                    machine.owner.username == me.username and (
                        machine.status not in [
                            NodeStatus.COMMISSIONING, NodeStatus.TESTING]))
            ]
        else:
            hostnames = {
                hostname: True
                for hostname in options.hostname
            }
            machines = origin.Machines.read(hostnames=hostnames)
            machines = [
                machine
                for machine in machines
                if hostnames.pop(machine.hostname, False)
            ]
            if len(hostnames) > 0:
                raise CommandError(
                    "Unable to find %s %s." % (
                        "machines" if len(hostnames) > 1 else "machine",
                        ','.join(hostnames)))
        if len(machines) == 0:
            return 0
        with utils.Spinner() as context:
            if len(machines) == 1:
                msg = machines[0].hostname
            elif len(machines) == 2:
                msg = "%s and %s" % (
                    machines[0].hostname, machines[1].hostname)
            else:
                msg = "%s machines" % len(machines)
            context.msg = colorized(
                "{autoblue}Releasing{/autoblue} %s" % msg)
            return self.release(machines, params)


def register(parser):
    """Register commands with the given parser."""
    cmd_machines.register(parser)
    cmd_allocate.register(parser)
    cmd_deploy.register(parser)
    cmd_release.register(parser)
