"""Tests for `alburnum.maas.flesh`."""

__all__ = []

from io import StringIO
import sys
from textwrap import dedent

from alburnum.maas import flesh
from alburnum.maas.testing import (
    make_name,
    TestCase,
)
from alburnum.maas.utils import auth
from alburnum.maas.utils.tests.test_auth import make_options


class TestLoginBase(TestCase):
    """Tests for `cmd_login_base`."""

    def test_print_whats_next(self):
        profile = {"name": make_name("profile"), "url": make_name("url")}
        stdout = self.patch(sys, "stdout", StringIO())
        flesh.cmd_login_base.print_whats_next(profile)
        expected = dedent("""\
            Congratulations! You are logged in to the MAAS
            server at %(url)s with the profile name
            %(name)s.

            For help with the available commands, try:

              maas --help

            """) % profile
        observed = stdout.getvalue()
        self.assertDocTestMatches(expected, observed)

    def test_save_profile_ensures_valid_apikey(self):
        options = make_options()
        check_key = self.patch(flesh, "check_valid_apikey")
        check_key.return_value = False
        error = self.assertRaises(
            SystemExit, flesh.cmd_login_base.save_profile, options,
            auth.Credentials.parse(options.credentials))
        self.assertEqual(
            "The MAAS server rejected your API key.",
            str(error))
        check_key.assert_called_once_with(
            options.url, auth.Credentials.parse(options.credentials),
            options.insecure)
