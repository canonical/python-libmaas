"""Tests for `maas.client.flesh.machines`."""

from functools import partial
from operator import itemgetter
import yaml

from .testing import TestCaseWithProfile
from .. import ArgumentParser, machines, tabular
from ...enum import NodeStatus, PowerState
from ...testing import make_name_without_spaces
from ...viscera.testing import bind
from ...viscera.machines import Machine, Machines
from ...viscera.resource_pools import ResourcePool
from ...viscera.tags import Tag, Tags
from ...viscera.users import User
from ...viscera.zones import Zone


def make_origin():
    """Make origin for machines."""
    return bind(Machines, Machine, User, ResourcePool, Zone, Tag, Tags)


class TestMachines(TestCaseWithProfile):
    """Tests for `cmd_machines`."""

    def test_returns_table_with_machines(self):
        origin = make_origin()
        parser = ArgumentParser()
        machine_objs = [
            {
                "hostname": make_name_without_spaces(),
                "architecture": "amd64/generic",
                "status": NodeStatus.READY.value,
                "status_name": NodeStatus.READY.name,
                "owner": None,
                "power_state": PowerState.OFF.value,
                "cpu_count": 2,
                "memory": 1024,
                "pool": {"id": 1, "name": "pool1", "description": "pool1"},
                "zone": {"id": 1, "name": "zone1", "description": "zone1"},
            },
            {
                "hostname": make_name_without_spaces(),
                "architecture": "i386/generic",
                "status": NodeStatus.DEPLOYED.value,
                "status_name": NodeStatus.DEPLOYED.name,
                "owner": make_name_without_spaces(),
                "power_state": PowerState.ON.value,
                "cpu_count": 4,
                "memory": 4096,
                "pool": {"id": 2, "name": "pool2", "description": "pool2"},
                "zone": {"id": 2, "name": "zone2", "description": "zone2"},
            },
        ]
        origin.Machines._handler.read.return_value = machine_objs
        cmd = machines.cmd_machines(parser)
        subparser = machines.cmd_machines.register(parser)
        options = subparser.parse_args([])
        output = yaml.safe_load(
            cmd.execute(origin, options, target=tabular.RenderTarget.yaml)
        )
        self.assertEqual(
            [
                {"name": "hostname", "title": "Hostname"},
                {"name": "power", "title": "Power"},
                {"name": "status", "title": "Status"},
                {"name": "owner", "title": "Owner"},
                {"name": "architecture", "title": "Arch"},
                {"name": "cpus", "title": "#CPUs"},
                {"name": "memory", "title": "RAM"},
                {"name": "pool", "title": "Resource pool"},
                {"name": "zone", "title": "Zone"},
            ],
            output["columns"],
        )
        machines_output = sorted(
            [
                {
                    "hostname": machine["hostname"],
                    "power": machine["power_state"],
                    "status": machine["status_name"],
                    "owner": machine["owner"] if machine["owner"] else "(none)",
                    "architecture": machine["architecture"],
                    "cpus": machine["cpu_count"],
                    "memory": machine["memory"],
                    "pool": machine["pool"]["name"],
                    "zone": machine["zone"]["name"],
                }
                for machine in machine_objs
            ],
            key=itemgetter("hostname"),
        )
        self.assertEqual(machines_output, output["data"])

    def test_calls_handler_with_hostnames(self):
        origin = make_origin()
        parser = ArgumentParser()
        origin.Machines._handler.read.return_value = []
        subparser = machines.cmd_machines.register(parser)
        cmd = machines.cmd_machines(parser)
        hostnames = [make_name_without_spaces() for _ in range(3)]
        options = subparser.parse_args(hostnames)
        cmd.execute(origin, options, target=tabular.RenderTarget.yaml)
        origin.Machines._handler.read.assert_called_once_with(hostname=hostnames)


class TestMachine(TestCaseWithProfile):
    """Tests for `cmd_machine`."""

    def setUp(self):
        super().setUp()
        origin = make_origin()
        parser = ArgumentParser()
        self.hostname = make_name_without_spaces()
        machine_objs = [
            {
                "hostname": self.hostname,
                "architecture": "amd64/generic",
                "status": NodeStatus.READY.value,
                "status_name": NodeStatus.READY.name,
                "owner": None,
                "power_state": PowerState.OFF.value,
                "cpu_count": 2,
                "memory": 1024,
                "pool": {"id": 1, "name": "pool1", "description": "pool1"},
                "zone": {"id": 1, "name": "zone1", "description": "zone1"},
                "tag_names": ["tag1", "tag2"],
                "distro_series": "",
                "power_type": "Manual",
            },
        ]
        origin.Machines._handler.read.return_value = machine_objs
        cmd = machines.cmd_machine(parser)
        subparser = machines.cmd_machine.register(parser)
        options = subparser.parse_args([machine_objs[0]["hostname"]])
        self.cmd = partial(cmd.execute, origin, options)

    def test_yaml_machine_details_with_tags(self):
        yaml_output = yaml.safe_load(self.cmd(target=tabular.RenderTarget.yaml))
        self.assertEqual(yaml_output.get("tags"), ["tag1", "tag2"])

    def test_plain_machine_details_with_tags(self):
        plain_output = self.cmd(target=tabular.RenderTarget.plain)
        self.assertEqual(
            plain_output,
            f"""\
+---------------+-------------+
| Hostname      | {self.hostname} |
| Status        | READY       |
| Image         | (none)      |
| Power         | Off         |
| Power Type    | Manual      |
| Arch          | amd64       |
| #CPUs         | 2           |
| RAM           | 1.0 GB      |
| Interfaces    | 0 physical  |
| IP addresses  |             |
| Resource pool | pool1       |
| Zone          | zone1       |
| Owner         | (none)      |
| Tags          | tag1        |
|               | tag2        |
+---------------+-------------+""",
        )
