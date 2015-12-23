# Copyright 2012-2015 Canonical Ltd. Copyright 2015 Alburnum Ltd.
# This software is licensed under the GNU Affero General Public
# License version 3 (see the file LICENSE).

"""Tests for `alburnum.maas.auth`."""

__all__ = []

from argparse import Namespace
import sys
from unittest.mock import (
    ANY,
    sentinel,
)

from alburnum.maas import auth
from alburnum.maas.creds import Credentials
from alburnum.maas.testing import (
    make_name,
    TestCase,
)


def make_credentials():
    return Credentials(
        make_name('consumer_key'),
        make_name('token_key'),
        make_name('secret_key'),
        )


def make_options():
    credentials = make_credentials()
    url = 'http://example.com/api/1.0/'
    options = Namespace(
        credentials=str(credentials), execute=None, insecure=False,
        profile_name='test', url=url)
    return options


class TestAuth(TestCase):

    def test_try_getpass(self):
        getpass = self.patch(auth, "getpass")
        getpass.return_value = sentinel.credentials
        self.assertIs(sentinel.credentials, auth.try_getpass(sentinel.prompt))
        getpass.assert_called_once_with(sentinel.prompt)

    def test_try_getpass_eof(self):
        getpass = self.patch(auth, "getpass")
        getpass.side_effect = EOFError
        self.assertIsNone(auth.try_getpass(sentinel.prompt))
        getpass.assert_called_once_with(sentinel.prompt)

    def test_obtain_credentials_from_stdin(self):
        # When "-" is passed to obtain_credentials, it reads credentials from
        # stdin, trims whitespace, and converts it into a 3-tuple of creds.
        credentials = make_credentials()
        stdin = self.patch(sys, "stdin")
        stdin.readline.return_value = str(credentials) + "\n"
        self.assertEqual(credentials, auth.obtain_credentials("-"))
        stdin.readline.assert_called_once_with()

    def test_obtain_credentials_via_getpass(self):
        # When None is passed to obtain_credentials, it attempts to obtain
        # credentials via getpass, then converts it into a 3-tuple of creds.
        credentials = make_credentials()
        getpass = self.patch(auth, "getpass")
        getpass.return_value = str(credentials)
        self.assertEqual(credentials, auth.obtain_credentials(None))
        getpass.assert_called_once_with(ANY)

    def test_obtain_credentials_empty(self):
        # If the entered credentials are empty or only whitespace,
        # obtain_credentials returns None.
        getpass = self.patch(auth, "getpass")
        getpass.return_value = None
        self.assertEqual(None, auth.obtain_credentials(None))
        getpass.assert_called_once_with(ANY)
