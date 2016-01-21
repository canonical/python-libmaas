"""Objects for nodes."""

__all__ = [
    "Node",
    "Nodes",
]

import base64
from http import HTTPStatus
from typing import (
    List,
    Sequence,
    Union,
)

from alburnum.maas.bones import CallError

from . import (
    check,
    check_optional,
    Disabled,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
)


class NodesType(ObjectType):
    """Metaclass for `Nodes`."""

    def __iter__(cls):
        return map(cls._object, cls._handler.list())

    def read(cls):
        return cls(cls)

    list = Disabled("list", "read")  # API is malformed in MAAS server.

    def acquire(
            cls, *, hostname: str=None, architecture: str=None,
            cpus: int=None, memory: float=None, tags: Sequence[str]=None):
        """
        :param hostname: The hostname to match.
        :param architecture: The architecture to match, e.g. "amd64".
        :param cpus: The minimum number of CPUs to match.
        :param memory: The minimum amount of RAM to match.
        :param tags: The tags to match, as a sequence. Each tag may be
            prefixed with a hyphen to denote that the given tag should NOT be
            associated with a matched node.
        """
        params = {}
        if hostname is not None:
            params["hostname"] = hostname
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
            data = cls._handler.acquire(**params)
        except CallError as error:
            if error.status == HTTPStatus.CONFLICT:
                message = "No node matching the given criteria was found."
                raise NodeNotFound(message) from error
            else:
                raise
        else:
            return cls._object(data)


class NodeNotFound(Exception):
    """Node was not found."""


class Nodes(ObjectSet, metaclass=NodesType):
    """The set of nodes stored in MAAS."""


class NodeType(ObjectType):

    def read(cls, system_id):
        data = cls._handler.read(system_id=system_id)
        return cls(data)


class Node(Object, metaclass=NodeType):
    """A node stored in MAAS."""

    architecture = ObjectField.Checked(
        "architecture", check_optional(str), check_optional(str))
    boot_disk = ObjectField.Checked(
        "boot_disk", check_optional(str), check_optional(str))

    # boot_type

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
    ip_addresses = ObjectField.Checked(
        "ip_addresses", check(List[str]), readonly=True)
    memory = ObjectField.Checked(
        "memory", check(int), check(int))
    min_hwe_kernel = ObjectField.Checked(
        "min_hwe_kernel", check_optional(str), check_optional(str))

    # blockdevice_set
    # interface_set
    # macaddress_set
    # netboot
    # osystem
    # owner
    # physicalblockdevice_set

    # TODO: Use an enum here.
    power_state = ObjectField.Checked(
        "power_state", check(str), readonly=True)

    # power_state
    # power_type
    # pxe_mac
    # resource_uri
    # routers
    # status
    # storage

    substatus = ObjectField.Checked(
        "substatus", check(int), readonly=True)
    substatus_action = ObjectField.Checked(
        "substatus_action", check_optional(str), readonly=True)
    substatus_message = ObjectField.Checked(
        "substatus_message", check_optional(str), readonly=True)
    substatus_name = ObjectField.Checked(
        "substatus_name", check(str), readonly=True)

    # swap_size

    system_id = ObjectField.Checked(
        "system_id", check(str), readonly=True)

    # system_id
    # tag_names
    # virtualblockdevice_set
    # zone

    def start(
            self, user_data: Union[bytes, str]=None, distro_series: str=None,
            hwe_kernel: str=None, comment: str=None):
        """Start this node.

        :param user_data: User-data to provide to the node when booting. If
            provided as a byte string, it will be base-64 encoded prior to
            transmission. If provided as a Unicode string it will be assumed
            to be already base-64 encoded.
        :param distro_series: The OS to deploy.
        :param hwe_kernel: The HWE kernel to deploy. Probably only relevant
            when deploying Ubuntu.
        :param comment: A comment for the event log.
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
        data = self._handler.start(**params)
        return type(self)(data)

    def release(self, comment: str=None):
        params = {"system_id": self.system_id}
        if comment is not None:
            params["comment"] = comment
        data = self._handler.release(**params)
        return type(self)(data)

    def __repr__(self):
        return super(Node, self).__repr__(
            fields={"system_id", "hostname"})
