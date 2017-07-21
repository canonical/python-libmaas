"""Test for `maas.client.viscera.machines`."""

from http import HTTPStatus
from unittest.mock import Mock
from xml.etree import ElementTree

from maas.client.bones.testing.server import ApplicationBuilder
from maas.client.utils.testing import make_Credentials
from maas.client.viscera import Origin
from testtools.matchers import (
    ContainsDict,
    Equals,
    IsInstance,
    MatchesStructure,
)

from .. import machines
from ...bones import CallError
from ...bones.testing import api_descriptions
from ...errors import OperationNotAllowed
from ...testing import (
    make_name_without_spaces,
    TestCase,
)
from ..testing import bind
from ...enum import NodeStatus


def make_origin():
    # Create a new origin with Machines and Machine. The former refers to the
    # latter via the origin, hence why it must be bound.
    return bind(machines.Machines, machines.Machine)


def make_get_details_coroutine(system_id, return_value=''):
    async def coroutine(system_id):
        return return_value
    return coroutine


class TestMachine(TestCase):

    def test__string_representation_includes_only_system_id_and_hostname(self):
        machine = machines.Machine({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        })
        self.assertThat(repr(machine), Equals(
            "<Machine hostname=%(hostname)r system_id=%(system_id)r>"
            % machine._data))

    def test__get_power_parameters(self):
        machine = make_origin().Machine({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        })
        power_parameters = {
            "key": make_name_without_spaces("value"),
        }
        machine._handler.power_parameters.return_value = power_parameters
        self.assertThat(
            machine.get_power_parameters(),
            Equals(power_parameters),
        )
        machine._handler.power_parameters.assert_called_once_with(
            system_id=machine.system_id
        )

    def test__abort(self):
        data = {
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        }
        origin = make_origin()
        machine = origin.Machine(data)
        machine._handler.abort.return_value = data
        comment = make_name_without_spaces("comment")
        self.assertThat(
            machine.abort(comment=comment),
            Equals(origin.Machine(data)))
        machine._handler.abort.assert_called_once_with(
            system_id=machine.system_id, comment=comment)

    def test__clear_default_gateways(self):
        data = {
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        }
        origin = make_origin()
        machine = origin.Machine(data)
        machine._handler.clear_default_gateways.return_value = data
        self.assertThat(
            machine.clear_default_gateways(),
            Equals(origin.Machine(data)))
        machine._handler.clear_default_gateways.assert_called_once_with(
            system_id=machine.system_id)

    def test__commissioning_without_wait(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.COMMISSIONING,
        }
        machine = make_origin().Machine(data)
        machine._handler.commission.return_value = data
        machine.commission()
        self.assertThat(machine.status, Equals(NodeStatus.COMMISSIONING))
        machine._handler.commission.assert_called_once_with(
            system_id=machine.system_id
        )

    def test__commissioning_with_wait(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.COMMISSIONING,
        }
        ready_data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.READY,
        }
        machine = make_origin().Machine(data)
        machine._handler.commission.return_value = data
        machine._handler.read.return_value = ready_data
        machine.commission(wait=True, wait_interval=0.1)
        self.assertThat(machine.status, Equals(NodeStatus.READY))
        machine._handler.commission.assert_called_once_with(
            system_id=machine.system_id
        )

    def test__commissioning_and_testing_with_wait(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.COMMISSIONING,
        }
        testing_data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.TESTING,
        }
        ready_data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.READY,
        }
        machine = make_origin().Machine(data)
        machine._handler.commission.return_value = data
        machine._handler.read.side_effect = [
            testing_data,
            ready_data,
        ]
        machine.commission(wait=True, wait_interval=0.1)
        self.assertThat(machine.status, Equals(NodeStatus.READY))
        machine._handler.commission.assert_called_once_with(
            system_id=machine.system_id
        )

    def test__commission_with_wait_failed(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.COMMISSIONING,
        }
        failed_commissioning_data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.FAILED_COMMISSIONING,
        }
        machine = make_origin().Machine(data)
        machine._handler.commission.return_value = data
        machine._handler.read.return_value = failed_commissioning_data
        self.assertRaises(machines.FailedCommissioning, machine.commission,
                          wait=True, wait_interval=0.1)

    def test__deploy_with_wait(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.DEPLOYING,
        }
        deployed_data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.DEPLOYED,
        }
        machine = make_origin().Machine(data)
        machine._handler.deploy.return_value = data
        machine._handler.read.return_value = deployed_data
        machine.deploy(wait=True, wait_interval=0.1)
        self.assertThat(machine.status, Equals(NodeStatus.DEPLOYED))
        machine._handler.deploy.assert_called_once_with(
            system_id=machine.system_id
        )

    def test__deploy_with_wait_failed(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.DEPLOYING,
        }
        failed_deploy_data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.FAILED_DEPLOYMENT,
        }
        machine = make_origin().Machine(data)
        machine._handler.deploy.return_value = data
        machine._handler.read.return_value = failed_deploy_data
        self.assertRaises(machines.FailedDeployment, machine.deploy,
                          wait=True, wait_interval=0.1)

    def test__enter_rescue_mode(self):
        rescue_mode_machine = {
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "status": NodeStatus.ENTERING_RESCUE_MODE,
        }
        machine = make_origin().Machine(rescue_mode_machine)
        machine._handler.rescue_mode.return_value = rescue_mode_machine
        self.assertThat(
            machine.enter_rescue_mode(),
            Equals(machine),
        )
        machine._handler.rescue_mode.assert_called_once_with(
            system_id=machine.system_id
        )

    def test__enter_rescue_mode_operation_not_allowed(self):
        machine = make_origin().Machine({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        })
        # Mock the call to content.decode in the CallError constructor
        content = Mock()
        content.decode = Mock(return_value='')
        machine._handler.rescue_mode.side_effect = CallError(
            request={"method": "GET", "uri": "www.example.com"},
            response=Mock(status=HTTPStatus.FORBIDDEN),
            content=content,
            call='',
        )
        self.assertRaises(OperationNotAllowed, machine.enter_rescue_mode)

    def test__enter_rescue_mode_with_wait(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        rm_data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.ENTERING_RESCUE_MODE,
        }
        erm_data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.RESCUE_MODE,
        }
        rm_machine = make_origin().Machine(rm_data)
        erm_machine = make_origin().Machine(erm_data)
        rm_machine._handler.rescue_mode.return_value = rm_data
        rm_machine._handler.read.return_value = erm_data
        result = rm_machine.enter_rescue_mode(wait=True, wait_interval=0.1)
        self.assertThat(result.status, Equals(erm_machine.status))
        rm_machine._handler.rescue_mode.assert_called_once_with(
            system_id=rm_machine.system_id
        )

    def test__enter_rescue_mode_with_wait_failed(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.ENTERING_RESCUE_MODE,
        }
        failed_enter_rescue_mode_data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.FAILED_ENTERING_RESCUE_MODE,
        }
        machine = make_origin().Machine(data)
        machine._handler.rescue_mode.return_value = data
        machine._handler.read.return_value = failed_enter_rescue_mode_data
        self.assertRaises(
            machines.RescueModeFailure,
            machine.enter_rescue_mode, wait=True, wait_interval=0.1
        )

    def test__exit_rescue_mode(self):
        exit_machine = {
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "status": NodeStatus.EXITING_RESCUE_MODE,
        }
        machine = make_origin().Machine(exit_machine)
        machine._handler.exit_rescue_mode.return_value = exit_machine
        self.assertThat(
            machine.exit_rescue_mode(),
            Equals(machine),
        )
        machine._handler.exit_rescue_mode.assert_called_once_with(
            system_id=machine.system_id
        )

    def test__exit_rescue_mode_operation_not_allowed(self):
        machine = make_origin().Machine({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        })
        # Mock the call to content.decode in the CallError constructor
        content = Mock()
        content.decode = Mock(return_value='')
        machine._handler.exit_rescue_mode.side_effect = CallError(
            request={"method": "GET", "uri": "www.example.com"},
            response=Mock(status=HTTPStatus.FORBIDDEN),
            content=content,
            call='',
        )
        self.assertRaises(OperationNotAllowed, machine.exit_rescue_mode)

    def test__exit_rescue_mode_with_wait(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.EXITING_RESCUE_MODE,
        }
        deployed_data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.DEPLOYED,
        }
        machine = make_origin().Machine(data)
        deployed_machine = make_origin().Machine(deployed_data)
        machine._handler.exit_rescue_mode.return_value = data
        machine._handler.read.return_value = deployed_data
        result = machine.exit_rescue_mode(wait=True, wait_interval=0.1)
        self.assertThat(result.status, Equals(deployed_machine.status))
        machine._handler.exit_rescue_mode.assert_called_once_with(
            system_id=machine.system_id
        )

    def test__exit_rescue_mode_with_wait_failed(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.EXITING_RESCUE_MODE,
        }
        failed_exit_rescue_mode_data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.FAILED_EXITING_RESCUE_MODE,
        }
        machine = make_origin().Machine(data)
        machine._handler.exit_rescue_mode.return_value = data
        machine._handler.read.return_value = failed_exit_rescue_mode_data
        self.assertRaises(
            machines.RescueModeFailure,
            machine.exit_rescue_mode, wait=True, wait_interval=0.1
        )

    def test__get_curtin_config(self):
        data = {
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        }
        origin = make_origin()
        machine = origin.Machine(data)
        config = make_name_without_spaces("config")
        machine._handler.get_curtin_config.return_value = config
        self.assertThat(
            machine.get_curtin_config(),
            Equals(config))
        machine._handler.get_curtin_config.assert_called_once_with(
            system_id=machine.system_id)

    def test__mark_broken(self):
        data = {
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        }
        origin = make_origin()
        machine = origin.Machine(data)
        machine._handler.mark_broken.return_value = data
        comment = make_name_without_spaces("comment")
        self.assertThat(
            machine.mark_broken(comment=comment),
            Equals(origin.Machine(data)))
        machine._handler.mark_broken.assert_called_once_with(
            system_id=machine.system_id, comment=comment)

    def test__mark_fixed(self):
        data = {
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        }
        origin = make_origin()
        machine = origin.Machine(data)
        machine._handler.mark_fixed.return_value = data
        comment = make_name_without_spaces("comment")
        self.assertThat(
            machine.mark_fixed(comment=comment),
            Equals(origin.Machine(data)))
        machine._handler.mark_fixed.assert_called_once_with(
            system_id=machine.system_id, comment=comment)

    def test__release_with_wait(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.RELEASING,
        }
        allocated_data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.ALLOCATED,
        }
        machine = make_origin().Machine(data)
        allocated_machine = make_origin().Machine(allocated_data)
        machine._handler.release.return_value = data
        machine._handler.read.return_value = allocated_data
        result = machine.release(wait=True, wait_interval=0.1)
        self.assertThat(result.status, Equals(allocated_machine.status))
        machine._handler.release.assert_called_once_with(
            system_id=machine.system_id
        )

    def test__release_with_wait_failed(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.RELEASING,
        }
        failed_release_data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.FAILED_RELEASING,
        }
        machine = make_origin().Machine(data)
        machine._handler.release.return_value = data
        machine._handler.read.return_value = failed_release_data
        self.assertRaises(
            machines.FailedReleasing,
            machine.release,
            wait=True,
            wait_interval=0.1
        )

    def test__release_with_wait_failed_disk_erasing(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.RELEASING,
        }
        failed_disk_erase_data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.FAILED_DISK_ERASING,
        }
        machine = make_origin().Machine(data)
        machine._handler.release.return_value = data
        machine._handler.read.return_value = failed_disk_erase_data
        self.assertRaises(
            machines.FailedDiskErasing,
            machine.release,
            wait=True,
            wait_interval=0.1
        )

    def test__get_details(self):
        return_val = b'S\x01\x00\x00\x05lshw\x00\xf2\x00\x00\x00\x00<?xml' \
                     b' version="1.0" standalone="yes" ?>\n<!-- generated by' \
                     b' lshw-B.02.17 -->\n<!-- GCC 5.3.1 20160413 -->\n<!--' \
                     b' Linux 4.8.0-34-generic #36~16.04.1-Ubuntu SMP Wed' \
                     b' Dec 21 18:55:08 UTC 2016 x86_64 -->\n<!-- GNU libc 2' \
                     b' (glibc 2.23) -->\n<list>\n</list>\n\x05lldp\x00F\x00' \
                     b'\x00\x00\x00<?xml version="1.0" encoding="UTF-8"?>\n' \
                     b'<lldp label="LLDP neighbors"/>\n\x00'
        machine = make_origin().Machine({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        })
        machine._handler.details = make_get_details_coroutine(
            machine.system_id,
            return_value=return_val
            )
        data = machine.get_details()
        self.assertItemsEqual(['lldp', 'lshw'], data.keys())
        lldp = ElementTree.fromstring(data['lldp'])
        lshw = ElementTree.fromstring(data['lshw'])
        assert IsInstance(lldp, ElementTree)
        assert IsInstance(lshw, ElementTree)


