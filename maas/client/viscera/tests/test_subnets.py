"""Test for `maas.client.viscera.subnets`."""

import random

from testtools.matchers import Equals

from ..subnets import (
    Subnet,
    Subnets,
)

from .. testing import bind
from ...testing import (
    make_string_without_spaces,
    TestCase,
)


def make_origin():
    """
    Create a new origin with Subnets and Subnet. The former
    refers to the latter via the origin, hence why it must be bound.
    """
    return bind(Subnets, Subnet)


class TestSubnets(TestCase):

    def test__subnets_create(self):
        Subnets = make_origin().Subnets
        name = make_string_without_spaces()
        description = make_string_without_spaces()
        Subnets._handler.create.return_value = {
            "id": 1,
            "name": name,
            "description": description,
        }
        Subnets.create(
            name=name,
            description=description,
        )
        Subnets._handler.create.assert_called_once_with(
            name=name,
            description=description,
        )

    def test__subnets_read(self):
        """Subnets.read() returns a list of Subnets."""
        Subnets = make_origin().Subnets
        subnets = [
            {
                "id": random.randint(0, 100),
                "name": make_string_without_spaces(),
            }
            for _ in range(3)
        ]
        Subnets._handler.read.return_value = subnets
        subnets = Subnets.read()
        self.assertThat(len(subnets), Equals(3))


class TestSubnet(TestCase):

    def test__subnet_get_default(self):
        Subnet = make_origin().Subnet
        Subnet._handler.read.return_value = {
            "id": 0,
            "name": make_string_without_spaces(),
        }
        Subnet.get_default()
        Subnet._handler.read.assert_called_once_with(
            id=0
        )

    def test__subnet_read(self):
        Subnet = make_origin().Subnet
        subnet = {
            "id": random.randint(0, 100),
            "name": make_string_without_spaces(),
        }
        Subnet._handler.read.return_value = subnet
        self.assertThat(Subnet.read(id=subnet["id"]), Equals(Subnet(subnet)))
        Subnet._handler.read.assert_called_once_with(id=subnet["id"])

    def test__subnet_delete(self):
        Subnet = make_origin().Subnet
        subnet_id = random.randint(1, 100)
        subnet = Subnet({
            "id": subnet_id,
            "name": make_string_without_spaces(),
        })
        subnet.delete()
        Subnet._handler.delete.assert_called_once_with(id=subnet_id)
