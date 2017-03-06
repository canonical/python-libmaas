"""Tests for `maas.client.utils.auth`."""

import sys
from unittest.mock import (
    ANY,
    sentinel,
)

from .. import auth
from ...testing import TestCase
from ..testing import make_Credentials


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
        credentials = make_Credentials()
        stdin = self.patch(sys, "stdin")
        stdin.readline.return_value = str(credentials) + "\n"
        self.assertEqual(credentials, auth.obtain_credentials("-"))
        stdin.readline.assert_called_once_with()

    def test_obtain_credentials_via_getpass(self):
        # When None is passed to obtain_credentials, it attempts to obtain
        # credentials via getpass, then converts it into a 3-tuple of creds.
        credentials = make_Credentials()
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
