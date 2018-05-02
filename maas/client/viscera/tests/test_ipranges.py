"""Test for `maas.client.viscera.ipranges`."""

import random

from testtools.matchers import Equals

from ..ipranges import (
    IPRange,
    IPRanges,
)

from .. testing import bind
from ...enum import IPRangeType
from ...testing import (
    make_string_without_spaces,
    TestCase,
)


def make_origin():
    """
    Create a new origin with IPRanges and IPRange. The former
    refers to the latter via the origin, hence why it must be bound.
    """
    return bind(IPRanges, IPRange)


class TestIPRanges(TestCase):

    def test__ipranges_create(self):
        IPRanges = make_origin().IPRanges
        start_ip = make_string_without_spaces()
        end_ip = make_string_without_spaces()
        type = IPRangeType.DYNAMIC
        comment = make_string_without_spaces()
        IPRanges._handler.create.return_value = {
            "id": 1,
            "start_ip": start_ip,
            "end_ip": end_ip,
            "type": type.value,
            "comment": comment,
        }
        IPRanges.create(
            start_ip=start_ip,
            end_ip=end_ip,
            type=type,
            comment=comment,
        )
        IPRanges._handler.create.assert_called_once_with(
            start_ip=start_ip,
            end_ip=end_ip,
            type=type.value,
            comment=comment,
        )

    def test__ipranges_create_requires_IPRangeType(self):
        IPRanges = make_origin().IPRanges
        start_ip = make_string_without_spaces()
        end_ip = make_string_without_spaces()
        comment = make_string_without_spaces()
        error = self.assertRaises(
            TypeError, IPRanges.create,
            start_ip=start_ip, end_ip=end_ip,
            type=make_string_without_spaces(), comment=comment)
        self.assertEquals("type must be an IPRangeType, not str", str(error))

    def test__ipranges_read(self):
        """IPRanges.read() returns a list of IPRanges."""
        IPRanges = make_origin().IPRanges
        ipranges = [
            {
                "id": random.randint(0, 100),
                "start_ip": make_string_without_spaces(),
                "end_ip": make_string_without_spaces(),
                "type": make_string_without_spaces(),
                "comment": make_string_without_spaces(),
            }
            for _ in range(3)
        ]
        IPRanges._handler.read.return_value = ipranges
        ipranges = IPRanges.read()
        self.assertThat(len(ipranges), Equals(3))


class TestIPRange(TestCase):

    def test__iprange_read(self):
        IPRange = make_origin().IPRange
        iprange = {
            "id": random.randint(0, 100),
            "start_ip": make_string_without_spaces(),
            "end_ip": make_string_without_spaces(),
            "type": make_string_without_spaces(),
            "comment": make_string_without_spaces(),
        }
        IPRange._handler.read.return_value = iprange
        self.assertThat(IPRange.read(id=iprange["id"]),
                        Equals(IPRange(iprange)))
        IPRange._handler.read.assert_called_once_with(id=iprange["id"])

    def test__iprange_delete(self):
        IPRange = make_origin().IPRange
        iprange_id = random.randint(1, 100)
        iprange = IPRange({
            "id": iprange_id,
            "start_ip": make_string_without_spaces(),
            "end_ip": make_string_without_spaces(),
            "type": make_string_without_spaces(),
            "comment": make_string_without_spaces(),
        })
        iprange.delete()
        IPRange._handler.delete.assert_called_once_with(id=iprange_id)
