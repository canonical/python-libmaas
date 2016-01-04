# Copyright 2012-2015 Canonical Ltd. Copyright 2015 Alburnum Ltd.
# This software is licensed under the GNU Affero General Public
# License version 3 (see LICENSE).

"""Tests for `alburnum.maas.viscera`."""

__all__ = []

from io import StringIO
import sys
from textwrap import dedent

from alburnum.maas import (
    auth,
    viscera,
)
from alburnum.maas.testing import (
    make_name,
    TestCase,
)
from alburnum.maas.tests.test_auth import make_options


class TestLogin(TestCase):

    def test_cmd_login_ensures_valid_apikey(self):
        parser = viscera.ArgumentParser()
        options = make_options()
        check_key = self.patch(viscera, "check_valid_apikey")
        check_key.return_value = False
        login = viscera.cmd_login(parser)
        error = self.assertRaises(SystemExit, login, options)
        self.assertEqual(
            "The MAAS server rejected your API key.",
            str(error))
        check_key.assert_called_once_with(
            options.url, auth.Credentials.parse(options.credentials),
            options.insecure)

    def test_print_whats_next(self):
        profile = {"name": make_name("profile"), "url": make_name("url")}
        stdout = self.patch(sys, "stdout", StringIO())
        viscera.cmd_login.print_whats_next(profile)
        expected = dedent("""\

            You are now logged in to the MAAS server at %(url)s with the
            profile name '%(name)s'.

            For help with the available commands, try:

              maas --help

            """) % profile
        observed = stdout.getvalue()
        self.assertDocTestMatches(expected, observed)
