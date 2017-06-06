"""Objects for machines."""

__all__ = [
    "Machine",
    "Machines",
]

import asyncio
import base64
from collections import Sequence
from http import HTTPStatus
import typing

from . import (
    check,
    check_optional,
    Object,
    ObjectField,
    ObjectFieldRelated,
    ObjectFieldRelatedSet,
    ObjectSet,
    ObjectType,
    zones,
)
from ..bones import CallError
from ..enum import NodeStatus
from ..errors import (
    MAASException,
    OperationNotAllowed
)


class MachinesType(ObjectType):
    """Metaclass for `Machines`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))

    async def allocate(
            cls, *, hostname: str=None, architecture: str=None, cpus: int=None,
            memory: float=None, tags: typing.Sequence[str]=None):
        """
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


class FailedDeployment(MAASException):
    """Machine failed to Deploy."""


class FailedReleasing(MAASException):
    """Machine failed to Release."""


class FailedDiskErasing(MAASException):
    """Machine failed to erase disk when releasing."""


class Machines(ObjectSet, metaclass=MachinesType):
    """The set of machines stored in MAAS."""


class MachineType(ObjectType):

    async def read(cls, system_id):
        data = await cls._handler.read(system_id=system_id)
        return cls(data)


class Machine(Object, metaclass=MachineType):
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
        "distro_series", check(str), check(str))
    hostname = ObjectField.Checked(
        "hostname", check(str), check(str))
    hwe_kernel = ObjectField.Checked(
        "hwe_kernel", check_optional(str), check_optional(str))
    ip_addresses = ObjectField.Checked(  # List[str]
        "ip_addresses", check(Sequence), readonly=True)
    memory = ObjectField.Checked(
        "memory", check(int), check(int))
    min_hwe_kernel = ObjectField.Checked(
        "min_hwe_kernel", check_optional(str), check_optional(str))

    boot_interface = ObjectFieldRelated(
        "boot_interface", "Interface", readonly=True)
    interfaces = ObjectFieldRelatedSet("interface_set", "Interfaces")

    # blockdevice_set
    # macaddress_set
    # netboot
    # osystem
    # owner
    # physicalblockdevice_set

    # TODO: Use an enum here.
    power_state = ObjectField.Checked(
        "power_state", check(str), readonly=True)

    # power_type
    # pxe_mac
    # resource_uri
    # routers
    # status
    # storage

    status = ObjectField.Checked(
        "status", check(int), readonly=True)
    status_action = ObjectField.Checked(
        "status_action", check_optional(str), readonly=True)
    status_message = ObjectField.Checked(
        "status_message", check_optional(str), readonly=True)
    status_name = ObjectField.Checked(
        "status_name", check(str), readonly=True)

    # swap_size

    system_id = ObjectField.Checked(
        "system_id", check(str), readonly=True)
    tags = ObjectField.Checked(  # List[str]
        "tag_names", check(Sequence), readonly=True)

    # virtualblockdevice_set

    zone = zones.ZoneField(
        "zone", readonly=True)

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
        data = await self._handler.deploy(**params)
        if not wait:
            return type(self)(data)
        else:
            # Wait for the machine to be fully deployed
            machine = type(self)(data)
            while machine.status == NodeStatus.DEPLOYING:
                await asyncio.sleep(wait_interval)
                data = await self._handler.read(system_id=self.system_id)
                machine = type(self)(data)
            if machine.status == NodeStatus.FAILED_DEPLOYMENT:
                msg = "{system_id} failed to Deploy.".format(
                    system_id=machine.system_id
                )
                raise FailedDeployment(msg, machine)
            return machine

    async def get_power_parameters(self):
        data = await self._handler.power_parameters(system_id=self.system_id)
        return data

    async def release(self, comment: str=None, wait: bool=False,
                      wait_interval: int=5):
        """
        Release the machine.

        :param wait: If specified, wait until the deploy is complete.
        :param wait_interval: How often to poll, defaults to 5 seconds
        """
        params = {"system_id": self.system_id}
        if comment is not None:
            params["comment"] = comment
        data = await self._handler.release(**params)
        if not wait:
            return type(self)(data)
        else:
            # Wait for machine to be released
            machine = type(self)(data)
            while (machine.status == NodeStatus.RELEASING or
                   machine.status == NodeStatus.DISK_ERASING):
                await asyncio.sleep(wait_interval)
                data = await self._handler.read(system_id=self.system_id)
                machine = type(self)(data)
            if machine.status == NodeStatus.FAILED_RELEASING:
                msg = "{system_id} failed to be Released.".format(
                    system_id=machine.system_id
                )
                raise FailedReleasing(msg, machine)
            elif machine.status == NodeStatus.FAILED_DISK_ERASING:
                msg = "{system_id} failed to erase disk.".format(
                    system_id=machine.system_id
                )
                raise FailedDiskErasing(msg, machine)
            return machine

    async def enter_rescue_mode(self, wait: bool=False, wait_interval: int=5):
        """
        Send this machine into 'rescue mode'.

        :param wait: If specified, wait until the deploy is complete.
        :param wait_interval: How often to poll, defaults to 5 seconds
        """
        try:
            data = await self._handler.rescue_mode(system_id=self.system_id)
        except CallError as error:
            if error.status == HTTPStatus.FORBIDDEN:
                message = "Not allowed to enter rescue mode"
                raise OperationNotAllowed(message) from error
            else:
                raise

        if not wait:
            return type(self)(data)
        else:
            # Wait for machine to finish entering rescue mode
            machine = type(self)(data)
            while machine.status == NodeStatus.ENTERING_RESCUE_MODE:
                await asyncio.sleep(wait)
                data = await self._handler.read(system_id=self.system_id)
                machine = type(self)(data)
            if machine.status == NodeStatus.FAILED_ENTERING_RESCUE_MODE:
                msg = "{system_id} failed to enter Rescue Mode.".format(
                    system_id=machine.system_id
                )
                raise RescueModeFailure(msg, machine)
            return machine

    async def exit_rescue_mode(self, wait: bool=False, wait_interval: int=5):
        """
        Exit rescue mode.

        :param wait: If specified, wait until the deploy is complete.
        :param wait_interval: How often to poll, defaults to 5 seconds
        """
        try:
            data = await self._handler.exit_rescue_mode(
                system_id=self.system_id
            )
        except CallError as error:
            if error.status == HTTPStatus.FORBIDDEN:
                message = "Not allowed to exit rescue mode."
                raise OperationNotAllowed(message) from error
            else:
                raise
        if not wait:
            return type(self)(data)
        else:
            # Wait for machine to finish exiting rescue mode
            machine = type(self)(data)
            while machine.status == NodeStatus.EXITING_RESCUE_MODE:
                await asyncio.sleep(wait_interval)
                data = await self._handler.read(system_id=self.system_id)
                machine = type(self)(data)
            if machine.status == NodeStatus.FAILED_EXITING_RESCUE_MODE:
                msg = "{system_id} failed to exit Rescue Mode.".format(
                    system_id=machine.system_id
                )
                raise RescueModeFailure(msg, machine)
            return machine

    def __repr__(self):
        return super(Machine, self).__repr__(
            fields={"system_id", "hostname"})
