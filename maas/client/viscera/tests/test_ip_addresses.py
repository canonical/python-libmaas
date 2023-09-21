"""Tests for `maas.client.viscera.ip_addresses`."""

from testtools.matchers import Equals

from .. import ip_addresses

from ..testing import bind
from ...testing import TestCase


def make_origin():
    """
    Create a new origin with IPAddress and IPAddresses. The former
    refers to the latter via the origin, hence why it must be bound.
    """
    return bind(ip_addresses.IPAddresses, ip_addresses.IPAddress)


class TestIPAddresses(TestCase):
    def test__ip_addresses_read(self):
        """IPAddresses.read() returns a list of IPAddresses."""
        IPAddresses = make_origin().IPAddresses
        ip_addresses = [
            {"ip": "10.0.0.%s" % (i + 1), "alloc_type_name": "User reserved"}
            for i in range(3)
        ]
        IPAddresses._handler.read.return_value = ip_addresses
        ip_addresses = IPAddresses.read()
        self.assertThat(len(ip_addresses), Equals(3))
