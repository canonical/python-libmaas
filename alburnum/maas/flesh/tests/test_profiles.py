"""Tests for `alburnum.maas.flesh.profiles`."""

__all__ = []

from io import StringIO
import sys
from textwrap import dedent

from alburnum.maas.testing import TestCase

from .. import profiles
from ...utils import auth
from ...utils.tests.test_auth import make_options
from ...utils.tests.test_profiles import make_profile


class TestLoginBase(TestCase):
    """Tests for `cmd_login_base`."""

    def test_print_whats_next(self):
        profile = make_profile()
        stdout = self.patch(sys, "stdout", StringIO())
        profiles.cmd_login_base.print_whats_next(profile)
        expected = dedent("""\
            Congratulations! You are logged in to the MAAS
            server at {profile.url} with the profile name
            {profile.name}.

            For help with the available commands, try:

              maas --help

            """).format(profile=profile)
        observed = stdout.getvalue()
        self.assertDocTestMatches(expected, observed)

    def test_save_profile_ensures_valid_apikey(self):
        options = make_options()
        check_key = self.patch(profiles, "check_valid_apikey")
        check_key.return_value = False
        error = self.assertRaises(
            SystemExit, profiles.cmd_login_base.save_profile, options,
            auth.Credentials.parse(options.credentials))
        self.assertEqual(
            "The MAAS server rejected your API key.",
            str(error))
        check_key.assert_called_once_with(
            options.url, auth.Credentials.parse(options.credentials),
            options.insecure)
