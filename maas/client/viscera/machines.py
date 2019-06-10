"""Objects for machines."""

__all__ = [
    "Machine",
    "Machines",
]

import asyncio
import base64
import bson
import json
from http import HTTPStatus
import typing

from . import (
    check,
    check_optional,
    ObjectField,
    ObjectFieldRelated,
    ObjectFieldRelatedSet,
    to,
)
from .fabrics import Fabric
from .interfaces import Interface
from .nodes import (
    Node,
    Nodes,
    NodesType,
    NodeTypeMeta,
)
from .pods import Pod
from .subnets import Subnet
from .zones import Zone
from ..bones import CallError
from ..enum import (
    NodeStatus,
    PowerState,
    PowerStopMode
)
from ..errors import (
    MAASException,
    OperationNotAllowed,
    PowerError
)
from ..utils import remove_None
from ..utils.diff import calculate_dict_diff


FabricParam = typing.Union[str, int, Fabric]
InterfaceParam = typing.Union[str, int, Interface]
SubnetParam = typing.Union[str, int, Subnet]
ZoneParam = typing.Union[str, Zone]


def get_param_arg(param, idx, klass, arg, attr='id'):
    """Return the correct value for a fabric from `arg`."""
    if isinstance(arg, klass):
        return getattr(arg, attr)
    elif isinstance(arg, (int, str)):
        return arg
    else:
        raise TypeError(
            "%s[%d] must be int, str, or %s, not %s" % (
                param, idx, klass.__name__, type(arg).__name__))


