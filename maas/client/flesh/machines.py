"""Commands for machines."""

__all__ = [
    "register",
]

import asyncio
import base64
import os
import re
import subprocess
import sys
import time

from . import (
    colorized,
    CommandError,
    OriginCommand,
    OriginPagedTableCommand,
    tables,
    yes_or_no
)
from .. import utils
from ..bones import CallError
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
    """List machines."""

    def __init__(self, parser):
        super(cmd_machines, self).__init__(parser)
        parser.add_argument("hostname", nargs='*', help=(
            "Hostname of the machine."))
        parser.add_argument("--owned", action="store_true", help=(
            "Show only machines owned by you."))

    def execute(self, origin, options, target):
        hostnames = None
        if options.hostname:
            hostnames = options.hostname
        machines = origin.Machines.read(hostnames=hostnames)
        if options.owned:
            me = origin.Users.whoami()
            machines = origin.Machines([
                machine
                for machine in machines
                if machine.owner is not None and
                machine.owner.username == me.username
            ])
        table = tables.MachinesTable()
        return table.render(target, machines)


class cmd_machine(OriginPagedTableCommand):
    """Details of a machine."""

    def __init__(self, parser):
        super(cmd_machine, self).__init__(parser)
        parser.add_argument("hostname", nargs=1, help=(
            "Hostname of the machine."))

    def execute(self, origin, options, target):
        machines = origin.Machines.read(hostnames=options.hostname)
        if len(machines) == 0:
            raise CommandError(
                "Unable to find machine %s." % options.hostname[0])
        machine = machines[0]
        table = tables.MachineDetail()
        return table.render(target, machine)


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
                "Reason for allocating the machine."))
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
        if options.hostname:
            me = await origin.Users.whoami()
            machines = await origin.Machines.read(hostnames=[options.hostname])
            if len(machines) == 0:
                raise CommandError(
                    "Unable to find machine %s." % options.hostname)
            machine = machines[0]
            if (machine.status == NodeStatus.ALLOCATED and
                    machine.owner.username == me.username):
                return False, machine
            elif machine.status != NodeStatus.READY:
                raise CommandError(
                    "Unable to allocate machine %s." % options.hostname)
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
        machine = await origin.Machines.allocate(**params)
        if options.hostname and machine.hostname != options.hostname:
            await machine.release()
            raise CommandError(
                "MAAS failed to allocate machine %s; "
                "instead it allocated %s." % (
                    options.hostname, machine.hostname))
        return True, machine

    def execute(self, origin, options):
        with utils.Spinner() as context:
            context.msg = colorized("{automagenta}Allocating{/automagenta}")
            _, machine = self.allocate(origin, options)
        print(colorized(
            "{autoblue}Allocated{/autoblue} %s") % machine.hostname)


