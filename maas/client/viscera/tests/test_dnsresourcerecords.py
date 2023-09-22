"""Tests for `maas.client.viscera.dnsresourcerecords`."""

import random

from testtools.matchers import Equals

from .. import dnsresourcerecords

from ..testing import bind
from ...testing import make_string_without_spaces, TestCase


def make_origin():
    """
    Create a new origin with DNSResourceRecord and DNSResourceRecords. The former
    refers to the latter via the origin, hence why it must be bound.
    """
    return bind(
        dnsresourcerecords.DNSResourceRecords, dnsresourcerecords.DNSResourceRecord
    )


class TestDNSResourceRecords(TestCase):
    def test__dnsresourcerecords_read(self):
        """DNSResourceRecords.read() returns a list of DNSResourceRecords."""
        DNSResourceRecords = make_origin().DNSResourceRecords
        dnsresourcerecords = [
            {"id": random.randint(0, 100), "fqdn": make_string_without_spaces()}
            for _ in range(3)
        ]
        DNSResourceRecords._handler.read.return_value = dnsresourcerecords
        dnsresourcerecords = DNSResourceRecords.read()
        self.assertThat(len(dnsresourcerecords), Equals(3))


class TestDNSResourceRecord(TestCase):
    def test__dnsresourcerecord_read(self):
        DNSResourceRecord = make_origin().DNSResourceRecord
        dnsresourcerecord = {
            "id": random.randint(0, 100),
            "fqdn": make_string_without_spaces(),
        }
        DNSResourceRecord._handler.read.return_value = dnsresourcerecord
        self.assertThat(
            DNSResourceRecord.read(id=dnsresourcerecord["id"]),
            Equals(DNSResourceRecord(dnsresourcerecord)),
        )
        DNSResourceRecord._handler.read.assert_called_once_with(
            id=dnsresourcerecord["id"]
        )
