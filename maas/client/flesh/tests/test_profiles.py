"""Tests for `maas.client.flesh.profiles`."""

from argparse import ArgumentParser
from io import StringIO
import sys
from textwrap import dedent
from unittest.mock import call

from .. import profiles
from ...bones.helpers import MacaroonLoginNotSupported
from ...testing import (
    AsyncCallableMock,
    TestCase,
)
from ...utils.tests.test_profiles import make_profile


class TestLogin(TestCase):
    """Tests for `cmd_login`."""

    def test_login_no_macaroons_prompts_user_pass(self):
        profile = make_profile()

        stdout = self.patch(sys, 'stdout', StringIO())
        mock_read_input = self.patch(profiles, 'read_input')
        mock_read_input.side_effect = ['username', 'password']
        mock_login = AsyncCallableMock(
            side_effect=[MacaroonLoginNotSupported, profile])
        self.patch(profiles.helpers, 'login', mock_login)

        parser = ArgumentParser()
        cmd = profiles.cmd_login(parser)
        options = parser.parse_args(['http://maas.example'])
        cmd(options)
        mock_login.assert_has_calls(
            [
                call('http://maas.example/api/2.0/', anonymous=False,
                     insecure=False, username=None, password=None),
                call('http://maas.example/api/2.0/', insecure=False,
                     username='username', password='password')])
        self.assertIn('Congratulations!', stdout.getvalue())

    def test_print_whats_next(self):
        profile = make_profile()
        stdout = self.patch(sys, "stdout", StringIO())
        profiles.cmd_login.print_whats_next(profile)
        expected = dedent("""\
            Congratulations! You are logged in to the MAAS
            server at {profile.url} with the profile name
            {profile.name}.

            For help with the available commands, try:

              maas help

            """).format(profile=profile)
        observed = stdout.getvalue()
        self.assertDocTestMatches(expected, observed)
