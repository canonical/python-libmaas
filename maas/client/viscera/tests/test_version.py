"""Test for `maas.client.viscera.version`."""

from random import randrange

from testtools.matchers import Equals

from .. import version
from ...testing import (
    make_name_without_spaces,
    TestCase,
)


class TestVersion(TestCase):

    def test__fields(self):
        v_major = randrange(2, 99)
        v_point1 = randrange(0, 99)
        v_point2 = randrange(0, 99)
        v_tuple = v_major, v_point1, v_point2
        v_string = "%d.%d.%d" % v_tuple
        v_sub = make_name_without_spaces("subv")
        v_caps = [
            make_name_without_spaces("cap") for _ in range(randrange(10))
        ]

        vsn = version.Version({
            "version": v_string,
            "subversion": v_sub,
            "capabilities": v_caps,
        })

        self.assertThat(vsn.version, Equals(v_string))
        self.assertThat(vsn.version_info, Equals(v_tuple))
        self.assertThat(vsn.subversion, Equals(v_sub))
        self.assertThat(vsn.capabilities, Equals(frozenset(v_caps)))

    def test__string_representation(self):
        vsn = version.Version({
            "version": "2.1.0",
            "subversion": "alpha9999+bzr8888",
            "capabilities": ["kung-fu", "badgering"],
        })
        self.assertThat(repr(vsn), Equals(
            "<Version 2.1.0 alpha9999+bzr8888 [badgering kung-fu]>"))