class MachinesType(NodesType):
    """Metaclass for `Machines`."""

    async def create(
            cls, architecture: str, mac_addresses: typing.Sequence[str],
            power_type: str,
            power_parameters: typing.Mapping[str, typing.Any] = None, *,
            subarchitecture: str = None, min_hwe_kernel: str = None,
            hostname: str = None, domain: typing.Union[int, str] = None):
        """
        Create a new machine.

        :param architecture: The architecture of the machine (required).
        :type architecture: `str`
        :param mac_addresses: The MAC address of the machine (required).
        :type mac_addresses: sequence of `str`
        :param power_type: The power type of the machine (required).
        :type power_type: `str`
        :param power_parameters: The power parameters for the machine
            (optional).
        :type power_parameters: mapping of `str` to any value.
        :param subarchitecture: The subarchitecture of the machine (optional).
        :type subarchitecture: `str`
        :param min_hwe_kernel: The minimal HWE kernel for the machine
            (optional).
        :param hostname: The hostname for the machine (optional).
        :type hostname: `str`
        :param domain: The domain for the machine (optional).
        :type domain: `int` or `str`
        """
        params = {
            "architecture": architecture,
            "mac_addresses": mac_addresses,
            "power_type": power_type,
        }
        if power_parameters is not None:
            params["power_parameters"] = json.dumps(
                power_parameters, sort_keys=True)
        if subarchitecture is not None:
            params["subarchitecture"] = subarchitecture
        if min_hwe_kernel is not None:
            params["min_hwe_kernel"] = min_hwe_kernel
        if hostname is not None:
            params["hostname"] = hostname
        if domain is not None:
            params["domain"] = domain
        return cls._object(await cls._handler.create(**params))

    async def allocate(
            cls, *,
            hostname: str = None,
            architectures: typing.Sequence[str] = None,
            cpus: int = None,
            fabrics: typing.Sequence[FabricParam] = None,
            interfaces: typing.Sequence[InterfaceParam] = None,
            memory: float = None,
            pod: typing.Union[str, Pod] = None,
            not_pod: typing.Union[str, Pod] = None,
            pod_type: str = None,
            not_pod_type: str = None,
            storage: typing.Sequence[str] = None,
            subnets: typing.Sequence[SubnetParam] = None,
            tags: typing.Sequence[str] = None,
            zone: typing.Union[str, Zone] = None,
            not_fabrics: typing.Sequence[FabricParam] = None,
            not_subnets: typing.Sequence[SubnetParam] = None,
            not_tags: typing.Sequence[str] = None,
            not_zones: typing.Sequence[ZoneParam] = None,
            agent_name: str = None, comment: str = None,
            bridge_all: bool = None, bridge_stp: bool = None,
            bridge_fd: int = None, dry_run: bool = None, verbose: bool = None):
        """
        Allocate a machine.

        :param hostname: The hostname to match.
        :type hostname: `str`
        :param architectures: The architecture(s) to match.
        :type architectures: sequence of `str`
        :param cpus: The minimum number of CPUs to match.
        :type cpus: `int`
        :param fabrics: The connected fabrics to match.
        :type fabrics: sequence of either `str`, `int`, or `Fabric`
        :param interfaces: The interfaces to match.
        :type interfaces: sequence of either `str`, `int`, or `Interface`
        :param memory: The minimum amount of RAM to match in MiB.
        :type memory: `int`
        :param pod: The pod to allocate the machine from.
        :type pod: `str`
        :param not_pod: Pod the machine must not be located in.
        :type not_pod: `str`
        :param pod_type: The type of pod to allocate the machine from.
        :type pod_type: `str`
        :param not_pod_type: Pod type the machine must not be located in.
        :type not_pod_type: `str`
        :param subnets: The subnet(s) the desired machine must be linked to.
        :type subnets: sequence of `str` or `int` or `Subnet`
        :param storage: The storage contraint to match.
        :type storage: `str`
        :param tags: The tags to match, as a sequence.
        :type tags: sequence of `str`
        :param zone: The zone the desired machine must belong to.
        :type zone: `str` or `Zone`
        :param not_fabrics: The fabrics the machine must NOT be connected to.
        :type not_fabrics: sequence of either `str`, `int`, or `Fabric`
        :param not_subnets: The subnet(s) the desired machine must NOT be
            linked to.
        :type not_subnets: sequence of `str` or `int` or `Subnet`
        :param not_zones: The zone(s) the desired machine must NOT in.
        :type not_zones: sequence of `str` or `Zone`
        :param agent_name: Agent name to attach to the acquire machine.
        :type agent_name: `str`
        :param comment: Comment for the allocate event placed on machine.
        :type comment: `str`
        :param bridge_all: Automatically create a bridge on all interfaces
            on the allocated machine.
        :type bridge_all: `bool`
        :param bridge_stp: Turn spaning tree protocol on or off for the
            bridges created with bridge_all.
        :type bridge_stp: `bool`
        :param bridge_fd: Set the forward delay in seconds on the bridges
            created with bridge_all.
        :type bridge_fd: `int`
        :param dry_run: Don't actually acquire the machine just return the
            machine that would have been acquired.
        :type dry_run: `bool`
        :param verbose: Indicate that the user would like additional verbosity
            in the constraints_by_type field (each constraint will be prefixed
            by `verbose_`, and contain the full data structure that indicates
            which machine(s) matched).
        :type verbose: `bool`
        """
        params = remove_None({
            'name': hostname,
            'arch': architectures,
            'cpu_count': str(cpus) if cpus else None,
            'mem': str(memory) if memory else None,
            'pod_type': pod_type,
            'not_pod_type': not_pod_type,
            'storage': storage,
            'tags': tags,
            'not_tags': not_tags,
            'agent_name': agent_name,
            'comment': comment,
            'bridge_all': bridge_all,
            'bridge_stp': bridge_stp,
            'bridge_fd': bridge_fd,
            'dry_run': dry_run,
            'verbose': verbose,
        })
        if fabrics is not None:
            params["fabrics"] = [
                get_param_arg('fabrics', idx, Fabric, fabric)
                for idx, fabric in enumerate(fabrics)
            ]
        if interfaces is not None:
            params["interfaces"] = [
                get_param_arg('interfaces', idx, Interface, nic)
                for idx, nic in enumerate(interfaces)
            ]
        if pod is not None:
            if isinstance(pod, Pod):
                params["pod"] = pod.name
            elif isinstance(pod, str):
                params["pod"] = pod
            else:
                raise TypeError(
                    "pod must be a str or Pod, not %s" % type(pod).__name__)
        if not_pod is not None:
            if isinstance(not_pod, Pod):
                params["not_pod"] = not_pod.name
            elif isinstance(not_pod, str):
                params["not_pod"] = not_pod
            else:
                raise TypeError(
                    "not_pod must be a str or Pod, not %s" %
                    type(not_pod).__name__)
        if subnets is not None:
            params["subnets"] = [
                get_param_arg('subnets', idx, Subnet, subnet)
                for idx, subnet in enumerate(subnets)
            ]
        if zone is not None:
            if isinstance(zone, Zone):
                params["zone"] = zone.name
            elif isinstance(zone, str):
                params["zone"] = zone
            else:
                raise TypeError(
                    "zone must be a str or Zone, not %s" % type(zone).__name__)
        if not_fabrics is not None:
            params["not_fabrics"] = [
                get_param_arg('not_fabrics', idx, Fabric, fabric)
                for idx, fabric in enumerate(not_fabrics)
            ]
        if not_subnets is not None:
            params["not_subnets"] = [
                get_param_arg('not_subnets', idx, Subnet, subnet)
                for idx, subnet in enumerate(not_subnets)
            ]
        if not_zones is not None:
            params["not_in_zones"] = [
                get_param_arg('not_zones', idx, Zone, zone, attr='name')
                for idx, zone in enumerate(not_zones)
            ]
        try:
            data = await cls._handler.allocate(**params)
        except CallError as error:
            if error.status == HTTPStatus.CONFLICT:
                message = "No machine matching the given criteria was found."
                raise MachineNotFound(message) from error
            else:
                raise
        else:
            return cls._object(data)

    async def get_power_parameters_for(
            cls, system_ids: typing.Sequence[str]):
        """
        Get a list of power parameters for specified systems.
        *WARNING*: This method is considered 'alpha' and may be modified
        in future.

        :param system_ids: The system IDs to get power parameters for
        """
        if len(system_ids) == 0:
            return {}
        data = await cls._handler.power_parameters(id=system_ids)
        return data