class TestMachine_APIVersion(TestCase):

    scenarios = tuple(
        (name, dict(version=version, description=description))
        for name, version, description in api_descriptions)

    async def test__deploy(self):
        builder = ApplicationBuilder(self.description)

        @builder.handle("auth:Machine.deploy")
        async def deploy(request, system_id):
            self.assertThat(request.params, ContainsDict({
                "distro_series": Equals("ubuntu/xenial"),
                "hwe_kernel": Equals("hwe-x"),
            }))
            return {
                "system_id": system_id,
                "status_name": "Deploying",
            }

        async with builder.serve() as baseurl:
            origin = await Origin.fromURL(
                baseurl, credentials=make_Credentials())
            machine = origin.Machine({
                "system_id": make_name_without_spaces("system-id"),
            })
            machine = await machine.deploy(
                distro_series='ubuntu/xenial',
                hwe_kernel='hwe-x',
            )
            self.assertThat(
                machine, MatchesStructure.byEquality(
                    status_name="Deploying"))


class TestMachines(TestCase):

    def test__create(self):
        origin = make_origin()
        Machines, Machine = origin.Machines, origin.Machine
        Machines._handler.create.return_value = {}
        observed = Machines.create(
            'amd64',
            ['00:11:22:33:44:55', '00:11:22:33:44:AA'],
            'ipmi',
            {'power_address': 'localhost', 'power_user': 'root'},
            subarchitecture='generic', min_hwe_kernel='hwe-x',
            hostname='new-machine', domain='maas')
        self.assertThat(observed, IsInstance(Machine))
        Machines._handler.create.assert_called_once_with(
            architecture='amd64',
            mac_addresses=['00:11:22:33:44:55', '00:11:22:33:44:AA'],
            power_type='ipmi',
            power_parameters={
                'power_address': 'localhost', 'power_user': 'root'},
            subarchitecture='generic',
            min_hwe_kernel='hwe-x',
            hostname='new-machine',
            domain='maas')

    def test__allocate(self):
        Machines = make_origin().Machines
        Machines._handler.allocate.return_value = {}
        hostname = make_name_without_spaces("hostname")
        Machines.allocate(
            hostname=hostname,
            architecture='amd64/generic',
            cpus=4,
            memory=1024.0,
            tags=['foo', 'bar', '-baz'],
        )
        Machines._handler.allocate.assert_called_once_with(
            name=hostname,  # API parameter is actually name, not hostname
            architecture='amd64/generic',
            cpu_count='4',
            mem='1024.0',
            tags=['foo', 'bar'],
            not_tags=['baz'],
        )

    def test__get_power_parameters_for_with_empty_list(self):
        Machines = make_origin().Machines
        self.assertThat(
            Machines.get_power_parameters_for(system_ids=[]),
            Equals({}),
        )

    def test__get_power_parameters_for_with_system_ids(self):
        power_parameters = {
            make_name_without_spaces("system_id"): {
                "key": make_name_without_spaces("value")
            }
            for _ in range(3)
        }
        Machines = make_origin().Machines
        Machines._handler.power_parameters.return_value = power_parameters
        self.assertThat(
            Machines.get_power_parameters_for(
                system_ids=power_parameters.keys()
            ),
            Equals(power_parameters)
        )
        Machines._handler.power_parameters.assert_called_once_with(
            id=power_parameters.keys()
        )
