"""Test for `maas.client.viscera.machines`."""

import random
from http import HTTPStatus
from unittest.mock import Mock
from xml.etree import ElementTree

from maas.client.bones.testing.server import ApplicationBuilder
from maas.client.utils.testing import make_Credentials
from maas.client.viscera import Origin
from testtools.matchers import ContainsDict, Equals, IsInstance, MatchesStructure

from .. import machines
from ..testing import bind
from ...bones import CallError
from ...bones.testing import api_descriptions
from ...enum import NodeStatus, PowerState, PowerStopMode
from ...errors import OperationNotAllowed
from ...testing import make_name_without_spaces, TestCase
from ..pods import Pod, Pods


def make_pods_origin():
    """
    Create a new origin with Pods and Pod. The former
    refers to the latter via the origin, hence why it must be bound.
    """
    return bind(Pods, Pod)


def make_machines_origin():
    """
    Create a new origin with Machines and Machine. The former
    refers to the latter via the origin, hence why it must be bound.
    """
    return bind(machines.Machines, machines.Machine)


def make_get_details_coroutine(system_id, return_value=""):
    async def coroutine(system_id):
        return return_value

    return coroutine


class TestMachine(TestCase):
    def test__string_representation_includes_only_system_id_and_hostname(self):
        machine = machines.Machine(
            {
                "system_id": make_name_without_spaces("system-id"),
                "hostname": make_name_without_spaces("hostname"),
            }
        )
        self.assertThat(
            repr(machine),
            Equals(
                "<Machine hostname=%(hostname)r system_id=%(system_id)r>"
                % machine._data
            ),
        )

    def test__get_power_parameters(self):
        machine = make_machines_origin().Machine(
            {
                "system_id": make_name_without_spaces("system-id"),
                "hostname": make_name_without_spaces("hostname"),
            }
        )
        power_parameters = {"key": make_name_without_spaces("value")}
        machine._handler.power_parameters.return_value = power_parameters
        self.assertThat(machine.get_power_parameters(), Equals(power_parameters))
        machine._handler.power_parameters.assert_called_once_with(
            system_id=machine.system_id
        )

    def test__set_power(self):
        orig_power_type = make_name_without_spaces("power_type")
        new_power_type = make_name_without_spaces("power_type")
        machine = make_machines_origin().Machine(
            {
                "system_id": make_name_without_spaces("system-id"),
                "hostname": make_name_without_spaces("hostname"),
                "power_type": orig_power_type,
            }
        )
        power_parameters = {"key": make_name_without_spaces("value")}
        machine._handler.update.return_value = {"power_type": new_power_type}
        machine.set_power(new_power_type, power_parameters)
        machine._handler.update.assert_called_once_with(
            system_id=machine.system_id,
            power_type=new_power_type,
            power_parameters=power_parameters,
        )
        self.assertThat(machine.power_type, Equals(new_power_type))

    def test__abort(self):
        data = {
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        }
        origin = make_machines_origin()
        machine = origin.Machine(data)
        machine._handler.abort.return_value = data
        comment = make_name_without_spaces("comment")
        self.assertThat(machine.abort(comment=comment), Equals(origin.Machine(data)))
        machine._handler.abort.assert_called_once_with(
            system_id=machine.system_id, comment=comment
        )

    def test__clear_default_gateways(self):
        data = {
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        }
        origin = make_machines_origin()
        machine = origin.Machine(data)
        machine._handler.clear_default_gateways.return_value = data
        self.assertThat(machine.clear_default_gateways(), Equals(origin.Machine(data)))
        machine._handler.clear_default_gateways.assert_called_once_with(
            system_id=machine.system_id
        )

    def test__commissioning_without_wait(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.COMMISSIONING,
        }
        machine = make_machines_origin().Machine(data)
        machine._handler.commission.return_value = data
        machine.commission()
        self.assertThat(machine.status, Equals(NodeStatus.COMMISSIONING))
        machine._handler.commission.assert_called_once_with(system_id=machine.system_id)

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
        machine = make_machines_origin().Machine(data)
        machine._handler.commission.return_value = data
        machine._handler.read.return_value = ready_data
        machine.commission(wait=True, wait_interval=0.1)
        self.assertThat(machine.status, Equals(NodeStatus.READY))
        machine._handler.commission.assert_called_once_with(system_id=machine.system_id)

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
        machine = make_machines_origin().Machine(data)
        machine._handler.commission.return_value = data
        machine._handler.read.side_effect = [testing_data, ready_data]
        machine.commission(wait=True, wait_interval=0.1)
        self.assertThat(machine.status, Equals(NodeStatus.READY))
        machine._handler.commission.assert_called_once_with(system_id=machine.system_id)

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
        machine = make_machines_origin().Machine(data)
        machine._handler.commission.return_value = data
        machine._handler.read.return_value = failed_commissioning_data
        self.assertRaises(
            machines.FailedCommissioning,
            machine.commission,
            wait=True,
            wait_interval=0.1,
        )

    def test__commission_with_no_tests(self):
        # Regression test for https://github.com/canonical/python-libmaas/issues/185
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.COMMISSIONING,
        }
        machine = make_machines_origin().Machine(data)
        machine._handler.commission.return_value = data
        machine.commission(testing_scripts=random.choice(["", [], "none"]))
        self.assertThat(machine.status, Equals(NodeStatus.COMMISSIONING))
        machine._handler.commission.assert_called_once_with(
            system_id=machine.system_id, testing_scripts=["none"]
        )

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
        machine = make_machines_origin().Machine(data)
        machine._handler.deploy.return_value = data
        machine._handler.read.return_value = deployed_data
        machine.deploy(wait=True, wait_interval=0.1)
        self.assertThat(machine.status, Equals(NodeStatus.DEPLOYED))
        machine._handler.deploy.assert_called_once_with(system_id=machine.system_id)

    def test__deploy_with_kvm_install(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.READY,
        }
        deploying_data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.DEPLOYING,
        }
        machine = make_machines_origin().Machine(data)
        machine._handler.deploy.return_value = deploying_data
        machine.deploy(install_kvm=True, wait=False)
        machine._handler.deploy.assert_called_once_with(
            system_id=machine.system_id, install_kvm=True
        )

    def test__deploy_with_ephemeral_deploy(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.READY,
        }
        deploying_data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.DEPLOYING,
        }
        machine = make_machines_origin().Machine(data)
        machine._handler.deploy.return_value = deploying_data
        machine.deploy(ephemeral_deploy=True, wait=False)
        machine._handler.deploy.assert_called_once_with(
            system_id=machine.system_id, ephemeral_deploy=True
        )

    def test__deploy_with_enable_hw_sync(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.READY,
        }
        deploying_data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.DEPLOYING,
        }
        machine = make_machines_origin().Machine(data)
        machine._handler.deploy.return_value = deploying_data
        machine.deploy(enable_hw_sync=True, wait=False)
        machine._handler.deploy.assert_called_once_with(
            system_id=machine.system_id, enable_hw_sync=True
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
        machine = make_machines_origin().Machine(data)
        machine._handler.deploy.return_value = data
        machine._handler.read.return_value = failed_deploy_data
        self.assertRaises(
            machines.FailedDeployment, machine.deploy, wait=True, wait_interval=0.1
        )

    def test__enter_rescue_mode(self):
        rescue_mode_machine = {
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "status": NodeStatus.ENTERING_RESCUE_MODE,
        }
        machine = make_machines_origin().Machine(rescue_mode_machine)
        machine._handler.rescue_mode.return_value = rescue_mode_machine
        self.assertThat(machine.enter_rescue_mode(), Equals(machine))
        machine._handler.rescue_mode.assert_called_once_with(
            system_id=machine.system_id
        )

    def test__enter_rescue_mode_operation_not_allowed(self):
        machine = make_machines_origin().Machine(
            {
                "system_id": make_name_without_spaces("system-id"),
                "hostname": make_name_without_spaces("hostname"),
            }
        )
        # Mock the call to content.decode in the CallError constructor
        content = Mock()
        content.decode = Mock(return_value="")
        machine._handler.rescue_mode.side_effect = CallError(
            request={"method": "GET", "uri": "www.example.com"},
            response=Mock(status=HTTPStatus.FORBIDDEN),
            content=content,
            call="",
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
        rm_machine = make_machines_origin().Machine(rm_data)
        erm_machine = make_machines_origin().Machine(erm_data)
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
        machine = make_machines_origin().Machine(data)
        machine._handler.rescue_mode.return_value = data
        machine._handler.read.return_value = failed_enter_rescue_mode_data
        self.assertRaises(
            machines.RescueModeFailure,
            machine.enter_rescue_mode,
            wait=True,
            wait_interval=0.1,
        )

    def test__exit_rescue_mode(self):
        exit_machine = {
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
            "status": NodeStatus.EXITING_RESCUE_MODE,
        }
        machine = make_machines_origin().Machine(exit_machine)
        machine._handler.exit_rescue_mode.return_value = exit_machine
        self.assertThat(machine.exit_rescue_mode(), Equals(machine))
        machine._handler.exit_rescue_mode.assert_called_once_with(
            system_id=machine.system_id
        )

    def test__exit_rescue_mode_operation_not_allowed(self):
        machine = make_machines_origin().Machine(
            {
                "system_id": make_name_without_spaces("system-id"),
                "hostname": make_name_without_spaces("hostname"),
            }
        )
        # Mock the call to content.decode in the CallError constructor
        content = Mock()
        content.decode = Mock(return_value="")
        machine._handler.exit_rescue_mode.side_effect = CallError(
            request={"method": "GET", "uri": "www.example.com"},
            response=Mock(status=HTTPStatus.FORBIDDEN),
            content=content,
            call="",
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
        machine = make_machines_origin().Machine(data)
        deployed_machine = make_machines_origin().Machine(deployed_data)
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
        machine = make_machines_origin().Machine(data)
        machine._handler.exit_rescue_mode.return_value = data
        machine._handler.read.return_value = failed_exit_rescue_mode_data
        self.assertRaises(
            machines.RescueModeFailure,
            machine.exit_rescue_mode,
            wait=True,
            wait_interval=0.1,
        )

    def test__get_curtin_config(self):
        data = {
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        }
        origin = make_machines_origin()
        machine = origin.Machine(data)
        config = make_name_without_spaces("config")
        machine._handler.get_curtin_config.return_value = config
        self.assertThat(machine.get_curtin_config(), Equals(config))
        machine._handler.get_curtin_config.assert_called_once_with(
            system_id=machine.system_id
        )

    def test__mark_broken(self):
        data = {
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        }
        origin = make_machines_origin()
        machine = origin.Machine(data)
        machine._handler.mark_broken.return_value = data
        comment = make_name_without_spaces("comment")
        self.assertThat(
            machine.mark_broken(comment=comment), Equals(origin.Machine(data))
        )
        machine._handler.mark_broken.assert_called_once_with(
            system_id=machine.system_id, comment=comment
        )

    def test__mark_fixed(self):
        data = {
            "system_id": make_name_without_spaces("system-id"),
            "hostname": make_name_without_spaces("hostname"),
        }
        origin = make_machines_origin()
        machine = origin.Machine(data)
        machine._handler.mark_fixed.return_value = data
        comment = make_name_without_spaces("comment")
        self.assertThat(
            machine.mark_fixed(comment=comment), Equals(origin.Machine(data))
        )
        machine._handler.mark_fixed.assert_called_once_with(
            system_id=machine.system_id, comment=comment
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
        machine = make_machines_origin().Machine(data)
        allocated_machine = make_machines_origin().Machine(allocated_data)
        machine._handler.release.return_value = data
        machine._handler.read.return_value = allocated_data
        result = machine.release(wait=True, wait_interval=0.1)
        self.assertThat(result.status, Equals(allocated_machine.status))
        machine._handler.release.assert_called_once_with(system_id=machine.system_id)

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
        machine = make_machines_origin().Machine(data)
        machine._handler.release.return_value = data
        machine._handler.read.return_value = failed_release_data
        self.assertRaises(
            machines.FailedReleasing, machine.release, wait=True, wait_interval=0.1
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
        machine = make_machines_origin().Machine(data)
        machine._handler.release.return_value = data
        machine._handler.read.return_value = failed_disk_erase_data
        self.assertRaises(
            machines.FailedDiskErasing, machine.release, wait=True, wait_interval=0.1
        )

    def test__release_with_deleted_machine(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "status": NodeStatus.RELEASING,
        }
        machine = make_machines_origin().Machine(data)
        machine._handler.release.return_value = data
        machine._handler.read.side_effect = CallError(
            request={"method": "GET", "uri": "www.example.com"},
            response=Mock(status=HTTPStatus.NOT_FOUND),
            content=b"",
            call="",
        )
        result = machine.release(wait=True, wait_interval=0.1)
        self.assertThat(result.status, Equals(NodeStatus.RELEASING))
        machine._handler.release.assert_called_once_with(system_id=machine.system_id)

    def test__power_on_with_wait(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "power_state": PowerState.OFF,
        }
        power_data = {
            "system_id": system_id,
            "hostname": hostname,
            "power_state": PowerState.ON,
        }
        machine = make_machines_origin().Machine(data)
        powered_machine = make_machines_origin().Machine(power_data)
        machine._handler.power_on.return_value = data
        machine._handler.read.return_value = power_data
        result = machine.power_on(wait=True, wait_interval=0.1)
        self.assertThat(result.power_state, Equals(powered_machine.power_state))
        machine._handler.power_on.assert_called_once_with(system_id=machine.system_id)

    def test__power_on_doesnt_wait_for_unknown(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "power_state": PowerState.UNKNOWN,
        }
        power_data = {
            "system_id": system_id,
            "hostname": hostname,
            "power_state": PowerState.UNKNOWN,
        }
        machine = make_machines_origin().Machine(data)
        powered_machine = make_machines_origin().Machine(power_data)
        machine._handler.power_on.return_value = data
        machine._handler.read.return_value = power_data
        result = machine.power_on(wait=True, wait_interval=0.1)
        self.assertThat(result.power_state, Equals(powered_machine.power_state))
        assert machine._handler.read.call_count == 0

    def test__power_on_with_wait_failed(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "power_state": PowerState.OFF,
        }
        failed_power_data = {
            "system_id": system_id,
            "hostname": hostname,
            "power_state": PowerState.ERROR,
        }
        machine = make_machines_origin().Machine(data)
        machine._handler.power_on.return_value = data
        machine._handler.read.return_value = failed_power_data
        self.assertRaises(
            machines.PowerError, machine.power_on, wait=True, wait_interval=0.1
        )

    def test__power_off_with_wait(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "power_state": PowerState.ON,
        }
        power_data = {
            "system_id": system_id,
            "hostname": hostname,
            "power_state": PowerState.OFF,
        }
        machine = make_machines_origin().Machine(data)
        powered_machine = make_machines_origin().Machine(power_data)
        machine._handler.power_off.return_value = data
        machine._handler.read.return_value = power_data
        result = machine.power_off(wait=True, wait_interval=0.1)
        self.assertThat(result.power_state, Equals(powered_machine.power_state))
        machine._handler.power_off.assert_called_once_with(
            system_id=machine.system_id, stop_mode=PowerStopMode.HARD.value
        )

    def test__power_off_soft_mode(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "power_state": PowerState.ON,
        }
        machine = make_machines_origin().Machine(data)
        machine._handler.power_off.return_value = data
        machine.power_off(stop_mode=PowerStopMode.SOFT, wait=False)
        machine._handler.power_off.assert_called_once_with(
            system_id=machine.system_id, stop_mode=PowerStopMode.SOFT.value
        )

    def test__power_off_doesnt_wait_for_unknown(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "power_state": PowerState.UNKNOWN,
        }
        power_data = {
            "system_id": system_id,
            "hostname": hostname,
            "power_state": PowerState.UNKNOWN,
        }
        machine = make_machines_origin().Machine(data)
        powered_machine = make_machines_origin().Machine(power_data)
        machine._handler.power_off.return_value = data
        machine._handler.read.return_value = power_data
        result = machine.power_off(wait=True, wait_interval=0.1)
        self.assertThat(result.power_state, Equals(powered_machine.power_state))
        self.assertThat(machine._handler.read.call_count, Equals(0))

    def test__power_off_with_wait_failed(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "power_state": PowerState.ON,
        }
        failed_power_data = {
            "system_id": system_id,
            "hostname": hostname,
            "power_state": PowerState.ERROR,
        }
        machine = make_machines_origin().Machine(data)
        machine._handler.power_off.return_value = data
        machine._handler.read.return_value = failed_power_data
        self.assertRaises(
            machines.PowerError, machine.power_off, wait=True, wait_interval=0.1
        )

    def test__query_power_state(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "power_state": PowerState.OFF,
        }
        query_data = {"state": "on"}
        machine = make_machines_origin().Machine(data)
        machine._handler.query_power_state.return_value = query_data
        result = machine.query_power_state()
        self.assertIsInstance(result, PowerState)
        self.assertEquals(PowerState.ON, result)
        self.assertEqual(PowerState.ON, machine.power_state)

    def test__get_details(self):
        return_val = (
            b"S\x01\x00\x00\x05lshw\x00\xf2\x00\x00\x00\x00<?xml"
            b' version="1.0" standalone="yes" ?>\n<!-- generated by'
            b" lshw-B.02.17 -->\n<!-- GCC 5.3.1 20160413 -->\n<!--"
            b" Linux 4.8.0-34-generic #36~16.04.1-Ubuntu SMP Wed"
            b" Dec 21 18:55:08 UTC 2016 x86_64 -->\n<!-- GNU libc 2"
            b" (glibc 2.23) -->\n<list>\n</list>\n\x05lldp\x00F\x00"
            b'\x00\x00\x00<?xml version="1.0" encoding="UTF-8"?>\n'
            b'<lldp label="LLDP neighbors"/>\n\x00'
        )
        machine = make_machines_origin().Machine(
            {
                "system_id": make_name_without_spaces("system-id"),
                "hostname": make_name_without_spaces("hostname"),
            }
        )
        machine._handler.details = make_get_details_coroutine(
            machine.system_id, return_value=return_val
        )
        data = machine.get_details()
        self.assertItemsEqual(["lldp", "lshw"], data.keys())
        lldp = ElementTree.fromstring(data["lldp"])
        lshw = ElementTree.fromstring(data["lshw"])
        assert IsInstance(lldp, ElementTree)
        assert IsInstance(lshw, ElementTree)

    def test__restore_default_configuration(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {"system_id": system_id, "hostname": hostname}
        machine = make_machines_origin().Machine(data)
        machine._handler.restore_default_configuration.return_value = data
        machine.restore_default_configuration()
        self.assertEqual(data, machine._data)
        machine._handler.restore_default_configuration.assert_called_once_with(
            system_id=machine.system_id
        )

    def test__restore_networking_configuration(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {"system_id": system_id, "hostname": hostname}
        machine = make_machines_origin().Machine(data)
        mock_restore_networking = machine._handler.restore_networking_configuration
        mock_restore_networking.return_value = data
        machine.restore_networking_configuration()
        self.assertEqual(data, machine._data)
        mock_restore_networking.assert_called_once_with(system_id=machine.system_id)

    def test__restore_storage_configuration(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {"system_id": system_id, "hostname": hostname}
        machine = make_machines_origin().Machine(data)
        mock_restore_storage = machine._handler.restore_storage_configuration
        mock_restore_storage.return_value = data
        machine.restore_storage_configuration()
        self.assertEqual(data, machine._data)
        mock_restore_storage.assert_called_once_with(system_id=machine.system_id)

    def test__save_updates_owner_data(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "owner_data": {"hello": "world", "delete": "me", "keep": "me"},
        }
        machine = make_machines_origin().Machine(data)
        del machine.owner_data["delete"]
        machine.owner_data["hello"] = "whole new world"
        machine.owner_data["new"] = "brand-new"
        machine._handler.set_owner_data.return_value = {}
        machine.save()
        self.assertThat(machine._handler.update.call_count, Equals(0))
        self.assertThat(
            machine.owner_data,
            Equals({"hello": "whole new world", "new": "brand-new", "keep": "me"}),
        )
        machine._handler.set_owner_data.assert_called_once_with(
            system_id=machine.system_id,
            delete="",
            hello="whole new world",
            new="brand-new",
        )

    def test__save_updates_owner_data_with_replace(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {
            "system_id": system_id,
            "hostname": hostname,
            "owner_data": {"hello": "world", "delete": "me", "keep": "me"},
        }
        machine = make_machines_origin().Machine(data)
        machine.owner_data = {
            "hello": "whole new world",
            "keep": "me",
            "new": "brand-new",
        }
        machine._handler.set_owner_data.return_value = {}
        machine.save()
        self.assertThat(machine._handler.update.call_count, Equals(0))
        self.assertThat(
            machine.owner_data,
            Equals({"hello": "whole new world", "new": "brand-new", "keep": "me"}),
        )
        machine._handler.set_owner_data.assert_called_once_with(
            system_id=machine.system_id,
            delete="",
            hello="whole new world",
            new="brand-new",
        )

    def test__lock(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {"system_id": system_id, "hostname": hostname, "locked": False}
        new_data = {"system_id": system_id, "hostname": hostname, "locked": True}
        origin = make_machines_origin()
        machine = origin.Machine(data)
        machine._handler.lock.return_value = new_data
        comment = make_name_without_spaces("comment")
        self.assertThat(machine.lock(comment=comment), Equals(origin.Machine(new_data)))
        machine._handler.lock.assert_called_once_with(
            system_id=machine.system_id, comment=comment
        )
        self.assertThat(machine.locked, Equals(new_data["locked"]))

    def test__unlock(self):
        system_id = make_name_without_spaces("system-id")
        hostname = make_name_without_spaces("hostname")
        data = {"system_id": system_id, "hostname": hostname, "locked": True}
        new_data = {"system_id": system_id, "hostname": hostname, "locked": False}
        origin = make_machines_origin()
        machine = origin.Machine(data)
        machine._handler.unlock.return_value = new_data
        comment = make_name_without_spaces("comment")
        self.assertThat(
            machine.unlock(comment=comment), Equals(origin.Machine(new_data))
        )
        machine._handler.unlock.assert_called_once_with(
            system_id=machine.system_id, comment=comment
        )
        self.assertThat(machine.locked, Equals(new_data["locked"]))


class TestMachine_APIVersion(TestCase):

    scenarios = tuple(
        (name, dict(version=version, description=description))
        for name, version, description in api_descriptions
    )

    async def test__deploy(self):
        builder = ApplicationBuilder(self.description)

        @builder.handle("auth:Machine.deploy")
        async def deploy(request, system_id):
            self.assertThat(
                request.params,
                ContainsDict(
                    {
                        "distro_series": Equals("ubuntu/xenial"),
                        "hwe_kernel": Equals("hwe-x"),
                    }
                ),
            )
            return {"system_id": system_id, "status_name": "Deploying"}

        async with builder.serve() as baseurl:
            origin = await Origin.fromURL(baseurl, credentials=make_Credentials())
            machine = origin.Machine(
                {"system_id": make_name_without_spaces("system-id")}
            )
            machine = await machine.deploy(
                distro_series="ubuntu/xenial", hwe_kernel="hwe-x"
            )
            self.assertThat(
                machine, MatchesStructure.byEquality(status_name="Deploying")
            )


class TestMachines(TestCase):
    def test__create(self):
        origin = make_machines_origin()
        Machines, Machine = origin.Machines, origin.Machine
        Machines._handler.create.return_value = {}
        observed = Machines.create(
            "amd64",
            ["00:11:22:33:44:55", "00:11:22:33:44:AA"],
            "ipmi",
            {"power_address": "localhost", "power_user": "root"},
            subarchitecture="generic",
            min_hwe_kernel="hwe-x",
            hostname="new-machine",
            domain="maas",
            skip_bmc_config=True,
        )
        self.assertThat(observed, IsInstance(Machine))
        Machines._handler.create.assert_called_once_with(
            architecture="amd64",
            mac_addresses=["00:11:22:33:44:55", "00:11:22:33:44:AA"],
            power_type="ipmi",
            power_parameters=(
                '{"power_address": "localhost", ' '"power_user": "root"}'
            ),
            subarchitecture="generic",
            min_hwe_kernel="hwe-x",
            hostname="new-machine",
            domain="maas",
            skip_bmc_config=True,
        )

    def test__allocate(self):
        Machines = make_machines_origin().Machines
        Machines._handler.allocate.return_value = {}
        hostname = make_name_without_spaces("hostname")
        Machines.allocate(
            hostname=hostname,
            architectures=["amd64/generic"],
            cpus=4,
            memory=1024.0,
            tags=["foo", "bar"],
            not_tags=["baz"],
        )
        Machines._handler.allocate.assert_called_once_with(
            name=hostname,  # API parameter is actually name, not hostname
            arch=["amd64/generic"],
            cpu_count="4",
            mem="1024.0",
            tags=["foo", "bar"],
            not_tags=["baz"],
        )

    def test__allocate_with_pod(self):
        Pod = make_pods_origin().Pod
        pod = Pod({"name": make_name_without_spaces("pod")})
        Machines = make_machines_origin().Machines
        Machines._handler.allocate.return_value = {}
        hostname = make_name_without_spaces("hostname")
        Machines.allocate(
            hostname=hostname,
            architectures=["amd64/generic"],
            cpus=4,
            memory=1024.0,
            tags=["foo", "bar"],
            not_tags=["baz"],
            pod=pod.name,
        )
        Machines._handler.allocate.assert_called_once_with(
            name=hostname,  # API parameter is actually name, not hostname
            arch=["amd64/generic"],
            cpu_count="4",
            mem="1024.0",
            tags=["foo", "bar"],
            not_tags=["baz"],
            pod=pod.name,
        )

    def test__allocate_with_not_pod(self):
        Pod = make_pods_origin().Pod
        pod = Pod({"name": make_name_without_spaces("pod")})
        Machines = make_machines_origin().Machines
        Machines._handler.allocate.return_value = {}
        hostname = make_name_without_spaces("hostname")
        Machines.allocate(
            hostname=hostname,
            architectures=["amd64/generic"],
            cpus=4,
            memory=1024.0,
            tags=["foo", "bar"],
            not_tags=["baz"],
            not_pod=pod.name,
        )
        Machines._handler.allocate.assert_called_once_with(
            name=hostname,  # API parameter is actually name, not hostname
            arch=["amd64/generic"],
            cpu_count="4",
            mem="1024.0",
            tags=["foo", "bar"],
            not_tags=["baz"],
            not_pod=pod.name,
        )

    def test__get_power_parameters_for_with_empty_list(self):
        Machines = make_machines_origin().Machines
        self.assertThat(Machines.get_power_parameters_for(system_ids=[]), Equals({}))

    def test__get_power_parameters_for_with_system_ids(self):
        power_parameters = {
            make_name_without_spaces("system_id"): {
                "key": make_name_without_spaces("value")
            }
            for _ in range(3)
        }
        Machines = make_machines_origin().Machines
        Machines._handler.power_parameters.return_value = power_parameters
        self.assertThat(
            Machines.get_power_parameters_for(system_ids=power_parameters.keys()),
            Equals(power_parameters),
        )
        Machines._handler.power_parameters.assert_called_once_with(
            id=power_parameters.keys()
        )
