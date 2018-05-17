"""Test for `maas.client.viscera.pods`."""

import random

from testtools.matchers import (
    Equals,
    IsInstance,
)

from ...errors import OperationNotAllowed
from ..pods import (
    Pod,
    Pods,
)
from .. testing import bind
from ...testing import (
    make_name_without_spaces,
    make_string_without_spaces,
    TestCase,
)


def make_origin():
    """
    Create a new origin with Pods and Pod. The former
    refers to the latter via the origin, hence why it must be bound.
    """
    return bind(Pods, Pod)


def make_pod():
    """Returns a pod dictionary."""
    return {
        "id": random.randint(1, 100),
        "type": make_name_without_spaces("type"),
        "name": make_name_without_spaces("name"),
        "architectures": [
            make_string_without_spaces()
            for _ in range(3)
        ],
        "capabilities": [
            make_string_without_spaces()
            for _ in range(3)
        ],
        "zone": {
            "id": random.randint(1, 100),
            "name": make_name_without_spaces("name"),
            "description": make_name_without_spaces("description"),
        },
        "tags": [
            make_string_without_spaces()
            for _ in range(3)
        ],
        "cpu_over_commit_ratio": random.uniform(0, 10),
        "memory_over_commit_ratio": random.uniform(0, 10),
        "available": {
            "cores": random.randint(1, 100),
            "memory": random.randint(4096, 8192),
            "local_storage": random.randint(1024, 1024 * 1024),
        },
        "used": {
            "cores": random.randint(1, 100),
            "memory": random.randint(4096, 8192),
            "local_storage": random.randint(1024, 1024 * 1024),
        },
        "total": {
            "cores": random.randint(1, 100),
            "memory": random.randint(4096, 8192),
            "local_storage": random.randint(1024, 1024 * 1024),
        },
    }


class TestPods(TestCase):

    def test__pods_create(self):
        type = make_string_without_spaces()
        power_address = make_string_without_spaces()
        power_user = make_string_without_spaces()
        power_pass = make_string_without_spaces()
        name = make_string_without_spaces()
        zone = make_string_without_spaces()
        tags = make_string_without_spaces()
        origin = make_origin()
        Pods, Pod = origin.Pods, origin.Pod
        Pods._handler.create.return_value = {}
        observed = Pods.create(
            type=type, power_address=power_address, power_user=power_user,
            power_pass=power_pass, name=name, zone=zone, tags=tags)
        self.assertThat(observed, IsInstance(Pod))
        Pods._handler.create.assert_called_once_with(
            type=type,
            power_address=power_address,
            power_user=power_user,
            power_pass=power_pass,
            name=name,
            zone=zone,
            tags=tags)

    def test__pods_create_raises_error_for_rsd_and_no_power_user(self):
        origin = make_origin()
        origin.Pods._handler.create.return_value = {}
        self.assertRaises(
            OperationNotAllowed, origin.Pods.create, type='rsd',
            power_address=make_string_without_spaces())

    def test__pods_create_raises_error_for_rsd_and_no_power_pass(self):
        origin = make_origin()
        origin.Pods._handler.create.return_value = {}
        self.assertRaises(
            OperationNotAllowed, origin.Pods.create, type='rsd',
            power_address=make_string_without_spaces(),
            power_user=make_string_without_spaces())

    def test__pods_create_raises_type_error_for_zone(self):
        origin = make_origin()
        origin.Pods._handler.create.return_value = {}
        self.assertRaises(
            TypeError, origin.Pods.create, type=make_string_without_spaces(),
            power_address=make_string_without_spaces(),
            power_user=make_string_without_spaces(),
            power_pass=make_string_without_spaces(),
            zone=0.1)

    def test__pods_read(self):
        Pods = make_origin().Pods
        pods = [
            make_pod()
            for _ in range(3)
        ]
        Pods._handler.read.return_value = pods
        pods = Pods.read()
        self.assertThat(len(pods), Equals(3))


