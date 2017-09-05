"""Objects for machines."""

__all__ = [
    "Machine",
    "Machines",
]

import asyncio
import base64
import bson
from http import HTTPStatus
import typing

from . import (
    check,
    check_optional,
    ObjectField,
    ObjectFieldRelated,
    to,
)
from .nodes import (
    Node,
    Nodes,
    NodesType,
    NodeTypeMeta,
)
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
from ..utils.diff import calculate_dict_diff


class MachinesType(NodesType):
    """Metaclass for `Machines`."""

    async def create(
            cls, architecture: str, mac_addresses: typing.Sequence[str],
            power_type: str,
            power_parameters: typing.Mapping[str, typing.Any]=None, *,
            subarchitecture: str=None, min_hwe_kernel: str=None,
            hostname: str=None, domain: typing.Union[int, str]=None):
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
            params["power_parameters"] = power_parameters
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
            cls, *, hostname: str=None, architecture: str=None, cpus: int=None,
            memory: float=None, tags: typing.Sequence[str]=None):
        """
        Allocate a machine.

        :param hostname: The hostname to match.
        :param architecture: The architecture to match, e.g. "amd64".
        :param cpus: The minimum number of CPUs to match.
        :param memory: The minimum amount of RAM to match.
        :param tags: The tags to match, as a sequence. Each tag may be
            prefixed with a hyphen to denote that the given tag should NOT be
            associated with a matched machine.
        """
        params = {}
        if hostname is not None:
            params["name"] = hostname
        if architecture is not None:
            params["architecture"] = architecture
        if cpus is not None:
            params["cpu_count"] = str(cpus)
        if memory is not None:
            params["mem"] = str(memory)
        if tags is not None:
            params["tags"] = [
                tag for tag in tags if not tag.startswith("-")]
            params["not_tags"] = [
                tag[1:] for tag in tags if tag.startswith("-")]

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
    boot_disk = ObjectField.Checked(
        "boot_disk", check_optional(str), check_optional(str))
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
    osystem = ObjectField.Checked(
        "osystem", check(str), readonly=True)
    owner_data = ObjectField.Checked(
        "owner_data", check(dict), check(dict))

    boot_interface = ObjectFieldRelated(
        "boot_interface", "Interface", readonly=True)

    # blockdevice_set
    # macaddress_set
    # netboot
    # physicalblockdevice_set

    power_state = ObjectField.Checked(
        "power_state", to(PowerState), readonly=True)

    # power_type
    # pxe_mac
    # resource_uri
    # routers
    # status
    # storage

    status = ObjectField.Checked(
        "status", to(NodeStatus), readonly=True)
    status_action = ObjectField.Checked(
        "status_action", check_optional(str), readonly=True)
    status_message = ObjectField.Checked(
        "status_message", check_optional(str), readonly=True)
    status_name = ObjectField.Checked(
        "status_name", check(str), readonly=True)

    # swap_size
    # virtualblockdevice_set

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

    async def get_power_parameters(self):
        """Get the power paramters for this machine."""
        data = await self._handler.power_parameters(system_id=self.system_id)
        return data

    async def abort(self, *, comment: str=None):
        """Abort the current action.

        :param comment: Reason for aborting the action.
        :param type: `str`
        """
        params = {
            "system_id": self.system_id
        }
        if comment:
            params["comment"] = comment
        self._data = await self._handler.abort(**params)
        return self

    async def clear_default_gateways(self):
        """Clear default gateways."""
        self._data = await self._handler.clear_default_gateways(
            system_id=self.system_id)
        return self

    async def commission(
            self, *, enable_ssh: bool=None, skip_networking: bool=None,
            skip_storage: bool=None,
            commissioning_scripts: typing.Sequence[str]=None,
            testing_scripts: typing.Sequence[str]=None,
            wait: bool=False, wait_interval: int=5):
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
            if len(testing_scripts) == 0:
                params["testing_scripts"] = ""
            else:
                params["testing_scripts"] = ",".join(testing_scripts)
        self._data = await self._handler.commission(**params)
        if not wait:
            return self
        else:
            # Wait for the machine to be fully commissioned.
            while self.status in [
                    NodeStatus.COMMISSIONING, NodeStatus.TESTING]:
                await asyncio.sleep(wait_interval)
                self._data = await self._handler.read(system_id=self.system_id)
            if self.status == NodeStatus.FAILED_COMMISSIONING:
                msg = "{system_id} failed to commission.".format(
                    system_id=self.system_id)
                raise FailedCommissioning(msg, self)
            if self.status == NodeStatus.FAILED_TESTING:
                msg = "{system_id} failed testing.".format(
                    system_id=self.system_id)
                raise FailedTesting(msg, self)
            return self

    async def deploy(
            self, user_data: typing.Union[bytes, str]=None,
            distro_series: str=None, hwe_kernel: str=None, comment: str=None,
            wait: bool=False, wait_interval: int=5):
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
        self._data = await self._handler.deploy(**params)
        if not wait:
            return self
        else:
            # Wait for the machine to be fully deployed
            while self.status == NodeStatus.DEPLOYING:
                await asyncio.sleep(wait_interval)
                self._data = await self._handler.read(system_id=self.system_id)
            if self.status == NodeStatus.FAILED_DEPLOYMENT:
                msg = "{system_id} failed to deploy.".format(
                    system_id=self.system_id
                )
                raise FailedDeployment(msg, self)
            return self

    async def enter_rescue_mode(self, wait: bool=False, wait_interval: int=5):
        """
        Send this machine into 'rescue mode'.

        :param wait: If specified, wait until the deploy is complete.
        :param wait_interval: How often to poll, defaults to 5 seconds
        """
        try:
            self._data = await self._handler.rescue_mode(
                system_id=self.system_id)
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
                self._data = await self._handler.read(system_id=self.system_id)
            if self.status == NodeStatus.FAILED_ENTERING_RESCUE_MODE:
                msg = "{system_id} failed to enter rescue mode.".format(
                    system_id=self.system_id
                )
                raise RescueModeFailure(msg, self)
            return self

    async def exit_rescue_mode(self, wait: bool=False, wait_interval: int=5):
        """
        Exit rescue mode.

        :param wait: If specified, wait until the deploy is complete.
        :param wait_interval: How often to poll, defaults to 5 seconds
        """
        try:
            self._data = await self._handler.exit_rescue_mode(
                system_id=self.system_id
            )
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
                self._data = await self._handler.read(system_id=self.system_id)
            if self.status == NodeStatus.FAILED_EXITING_RESCUE_MODE:
                msg = "{system_id} failed to exit rescue mode.".format(
                    system_id=self.system_id
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
        return bson.loads(data)

    async def mark_broken(self, *, comment: str=None):
        """Mark broken.

        :param comment: Reason machine is broken.
        :type comment: `str`
        """
        params = {
            "system_id": self.system_id
        }
        if comment:
            params["comment"] = comment
        self._data = await self._handler.mark_broken(**params)
        return self

    async def mark_fixed(self, *, comment: str=None):
        """Mark fixes.

        :param comment: Reason machine is fixed.
        :type comment: `str`
        """
        params = {
            "system_id": self.system_id
        }
        if comment:
            params["comment"] = comment
        self._data = await self._handler.mark_fixed(**params)
        return self

    async def release(
            self, comment: str=None, wait: bool=False, wait_interval: int=5):
        """
        Release the machine.

        :param comment: Reason machine was released.
        :type comment: `str`
        :param wait: If specified, wait until the deploy is complete.
        :type wait: `bool`
        :param wait_interval: How often to poll, defaults to 5 seconds.
        :type wait_interval: `int`
        """
        params = {"system_id": self.system_id}
        if comment is not None:
            params["comment"] = comment
        self._data = await self._handler.release(**params)
        if not wait:
            return self
        else:
            # Wait for machine to be released
            while self.status in [
                    NodeStatus.RELEASING, NodeStatus.DISK_ERASING]:
                await asyncio.sleep(wait_interval)
                self._data = await self._handler.read(system_id=self.system_id)
            if self.status == NodeStatus.FAILED_RELEASING:
                msg = "{system_id} failed to be released.".format(
                    system_id=self.system_id
                )
                raise FailedReleasing(msg, self)
            elif self.status == NodeStatus.FAILED_DISK_ERASING:
                msg = "{system_id} failed to erase disk.".format(
                    system_id=self.system_id
                )
                raise FailedDiskErasing(msg, self)
            return self

    async def power_on(
            self, comment: str=None, wait: bool=False, wait_interval: int=5):
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
            self._data = await self._handler.power_on(**params)
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
                self._data = await self._handler.read(system_id=self.system_id)
            if self.power_state == PowerState.ERROR:
                msg = "{system_id} failed to power on.".format(
                    system_id=self.system_id
                )
                raise PowerError(msg, self)
            return self

    async def power_off(
            self, stop_mode: PowerStopMode=PowerStopMode.HARD,
            comment: str=None, wait: bool=False, wait_interval: int=5):
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
            self._data = await self._handler.power_off(**params)
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
                self._data = await self._handler.read(system_id=self.system_id)
            if self.power_state == PowerState.ERROR:
                msg = "{system_id} failed to power off.".format(
                    system_id=self.system_id
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
        self._data = await self._handler.restore_default_configuration(
            system_id=self.system_id)

    async def restore_networking_configuration(self):
        """
        Restore machine's networking configuration to its initial state.
        """
        self._data = await self._handler.restore_networking_configuration(
            system_id=self.system_id)

    async def restore_storage_configuration(self):
        """
        Restore machine's storage configuration to its initial state.
        """
        self._data = await self._handler.restore_storage_configuration(
            system_id=self.system_id)
