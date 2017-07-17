"""Test for `maas.client.viscera.subnets`."""

import random

from testtools.matchers import (
    Equals,
    IsInstance,
    MatchesAll,
    MatchesStructure,
)

from ..subnets import (
    Subnet,
    Subnets,
)
from ..vlans import (
    Vlan,
    Vlans,
)

from ..testing import bind
from ...enum import RDNSMode
from ...testing import (
    make_string_without_spaces,
    TestCase,
)


def make_origin():
    """
    Create a new origin with Subnets, Subnet, Vlans, Vlan.
    """
    return bind(Subnets, Subnet, Vlans, Vlan)


class TestSubnets(TestCase):

    def test__subnets_create(self):
        Subnets = make_origin().Subnets
        cidr = make_string_without_spaces()
        vlan = random.randint(5000, 8000)
        name = make_string_without_spaces()
        description = make_string_without_spaces()
        Subnets._handler.create.return_value = {
            "id": 1,
            "cidr": cidr,
            "vlan": vlan,
            "name": name,
            "description": description,
        }
        Subnets.create(cidr, vlan, name=name, description=description)
        Subnets._handler.create.assert_called_once_with(
            cidr=cidr, vlan=vlan,
            name=name, description=description)

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

    def test__subnet_read(self):
        Subnet = make_origin().Subnet
        vlan_id = random.randint(5000, 8000)
        subnet = {
            "id": random.randint(0, 100),
            "name": make_string_without_spaces(),
            "vlan": {
                "id": vlan_id,
            },
            "rdns_mode": 2,
        }
        Subnet._handler.read.return_value = subnet
        self.assertThat(Subnet.read(id=subnet["id"]), Equals(Subnet(subnet)))
        self.assertThat(
            Subnet(subnet).vlan, MatchesAll(
                IsInstance(Vlan), MatchesStructure.byEquality(id=vlan_id)))
        self.assertThat(Subnet(subnet).rdns_mode, Equals(RDNSMode.RFC2317))
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