class TestPod(TestCase):

    def test__pod_read(self):
        Pod = make_origin().Pod
        pod = make_pod()
        Pod._handler.read.return_value = pod
        self.assertThat(Pod.read(id=pod["id"]), Equals(Pod(pod)))
        Pod._handler.read.assert_called_once_with(id=pod["id"])

    def test__pod_refresh(self):
        Pod = make_origin().Pod
        pod_data = make_pod()
        pod = Pod(pod_data)
        pod.refresh()
        Pod._handler.refresh.assert_called_once_with(id=pod_data["id"])

    def test__pod_parameters(self):
        Pod = make_origin().Pod
        pod_data = make_pod()
        pod = Pod(pod_data)
        pod.parameters()
        Pod._handler.parameters.assert_called_once_with(id=pod_data["id"])

    def test__pod_compose(self):
        Pod = make_origin().Pod
        pod_data = make_pod()
        pod = Pod(pod_data)
        cores = random.randint(1, 100)
        memory = random.randint(4096, 8192)
        cpu_speed = random.randint(16, 256)
        architecture = make_name_without_spaces("architecture")
        storage = make_string_without_spaces()
        hostname = make_name_without_spaces("hostname")
        domain = random.randint(1, 10)
        zone = random.randint(1, 10)
        pod.compose(
            cores=cores, memory=memory, cpu_speed=cpu_speed,
            architecture=architecture, storage=storage,
            hostname=hostname, domain=domain, zone=zone)
        Pod._handler.compose.assert_called_once_with(
            id=pod_data["id"], cores=str(cores), memory=str(memory),
            cpu_speed=str(cpu_speed), architecture=architecture,
            storage=storage, hostname=hostname, domain=str(domain),
            zone=str(zone))

    def test__pod_compose_raises_type_error_for_zone(self):
        Pod = make_origin().Pod
        pod_data = make_pod()
        pod = Pod(pod_data)
        cores = random.randint(1, 100)
        memory = random.randint(4096, 8192)
        cpu_speed = random.randint(16, 256)
        architecture = make_name_without_spaces("architecture")
        storage = make_string_without_spaces()
        hostname = make_name_without_spaces("hostname")
        domain = random.randint(1, 10)
        zone = 0.1
        self.assertRaises(
            TypeError, pod.compose, cores=cores, memory=memory,
            cpu_speed=cpu_speed, architecture=architecture, storage=storage,
            hostname=hostname, domain=domain, zone=zone)

    def test__pod_update(self):
        Pod = make_origin().Pod
        pod_data = make_pod()
        pod_data["type"] = "virsh"
        pod = Pod(pod_data)
        name = make_name_without_spaces("name")
        default_storage_pool = make_name_without_spaces("default_storage_pool")
        cpu_over_commit_ratio = random.uniform(0, 10)
        memory_over_commit_ratio = random.uniform(0, 10)
        pod.update(
            name=name, default_storage_pool=default_storage_pool,
            cpu_over_commit_ratio=cpu_over_commit_ratio,
            memory_over_commit_ratio=memory_over_commit_ratio)
        Pod._handler.update.assert_called_once_with(
            id=pod_data["id"], name=name,
            default_storage_pool=default_storage_pool,
            cpu_over_commit_ratio=str(cpu_over_commit_ratio),
            memory_over_commit_ratio=str(memory_over_commit_ratio))

    def test__pod_update_raises_error_for_default_storage_pool_not_virsh(self):
        Pod = make_origin().Pod
        pod_data = make_pod()
        pod = Pod(pod_data)
        name = make_name_without_spaces("name")
        default_storage_pool = make_name_without_spaces("default_storage_pool")
        cpu_over_commit_ratio = random.uniform(0, 10)
        memory_over_commit_ratio = random.uniform(0, 10)
        self.assertRaises(
            OperationNotAllowed, pod.update, name=name,
            default_storage_pool=default_storage_pool,
            cpu_over_commit_ratio=cpu_over_commit_ratio,
            memory_over_commit_ratio=memory_over_commit_ratio)

    def test__pod_delete(self):
        Pod = make_origin().Pod
        pod_data = make_pod()
        pod = Pod(pod_data)
        pod.delete()
        Pod._handler.delete.assert_called_once_with(id=pod_data["id"])

    def test__save_add_tag(self):
        Pod = make_origin().Pod
        pod_data = make_pod()
        pod = Pod(pod_data)
        tag = make_string_without_spaces()
        pod.tags.append(tag)
        Pod._handler.add_tag.return_value = None
        pod.save()
        Pod._handler.add_tag.assert_called_once_with(id=pod.id, tag=tag)

    def test__save_remove_tag(self):
        Pod = make_origin().Pod
        pod_data = make_pod()
        tag = make_string_without_spaces()
        pod_data['tags'] = [tag]
        pod = Pod(pod_data)
        pod.tags.remove(tag)
        Pod._handler.remove_tag.return_value = None
        pod.save()
        Pod._handler.remove_tag.assert_called_once_with(id=pod.id, tag=tag)