class MachineNotFound(Exception):
    """
    Machine was not found.

    Not a MAASException because this doesn't occur in the context of
    a specific object.
    """


class RescueModeFailure(MAASException):
    """Machine failed to perform a Rescue mode transition."""


class FailedCommissioning(MAASException):
    """Machine failed to commission."""


class FailedTesting(MAASException):
    """Machine failed testing."""


class FailedDeployment(MAASException):
    """Machine failed to deploy."""


class FailedReleasing(MAASException):
    """Machine failed to release."""


class FailedDiskErasing(MAASException):
    """Machine failed to erase disk when releasing."""


class Machines(Nodes, metaclass=MachinesType):
    """The set of machines stored in MAAS."""


class MachineType(NodeTypeMeta):
    """Metaclass for `Machine`."""

    async def read(cls, system_id):
        data = await cls._handler.read(system_id=system_id)
        return cls(data)


class Machine(Node, metaclass=MachineType):
    """A machine stored in MAAS."""

    architecture = ObjectField.Checked(
        "architecture", check_optional(str), check_optional(str))
    boot_disk = ObjectFieldRelated(
        "boot_disk", "BlockDevice", readonly=True)
    boot_interface = ObjectFieldRelated(
        "boot_interface", "Interface", readonly=True)
    block_devices = ObjectFieldRelatedSet(
        "blockdevice_set", "BlockDevices", reverse=None)
    bcaches = ObjectFieldRelatedSet(
        "bcaches", "Bcaches", reverse=None)
    cache_sets = ObjectFieldRelatedSet(
        "cache_sets", "BcacheCacheSets", reverse=None)
    cpus = ObjectField.Checked(
        "cpu_count", check(int), check(int))
    disable_ipv4 = ObjectField.Checked(
        "disable_ipv4", check(bool), check(bool))
    distro_series = ObjectField.Checked(
        "distro_series", check(str), readonly=True)
    hwe_kernel = ObjectField.Checked(
        "hwe_kernel", check_optional(str), check_optional(str))
    memory = ObjectField.Checked(
        "memory", check(int), check(int))
    min_hwe_kernel = ObjectField.Checked(
        "min_hwe_kernel", check_optional(str), check_optional(str))
    netboot = ObjectField.Checked(
        "netboot", check(bool), readonly=True)
    osystem = ObjectField.Checked(
        "osystem", check(str), readonly=True)
    owner_data = ObjectField.Checked(
        "owner_data", check(dict), check(dict))
    status = ObjectField.Checked(
        "status", to(NodeStatus), readonly=True)
    status_action = ObjectField.Checked(
        "status_action", check_optional(str), readonly=True)
    status_message = ObjectField.Checked(
        "status_message", check_optional(str), readonly=True)
    status_name = ObjectField.Checked(
        "status_name", check(str), readonly=True)
    raids = ObjectFieldRelatedSet(
        "raids", "Raids", reverse=None)
    volume_groups = ObjectFieldRelatedSet(
        "volume_groups", "VolumeGroups", reverse=None)

    async def save(self):
        """Save the machine in MAAS."""
        orig_owner_data = self._orig_data['owner_data']
        new_owner_data = dict(self._data['owner_data'])
        self._changed_data.pop('owner_data', None)
        await super(Machine, self).save()
        params_diff = calculate_dict_diff(orig_owner_data, new_owner_data)
        if len(params_diff) > 0:
            params_diff['system_id'] = self.system_id
            await self._handler.set_owner_data(**params_diff)
            self._data['owner_data'] = self._data['owner_data']

    async def abort(self, *, comment: str = None):
        """Abort the current action.

        :param comment: Reason for aborting the action.
        :param type: `str`
        """
        params = {
            "system_id": self.system_id
        }
        if comment:
            params["comment"] = comment
        self._reset(await self._handler.abort(**params))
        return self

    async def clear_default_gateways(self):
        """Clear default gateways."""
        self._reset(await self._handler.clear_default_gateways(
            system_id=self.system_id))
        return self

    async def commission(
            self, *, enable_ssh: bool = None, skip_networking: bool = None,
            skip_storage: bool = None,
            commissioning_scripts: typing.Sequence[str] = None,
            testing_scripts: typing.Sequence[str] = None,
            wait: bool = False, wait_interval: int = 5):
        """Commission this machine.

        :param enable_ssh: Prevent the machine from powering off after running
            commissioning scripts and enable your user to SSH into the machine.
        :type enable_ssh: `bool`
        :param skip_networking: Skip updating the MAAS interfaces for the
            machine.
        :type skip_networking: `bool`
        :param skip_storage: Skip update the MAAS block devices for the
            machine.
        :type skip_storage: `bool`
        :param commissioning_scripts: List of extra commisisoning scripts
            to run. If the name of the commissioning scripts match a tag, then
            all commissioning scripts with that tag will be used.
        :type commissioning_scripts: sequence of `str`
        :param testing_scripts: List of testing scripts to run after
            commissioning. By default a small set of testing scripts will run
            by default. Passing empty list will disable running any testing
            scripts during commissioning. If the name of the testing scripts
            match a tag, then all testing scripts with that tag will be used.
        :type testing_scripts: sequence of `str`
        :param wait: If specified, wait until the commissioning is complete.
        :param wait_interval: How often to poll, defaults to 5 seconds
        """
        params = {"system_id": self.system_id}
        if enable_ssh is not None:
            params["enable_ssh"] = enable_ssh
        if skip_networking is not None:
            params["skip_networking"] = skip_networking
        if skip_storage is not None:
            params["skip_storage"] = skip_storage
        if (commissioning_scripts is not None and
                len(commissioning_scripts) > 0):
            params["commissioning_scripts"] = ",".join(commissioning_scripts)
        if testing_scripts is not None:
            if len(testing_scripts) == 0 or testing_scripts == "none":
                params["testing_scripts"] = ["none"]
            else:
                params["testing_scripts"] = ",".join(testing_scripts)
        self._reset(await self._handler.commission(**params))
        if not wait:
            return self
        else:
            # Wait for the machine to be fully commissioned.
            while self.status in [
                    NodeStatus.COMMISSIONING, NodeStatus.TESTING]:
                await asyncio.sleep(wait_interval)
                self._reset(await self._handler.read(system_id=self.system_id))
            if self.status == NodeStatus.FAILED_COMMISSIONING:
                msg = "{hostname} failed to commission.".format(
                    hostname=self.hostname)
                raise FailedCommissioning(msg, self)
            if self.status == NodeStatus.FAILED_TESTING:
                msg = "{hostname} failed testing.".format(
                    hostname=self.hostname)
                raise FailedTesting(msg, self)
            return self

    async def deploy(
            self, *, user_data: typing.Union[bytes, str] = None,
            distro_series: str = None, hwe_kernel: str = None,
            comment: str = None, wait: bool = False, wait_interval: int = 5):
        """Deploy this machine.

        :param user_data: User-data to provide to the machine when booting. If
            provided as a byte string, it will be base-64 encoded prior to
            transmission. If provided as a Unicode string it will be assumed
            to be already base-64 encoded.
        :param distro_series: The OS to deploy.
        :param hwe_kernel: The HWE kernel to deploy. Probably only relevant
            when deploying Ubuntu.
        :param comment: A comment for the event log.
        :param wait: If specified, wait until the deploy is complete.
        :param wait_interval: How often to poll, defaults to 5 seconds
        """
        params = {"system_id": self.system_id}
        if user_data is not None:
            if isinstance(user_data, bytes):
                params["user_data"] = base64.encodebytes(user_data)
            else:
                # Already base-64 encoded. Convert to a byte string in
                # preparation for multipart assembly.
                params["user_data"] = user_data.encode("ascii")
        if distro_series is not None:
            params["distro_series"] = distro_series
        if hwe_kernel is not None:
            params["hwe_kernel"] = hwe_kernel
        if comment is not None:
            params["comment"] = comment
        self._reset(await self._handler.deploy(**params))
        if not wait:
            return self
        else:
            # Wait for the machine to be fully deployed
            while self.status == NodeStatus.DEPLOYING:
                await asyncio.sleep(wait_interval)
                self._reset(await self._handler.read(system_id=self.system_id))
            if self.status == NodeStatus.FAILED_DEPLOYMENT:
                msg = "{hostname} failed to deploy.".format(
                    hostname=self.hostname
                )
                raise FailedDeployment(msg, self)
            return self

    async def enter_rescue_mode(
            self, wait: bool = False, wait_interval: int = 5):
        """
        Send this machine into 'rescue mode'.

        :param wait: If specified, wait until the deploy is complete.
        :param wait_interval: How often to poll, defaults to 5 seconds
        """
        try:
            self._reset(await self._handler.rescue_mode(
                system_id=self.system_id))
        except CallError as error:
            if error.status == HTTPStatus.FORBIDDEN:
                message = "Not allowed to enter rescue mode"
                raise OperationNotAllowed(message) from error
            else:
                raise

        if not wait:
            return self
        else:
            # Wait for machine to finish entering rescue mode
            while self.status == NodeStatus.ENTERING_RESCUE_MODE:
                await asyncio.sleep(wait)
                self._reset(await self._handler.read(system_id=self.system_id))
            if self.status == NodeStatus.FAILED_ENTERING_RESCUE_MODE:
                msg = "{hostname} failed to enter rescue mode.".format(
                    hostname=self.hostname
                )
                raise RescueModeFailure(msg, self)
            return self

    async def exit_rescue_mode(
            self, wait: bool = False, wait_interval: int = 5):
        """
        Exit rescue mode.

        :param wait: If specified, wait until the deploy is complete.
        :param wait_interval: How often to poll, defaults to 5 seconds
        """
        try:
            self._reset(await self._handler.exit_rescue_mode(
                system_id=self.system_id
            ))
        except CallError as error:
            if error.status == HTTPStatus.FORBIDDEN:
                message = "Not allowed to exit rescue mode."
                raise OperationNotAllowed(message) from error
            else:
                raise
        if not wait:
            return self
        else:
            # Wait for machine to finish exiting rescue mode
            while self.status == NodeStatus.EXITING_RESCUE_MODE:
                await asyncio.sleep(wait_interval)
                self._reset(await self._handler.read(system_id=self.system_id))
            if self.status == NodeStatus.FAILED_EXITING_RESCUE_MODE:
                msg = "{hostname} failed to exit rescue mode.".format(
                    hostname=self.hostname
                )
                raise RescueModeFailure(msg, self)
            return self

    async def get_curtin_config(self):
        """Get the curtin configuration.

        :returns: Curtin configuration
        :rtype: `str`
        """
        return self._handler.get_curtin_config(system_id=self.system_id)

    async def get_details(self):
        """Get machine details information.

        :returns: Mapping of hardware details.
        """
        data = await self._handler.details(system_id=self.system_id)
        return bson.decode_all(data)[0]

    async def mark_broken(self, *, comment: str = None):
        """Mark broken.

        :param comment: Reason machine is broken.
        :type comment: `str`
        """
        params = {
            "system_id": self.system_id
        }
        if comment:
            params["comment"] = comment
        self._reset(await self._handler.mark_broken(**params))
        return self

    async def mark_fixed(self, *, comment: str = None):
        """Mark fixes.

        :param comment: Reason machine is fixed.
        :type comment: `str`
        """
        params = {
            "system_id": self.system_id
        }
        if comment:
            params["comment"] = comment
        self._reset(await self._handler.mark_fixed(**params))
        return self

    async def release(
            self, *, comment: str = None, erase: bool = None,
            secure_erase: bool = None, quick_erase: bool = None,
            wait: bool = False, wait_interval: int = 5):
        """
        Release the machine.

        :param comment: Reason machine was released.
        :type comment: `str`
        :param erase: Erase the disk when release.
        :type erase: `bool`
        :param secure_erase: Use the drive's secure erase feature if available.
        :type secure_erase: `bool`
        :param quick_erase: Wipe the just the beginning and end of the disk.
            This is not secure.
        :param wait: If specified, wait until the deploy is complete.
        :type wait: `bool`
        :param wait_interval: How often to poll, defaults to 5 seconds.
        :type wait_interval: `int`
        """
        params = remove_None({
            "system_id": self.system_id,
            "comment": comment,
            "erase": erase,
            "secure_erase": secure_erase,
            "quick_erase": quick_erase,
        })
        self._reset(await self._handler.release(**params))
        if not wait:
            return self
        else:
            # Wait for machine to be released
            while self.status in [
                    NodeStatus.RELEASING, NodeStatus.DISK_ERASING]:
                await asyncio.sleep(wait_interval)
                try:
                    self._reset(await self._handler.read(
                        system_id=self.system_id))
                except CallError as error:
                    if error.status == HTTPStatus.NOT_FOUND:
                        # Release must have been on a machine in a pod. This
                        # machine no longer exists. Just return the machine
                        # as it has been released.
                        return self
                    else:
                        raise
            if self.status == NodeStatus.FAILED_RELEASING:
                msg = "{hostname} failed to be released.".format(
                    hostname=self.hostname
                )
                raise FailedReleasing(msg, self)
            elif self.status == NodeStatus.FAILED_DISK_ERASING:
                msg = "{hostname} failed to erase disk.".format(
                    hostname=self.hostname
                )
                raise FailedDiskErasing(msg, self)
            return self

    async def power_on(
            self, comment: str = None,
            wait: bool = False, wait_interval: int = 5):
        """
        Power on.

        :param comment: Reason machine was powered on.
        :type comment: `str`
        :param wait: If specified, wait until the machine is powered on.
        :type wait: `bool`
        :param wait_interval: How often to poll, defaults to 5 seconds.
        :type wait_interval: `int`
        """
        params = {"system_id": self.system_id}
        if comment is not None:
            params["comment"] = comment
        try:
            self._reset(await self._handler.power_on(**params))
        except CallError as error:
            if error.status == HTTPStatus.FORBIDDEN:
                message = "Not allowed to power on machine."
                raise OperationNotAllowed(message) from error
            else:
                raise
        if not wait or self.power_state == PowerState.UNKNOWN:
            # Don't wait for a machine that always shows power state as
            # unknown as the driver cannot query the power state.
            return self
        else:
            # Wait for machine to be powered on.
            while self.power_state == PowerState.OFF:
                await asyncio.sleep(wait_interval)
                self._reset(await self._handler.read(system_id=self.system_id))
            if self.power_state == PowerState.ERROR:
                msg = "{hostname} failed to power on.".format(
                    hostname=self.hostname
                )
                raise PowerError(msg, self)
            return self

    async def power_off(
            self, stop_mode: PowerStopMode = PowerStopMode.HARD,
            comment: str = None, wait: bool = False, wait_interval: int = 5):
        """
        Power off.

        :param stop_mode: How to perform the power off.
        :type stop_mode: `PowerStopMode`
        :param comment: Reason machine was powered on.
        :type comment: `str`
        :param wait: If specified, wait until the machine is powered on.
        :type wait: `bool`
        :param wait_interval: How often to poll, defaults to 5 seconds.
        :type wait_interval: `int`
        """
        params = {"system_id": self.system_id, 'stop_mode': stop_mode.value}
        if comment is not None:
            params["comment"] = comment
        try:
            self._reset(await self._handler.power_off(**params))
        except CallError as error:
            if error.status == HTTPStatus.FORBIDDEN:
                message = "Not allowed to power off machine."
                raise OperationNotAllowed(message) from error
            else:
                raise
        if not wait or self.power_state == PowerState.UNKNOWN:
            # Don't wait for a machine that always shows power state as
            # unknown as the driver cannot query the power state.
            return self
        else:
            # Wait for machine to be powered off.
            while self.power_state == PowerState.ON:
                await asyncio.sleep(wait_interval)
                self._reset(await self._handler.read(system_id=self.system_id))
            if self.power_state == PowerState.ERROR:
                msg = "{hostname} failed to power off.".format(
                    hostname=self.hostname
                )
                raise PowerError(msg, self)
            return self

    async def query_power_state(self):
        """
        Query the machine's BMC for the current power state.

        :returns: Current power state.
        :rtype: `PowerState`
        """
        power_data = await self._handler.query_power_state(
            system_id=self.system_id)
        # Update the internal state of this object as well, since we have the
        # updated power state from the BMC directly. MAAS server does this as
        # well, just do it client side to make it nice for a developer.
        self._data['power_state'] = power_data['state']
        return PowerState(power_data['state'])

    async def restore_default_configuration(self):
        """
        Restore machine's configuration to its initial state.
        """
        self._reset(await self._handler.restore_default_configuration(
            system_id=self.system_id))

    async def restore_networking_configuration(self):
        """
        Restore machine's networking configuration to its initial state.
        """
        self._reset(await self._handler.restore_networking_configuration(
            system_id=self.system_id))

    async def restore_storage_configuration(self):
        """
        Restore machine's storage configuration to its initial state.
        """
        self._reset(await self._handler.restore_storage_configuration(
            system_id=self.system_id))

    async def lock(self, *, comment: str = None):
        """Lock the machine to prevent changes.

        :param comment: Reason machine was locked.
        :type comment: `str`
        """
        params = {
            "system_id": self.system_id
        }
        if comment:
            params["comment"] = comment
        self._reset(await self._handler.lock(**params))
        return self

    async def unlock(self, *, comment: str = None):
        """Unlock the machine allowing changes.

        :param comment: Reason machine was unlocked.
        :type comment: `str`
        """
        params = {
            "system_id": self.system_id
        }
        if comment:
            params["comment"] = comment
        self._reset(await self._handler.unlock(**params))
        return self