class MachineWorkMixin:
    """Mixin that helps with performing actions across a set of machinse."""

    @asynchronous
    async def _async_perform_action(
            self, context, action, machines, params,
            progress_title, success_title):

        def _update_msg(remaining):
            """Update the spinner message."""
            if len(remaining) == 1:
                msg = remaining[0].hostname
            elif len(remaining) == 2:
                msg = "%s and %s" % (
                    remaining[0].hostname, remaining[1].hostname)
            else:
                msg = "%s machines" % len(remaining)
            context.msg = colorized(
                "{autoblue}%s{/autoblue} %s" % (progress_title, msg))

        async def _perform(machine, params, remaining):
            """Updates the messages as actions complete."""
            try:
                await getattr(machine, action)(**params)
            except Exception as exc:
                remaining.remove(machine)
                _update_msg(remaining)
                context.print(
                    colorized("{autored}Error:{/autored} %s") % str(exc))
                raise
            else:
                remaining.remove(machine)
                _update_msg(remaining)
                context.print(colorized(
                    "{autogreen}%s{/autogreen} %s") % (
                        success_title, machine.hostname))

        _update_msg(machines)
        results = await asyncio.gather(*[
            _perform(machine, params, machines)
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

    def perform_action(
            self, action, machines, params, progress_title, success_title):
        """Perform the action on the set of machines."""
        if len(machines) == 0:
            return 0
        with utils.Spinner() as context:
            return self._async_perform_action(
                context, action, list(machines), params,
                progress_title, success_title)

    def get_machines(self, origin, hostnames):
        """Return a set of machines based on `hostnames`.

        Any hostname that is not found will result in an error.
        """
        hostnames = {
            hostname: True
            for hostname in hostnames
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
        return machines


class MachineSSHMixin:
    """Mixin that provides the ability to SSH."""

    def add_ssh_options(self, parser):
        """Add the SSH arguments to the `parser`."""
        parser.add_argument(
            "--username", metavar='USER', help=(
                "Username for the SSH connection."))
        parser.add_argument(
            "--boot-only", action="store_true", help=(
                "Only use the IP addresses on the machine's boot interface."))

    def get_ip_addresses(self, machine, *, boot_only=False, discovered=False):
        """Return all IP address for `machine`.

        IP address from `boot_interface` come first.
        """
        boot_ips = [
            link.ip_address
            for link in machine.boot_interface.links
            if link.ip_address
        ]
        if boot_only:
            if boot_ips:
                return boot_ips
            elif discovered:
                return [
                    link.ip_address
                    for link in machine.boot_interface.discovered
                    if link.ip_address
                ]
            else:
                return []
        else:
            other_ips = [
                link.ip_address
                for interface in machine.interfaces
                for link in interface.links
                if (interface.id != machine.boot_interface.id and
                    link.ip_address)
            ]
            ips = boot_ips + other_ips
            if ips:
                return ips
            elif discovered:
                return [
                    link.ip_address
                    for link in machine.boot_interface.discovered
                    if link.ip_address
                ] + [
                    link.ip_address
                    for interface in machine.interfaces
                    for link in interface.discovered
                    if (interface.id != machine.boot_interface.id and
                        link.ip_address)
                ]
            else:
                return []

    @asynchronous
    async def _async_get_sshable_ips(self, ip_addresses):
        """Return list of all IP address that could be pinged."""

        async def _async_ping(ip_address):
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip_address, 22), timeout=5)
            except (OSError, TimeoutError):
                return None
            try:
                line = await reader.readline()
            finally:
                writer.close()
            if line.startswith(b'SSH-'):
                return ip_address

        ssh_ips = await asyncio.gather(*[
            _async_ping(ip_address)
            for ip_address in ip_addresses
        ])
        return [
            ip_address
            for ip_address in ssh_ips
            if ip_address is not None
        ]

    def _check_ssh(self, *args):
        """Check if SSH connection can be made to IP with username."""
        ssh = subprocess.Popen(
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        ssh.wait()
        return ssh.returncode == 0

    def _determine_username(self, ip):
        """SSH in as root and determine the username."""
        ssh = subprocess.Popen([
            "ssh",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "StrictHostKeyChecking=no",
            "root@%s" % ip],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL)
        first_line = ssh.stdout.readline()
        ssh.kill()
        ssh.wait()
        if first_line:
            match = re.search(
                r"Please login as the user \"(\w+)\" rather than "
                r"the user \"root\".", first_line.decode('utf-8'))
            if match:
                return match.groups()[0]
        else:
            return None

    def ssh(
            self, machine, *,
            username=None, command=None, boot_only=False, discovered=False,
            wait=300):
        """SSH into `machine`."""
        start_time = time.monotonic()
        with utils.Spinner() as context:
            context.msg = colorized(
                "{autoblue}Determining{/autoblue} best IP for %s" % (
                    machine.hostname))
            ip_addresses = self.get_ip_addresses(
                machine, boot_only=boot_only, discovered=discovered)
            if len(ip_addresses) > 0:
                pingable_ips = self._async_get_sshable_ips(ip_addresses)
                while (len(pingable_ips) == 0 and
                        (time.monotonic() - start_time) < wait):
                    time.sleep(5)
                    pingable_ips = self._async_get_sshable_ips(ip_addresses)
                if len(pingable_ips) == 0:
                    raise CommandError(
                        "No IP addresses on %s can be reached." % (
                            machine.hostname))
                else:
                    ip = pingable_ips[0]
            else:
                raise CommandError(
                    "%s has no IP addresses." % machine.hostname)

            if username is None:
                context.msg = colorized(
                    "{autoblue}Determining{/autoblue} SSH username on %s" % (
                        machine.hostname))
                username = self._determine_username(ip)
                while (username is None and
                        (time.monotonic() - start_time) < wait):
                    username = self._determine_username(ip)
                if username is None:
                    raise CommandError(
                        "Failed to determine the username for SSH.")

            conn_str = "%s@%s" % (username, ip)
            args = [
                "ssh",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "StrictHostKeyChecking=no",
                conn_str
            ]

            context.msg = colorized(
                "{automagenta}Waiting{/automagenta} for SSH on %s" % (
                    machine.hostname))
            check_args = args + ["echo"]
            connectable = self._check_ssh(*check_args)
            while not connectable and (time.monotonic() - start_time) < wait:
                time.sleep(5)
                connectable = self._check_ssh(*check_args)
            if not connectable:
                raise CommandError(
                    "SSH never started on %s using IP %s." % (
                        machine.hostname, ip))

        if command is not None:
            args.append(command)
        ssh = subprocess.Popen(
            args, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        ssh.wait()
        return ssh.returncode


class MachineReleaseMixin(MachineWorkMixin):
    """Mixin that provide releasing machines."""

    def add_release_options(self, parser):
        parser.add_argument('--erase', action='store_true', help=(
            "Erase the disk when releasing."))
        parser.add_argument('--secure-erase', action='store_true', help=(
            "Use the drives secure erase feature if available on the disk."))
        parser.add_argument('--quick-erase', action='store_true', help=(
            "Wipe the just the beginning and end of the disk. "
            "This is not secure."))

    def get_release_params(self, options):
        return utils.remove_None({
            'erase': options.erase,
            'secure_erase': options.secure_erase,
            'quick_erase': options.quick_erase,
        })

    def release(self, machines, params):
        wait = params.get('wait', True)
        return self.perform_action(
            "release", machines, params, "Releasing",
            "Released" if wait else "Releasing")


class cmd_deploy(cmd_allocate, MachineSSHMixin, MachineReleaseMixin):
    """Allocate and deploy machine.

    See `help allocate` for more details on the allocation parameters.
    """

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
        parser.add_argument(
            "--ssh", action="store_true", help=(
                "SSH into the machine once its deployed."))
        self.add_ssh_options(parser)
        parser.add_argument(
            "--release-on-exit", action="store_true", help=(
                "Release the machine once the SSH connection is closed. "
                "Only used with --ssh is provided."))
        self.add_release_options(parser)
        parser.other.add_argument("--comment", help=(
            "Reason for deploying the machine."))
        parser.other.add_argument(
            "--no-wait", action="store_true", help=(
                "Don't wait for the deploy to complete."))

    def _get_deploy_options(self, options):
        """Return the deployment options based on command line."""
        user_data = None
        if options.user_data and options.b64_user_data:
            raise CommandError(
                "Cannot provide both --user-data and --b64-user-data.")
        if options.b64_user_data:
            user_data = options.b64_user_data
        if options.user_data:
            user_data = base64_file(options.user_data).decode("ascii")
        return utils.remove_None({
            'distro_series': options.image,
            'hwe_kernel': options.hwe_kernel,
            'user_data': user_data,
            'comment': options.comment,
            'wait': False,
        })

    def _handle_abort(self, machine, allocated):
        """Handle the user aborting mid deployment."""
        abort = yes_or_no("Abort deployment?")
        if abort:
            with utils.Spinner() as context:
                if allocated:
                    context.msg = colorized(
                        "{autoblue}Releasing{/autoblue} %s") % (
                            machine.hostname)
                    machine.release()
                    context.print(colorized(
                        "{autoblue}Released{/autoblue} %s") % (
                            machine.hostname))
                else:
                    context.msg = colorized(
                        "{autoblue}Aborting{/autoblue} %s") % (
                            machine.hostname)
                    machine.abort()
                    context.print(colorized(
                        "{autoblue}Aborted{/autoblue} %s") % (
                            machine.hostname))

    def execute(self, origin, options):
        deploy_options = self._get_deploy_options(options)
        allocated, machine = False, None
        try:
            with utils.Spinner() as context:
                if options.hostname:
                    context.msg = colorized(
                        "{autoblue}Allocating{/autoblue} %s") % (
                            options.hostname)
                else:
                    context.msg = colorized("{autoblue}Searching{/autoblue}")
                allocated, machine = self.allocate(origin, options)
                context.msg = colorized(
                    "{autoblue}Deploying{/autoblue} %s") % machine.hostname
                try:
                    machine = machine.deploy(**deploy_options)
                except CallError:
                    if allocated:
                        machine.release()
                    raise
                if not options.no_wait:
                    context.msg = colorized(
                        "{autoblue}Deploying{/autoblue} %s on %s") % (
                            machine.distro_series, machine.hostname)
                    while machine.status == NodeStatus.DEPLOYING:
                        time.sleep(15)
                        machine.refresh()
        except KeyboardInterrupt:
            if sys.stdout.isatty() and machine is not None:
                self._handle_abort(machine, allocated)
            raise

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

        if options.ssh:
            machine.refresh()
            code = self.ssh(
                machine, username=options.username,
                boot_only=options.boot_only)
            if code == 0 and options.release_on_exit:
                release_params = self.get_release_params(options)
                release_params["wait"] = True
                self.release([machine], release_params)


class cmd_commission(OriginCommand, MachineSSHMixin, MachineWorkMixin):
    """Commission machine."""

    def __init__(self, parser):
        super(cmd_commission, self).__init__(parser)
        parser.add_argument("hostname", nargs="*", help=(
            "Hostname of the machine to commission."))
        parser.add_argument("--all", action="store_true", help=(
            "Commission all machines that can be commissioned."))
        parser.add_argument("--new", action="store_true", help=(
            "Commission all new machines."))
        parser.add_argument("--skip-networking", action="store_true", help=(
            "Skip machine network discovery, keeping the current interface "
            "configuration for the machine."))
        parser.add_argument("--skip-storage", action="store_true", help=(
            "Skip machine storage discovery, keeping the current storage "
            "configuration for the machine."))
        parser.add_argument("--scripts", nargs="*", metavar="SCRIPT", help=(
            "Run only the selected commissioning scripts."))
        parser.add_argument("--ssh", action="store_true", help=(
            "SSH into the machine during commissioning."))
        self.add_ssh_options(parser)
        parser.other.add_argument(
            "--no-wait", action="store_true", help=(
                "Don't wait for the commisisoning to complete."))

    def execute(self, origin, options):
        if options.hostname and options.all:
            raise CommandError("Cannot pass both hostname and --all.")
        if options.hostname and options.new:
            raise CommandError("Cannot pass both hostname and --new.")
        if not options.hostname and not options.all and not options.new:
            raise CommandError("Missing parameter hostname, --all, or --new.")
        if (options.ssh and
                (len(options.hostname) > 1 or options.all or options.new)):
            raise CommandError(
                "--ssh can only be used when commissioning one machine.")
        if options.all:
            machines = origin.Machines.read()
            machines = [
                machine
                for machine in machines
                if machine.status in [
                    NodeStatus.NEW, NodeStatus.READY,
                    NodeStatus.FAILED_COMMISSIONING]
            ]
        elif options.new:
            machines = origin.Machines.read()
            machines = [
                machine
                for machine in machines
                if machine.status == NodeStatus.NEW
            ]
        else:
            machines = self.get_machines(origin, options.hostname)
        params = utils.remove_None({
            'enable_ssh': options.ssh,
            'skip_networking': options.skip_networking,
            'skip_storage': options.skip_storage,
            'commissioning_scripts': options.scripts,
            'wait': False if options.no_wait else True
        })
        try:
            rc = self.perform_action(
                "commission", machines, params,
                "Commissioning",
                "Commissioning" if options.no_wait else "Commissioned")
        except KeyboardInterrupt:
            if sys.stdout.isatty():
                abort = yes_or_no("Abort commissioning?")
                if abort:
                    return self.perform_action(
                        "abort", machines, {}, "Aborting", "Aborted")
                else:
                    return 1
        if rc == 0 and len(machines) > 0 and options.ssh:
            machine = machines[0]
            machine.refresh()
            rc = self.ssh(
                machine, username=options.username,
                boot_only=options.boot_only, discovered=True)
            if rc == 0:
                return self.perform_action(
                    "power_off", [machine], {}, "Powering off", "Powered off")
        return rc


class cmd_release(OriginCommand, MachineReleaseMixin):
    """Release machine."""

    def __init__(self, parser):
        super(cmd_release, self).__init__(parser)
        parser.add_argument("hostname", nargs="*", help=(
            "Hostname of the machine to release."))
        parser.add_argument('--all', action='store_true', help=(
            "Release all machines owned by you."))
        parser.add_argument('--comment', help=(
            "Reason for releasing the machine."))
        self.add_release_options(parser)
        parser.other.add_argument(
            "--no-wait", action="store_true", help=(
                "Don't wait for the release to complete."))

    def execute(self, origin, options):
        if options.hostname and options.all:
            raise CommandError("Cannot pass both hostname and --all.")
        if not options.hostname and not options.all:
            raise CommandError("Missing parameter hostname or --all.")
        params = self.get_release_params(options)
        params['wait'] = False if options.no_wait else True
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
            machines = self.get_machines(origin, options.hostname)
        return self.release(machines, params)


class cmd_abort(OriginCommand, MachineWorkMixin):
    """Abort machine's current action."""

    def __init__(self, parser):
        super(cmd_abort, self).__init__(parser)
        parser.add_argument("hostname", nargs="+", help=(
            "Hostname of the machine to abort the action."))
        parser.add_argument('--comment', help=(
            "Reason for aborting the action."))

    def execute(self, origin, options):
        params = utils.remove_None({
            "comment": options.comment,
        })
        machines = self.get_machines(origin, options.hostname)
        return self.perform_action(
            "abort", machines, params, "Aborting", "Aborted")


class cmd_mark_fixed(OriginCommand, MachineWorkMixin):
    """Mark machine fixed."""

    def __init__(self, parser):
        super(cmd_mark_fixed, self).__init__(parser)
        parser.add_argument("hostname", nargs="+", help=(
            "Hostname of the machine to mark fixed."))
        parser.add_argument('--comment', help=(
            "Reason for marking the machine fixed."))

    def execute(self, origin, options):
        machines = self.get_machines(origin, options.hostname)
        return self.perform_action(
            "mark_fixed", machines, {}, "Marking fixed", "Marked fixed")


class cmd_mark_broken(OriginCommand, MachineWorkMixin):
    """Mark machine broken."""

    def __init__(self, parser):
        super(cmd_mark_broken, self).__init__(parser)
        parser.add_argument("hostname", nargs="+", help=(
            "Hostname of the machine to mark broken."))
        parser.add_argument('--comment', help=(
            "Reason for marking the machine broken."))

    def execute(self, origin, options):
        machines = self.get_machines(origin, options.hostname)
        return self.perform_action(
            "mark_broken", machines, {}, "Marking broken", "Marked broken")


class cmd_ssh(OriginCommand, MachineWorkMixin, MachineSSHMixin):
    """SSH into a machine."""

    def __init__(self, parser):
        super(cmd_ssh, self).__init__(parser)
        parser.add_argument("hostname", nargs=1, help=(
            "Hostname of the machine to SSH to."))
        parser.add_argument("command", nargs="?", default=None, help=(
            "Hostname of the machine to SSH to."))
        self.add_ssh_options(parser)

    def execute(self, origin, options):
        machine = self.get_machines(origin, options.hostname)[0]
        return self.ssh(
            machine, username=options.username,
            command=options.command, boot_only=options.boot_only)


class cmd_power_on(OriginCommand, MachineWorkMixin):
    """Power on machine."""

    def __init__(self, parser):
        super(cmd_power_on, self).__init__(parser)
        parser.add_argument("hostname", nargs="+", help=(
            "Hostname of the machine to power on."))
        parser.add_argument('--comment', help=(
            "Reason for powering the machine on."))

    def execute(self, origin, options):
        machines = self.get_machines(origin, options.hostname)
        return self.perform_action(
            "power_on", machines, {}, "Powering on", "Powered on")


class cmd_power_off(OriginCommand, MachineWorkMixin):
    """Power off machine."""

    def __init__(self, parser):
        super(cmd_power_off, self).__init__(parser)
        parser.add_argument("hostname", nargs="+", help=(
            "Hostname of the machine to power off."))
        parser.add_argument('--comment', help=(
            "Reason for powering the machine off."))

    def execute(self, origin, options):
        machines = self.get_machines(origin, options.hostname)
        return self.perform_action(
            "power_off", machines, {}, "Powering off", "Powered off")


def register(parser):
    """Register commands with the given parser."""
    cmd_machines.register(parser)
    cmd_machine.register(parser)
    cmd_allocate.register(parser)
    cmd_deploy.register(parser)
    cmd_commission.register(parser)
    cmd_release.register(parser)
    cmd_abort.register(parser)
    cmd_mark_fixed.register(parser)
    cmd_mark_broken.register(parser)
    cmd_power_off.register(parser)
    cmd_power_on.register(parser)
    cmd_ssh.register(parser)
