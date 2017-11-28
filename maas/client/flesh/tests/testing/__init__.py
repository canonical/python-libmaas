"""Test helpers for `maas.client.flesh`."""

__all__ = [
    "capture_parse_error",
]

import argparse

from .... import flesh
from ....testing import TestCase
from ....utils.tests.test_profiles import make_profile


def capture_parse_error(parser, *args):
    """Capture the `ArgumentError` arising from parsing the given arguments.

    `argparse` is hard to test (and to introspect, and extend... but it is
    good at what it does) so we have to use a pseudo-private method here.
    """
    namespace = argparse.Namespace()
    try:
        parser._parse_known_args(list(args), namespace)
    except argparse.ArgumentError as error:
        return error
    else:
        return None


class TestCaseWithProfile(TestCase):
    """Base test case class for all of `flesh` commands.

    This creates an empty default profile.
    """

    def setUp(self):
        self.profile = make_profile("default")
        self.patch(flesh, "PROFILE_NAMES", ["default"])
        self.patch(flesh, "PROFILE_DEFAULT", self.profile)
        super(TestCaseWithProfile, self).setUp()
