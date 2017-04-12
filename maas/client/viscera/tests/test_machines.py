"""Test for `maas.client.viscera.machines`."""

from http import HTTPStatus
from unittest.mock import Mock

from maas.client.bones.testing.server import ApplicationBuilder
from maas.client.utils.testing import make_Credentials
from maas.client.viscera import Origin
from testtools.matchers import (
    ContainsDict,
    Equals,
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


class TestMachine(TestCase):

    def test__string_representation_includes_only_system_id_and_hostname(self):
        machine = machines.Machine({
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        })
        self.assertThat(repr(machine), Equals(
            "<Machine hostname=%(hostname)r system_id=%(system_id)r>"
            % machine._data))

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
        deployed_machine = make_origin().Machine(deployed_data)
        machine._handler.deploy.return_value = data
        machine._handler.read.return_value = deployed_data
        result = machine.deploy(wait=True, wait_interval=0.1)
        self.assertThat(result.status, Equals(deployed_machine.status))
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
