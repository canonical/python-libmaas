__all__ = [
    "NodeStatus",
]

import enum


class NodeStatus(enum.IntEnum):
    #: A node starts out as NEW (DEFAULT is an alias for NEW).
    DEFAULT = 0
    #: The node has been created and has a system ID assigned to it.
    NEW = 0
    #: Testing and other commissioning steps are taking place.
    COMMISSIONING = 1
    #: The commissioning step failed.
    FAILED_COMMISSIONING = 2
    #: The node can't be contacted.
    MISSING = 3
    #: The node is in the general pool ready to be deployed.
    READY = 4
    #: The node is ready for named deployment.
    RESERVED = 5
    #: The node has booted into the operating system of its owner's choice
    #: and is ready for use.
    DEPLOYED = 6
    #: The node has been removed from service manually until an admin
    #: overrides the retirement.
    RETIRED = 7
    #: The node is broken: a step in the node lifecyle failed.
    #: More details can be found in the node's event log.
    BROKEN = 8
    #: The node is being installed.
    DEPLOYING = 9
    #: The node has been allocated to a user and is ready for deployment.
    ALLOCATED = 10
    #: The deployment of the node failed.
    FAILED_DEPLOYMENT = 11
    #: The node is powering down after a release request.
    RELEASING = 12
    #: The releasing of the node failed.
    FAILED_RELEASING = 13
    #: The node is erasing its disks.
    DISK_ERASING = 14
    #: The node failed to erase its disks.
    FAILED_DISK_ERASING = 15
    #: The node is in rescue mode.
    RESCUE_MODE = 16
    #: The node is entering rescue mode.
    ENTERING_RESCUE_MODE = 17
    #: The node failed to enter rescue mode.
    FAILED_ENTERING_RESCUE_MODE = 18
    #: The node is exiting rescue mode.
    EXITING_RESCUE_MODE = 19
    #: The node failed to exit rescue mode.
    FAILED_EXITING_RESCUE_MODE = 20
    #: Running tests on Node
    TESTING = 21
    #: Testing has failed
    FAILED_TESTING = 22


class NodeType(enum.IntEnum):
    #: Machine
    MACHINE = 0
    #: Device
    DEVICE = 1
    #: Rack
    RACK_CONTROLLER = 2
    #: Region
    REGION_CONTROLLER = 3
    #: Region+Rack
    REGION_AND_RACK_CONTROLLER = 4


class PowerState(enum.Enum):
    #: On
    ON = 'on'
    #: Off
    OFF = 'off'
    #: Unknown
    UNKNOWN = 'unknown'
    #: Error
    ERROR = 'error'


class PowerStopMode(enum.Enum):
    #: Perform hard stop.
    HARD = 'hard'
    #: Perform soft stop.
    SOFT = 'soft'


class RDNSMode(enum.IntEnum):
    #: Do not generate reverse DNS for this Subnet.
    DISABLED = 0
    #: Generate reverse DNS only for the CIDR.
    ENABLED = 1
    #: Generate RFC2317 glue if needed (Subnet is too small for its own zone.)
    RFC2317 = 2


class IPRangeType(enum.Enum):
    #: Dynamic IP Range.
    DYNAMIC = 'dynamic'
    #: Reserved for exclusive use by MAAS or user.
    RESERVED = 'reserved'


class InterfaceType(enum.Enum):
    #: Physical interface.
    PHYSICAL = 'physical'
    #: Bonded interface.
    BOND = 'bond'
    #: Bridge interface.
    BRIDGE = 'bridge'
    #: VLAN interface.
    VLAN = 'vlan'
    #: Interface not linked to a node.
    UNKNOWN = 'unknown'


class LinkMode(enum.Enum):
    #: IP is auto assigned by MAAS.
    AUTO = 'auto'
    #: IP is assigned by a DHCP server.
    DHCP = 'dhcp'
    #: IP is statically assigned.
    STATIC = 'static'
    #: Connected to subnet with no IP address.
    LINK_UP = 'link_up'


class BlockDeviceType(enum.Enum):
    #: Physical block device.
    PHYSICAL = 'physical'
    #: Virtual block device.
    VIRTUAL = 'virtual'


class PartitionTableType(enum.Enum):
    #: Master boot record
    MBR = 'mbr'
    #: GUID Partition Table
    GPT = 'gpt'


class RaidLevel(enum.Enum):
    #: RAID level 0
    RAID_0 = 'raid-0'
    #: RAID level 1
    RAID_1 = 'raid-1'
    #: RAID level 5
    RAID_5 = 'raid-5'
    #: RAID level 6
    RAID_6 = 'raid-6'
    #: RAID level 10
    RAID_10 = 'raid-10'


class CacheMode(enum.Enum):
    #: Writeback
    WRITEBACK = 'writeback'
    #: Writethough
    WRITETHROUGH = 'writethrough'
    #: Writearound
    WRITEAROUND = 'writearound'
