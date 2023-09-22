"""Tests for `maas.client.viscera.dnsresources`."""

import random

from testtools.matchers import Equals

from .. import dnsresources

from ..testing import bind
from ...testing import make_string_without_spaces, TestCase


def make_origin():
    """
    Create a new origin with DNSResource and DNSResources. The former
    refers to the latter via the origin, hence why it must be bound.
    """
    return bind(dnsresources.DNSResources, dnsresources.DNSResource)


class TestDNSResources(TestCase):
    def test__dnsresources_read(self):
        """DNSResources.read() returns a list of DNSResources."""
        DNSResources = make_origin().DNSResources
        dnsresources = [
            {"id": random.randint(0, 100), "fqdn": make_string_without_spaces()}
            for _ in range(3)
        ]
        DNSResources._handler.read.return_value = dnsresources
        dnsresources = DNSResources.read()
        self.assertThat(len(dnsresources), Equals(3))


class TestDNSResource(TestCase):
    def test__dnsresource_read(self):
        DNSResource = make_origin().DNSResource
        dnsresource = {
            "id": random.randint(0, 100),
            "fqdn": make_string_without_spaces(),
        }
        DNSResource._handler.read.return_value = dnsresource
        self.assertThat(
            DNSResource.read(id=dnsresource["id"]), Equals(DNSResource(dnsresource))
        )
        DNSResource._handler.read.assert_called_once_with(id=dnsresource["id"])
