"""Tests for `maas.client`."""

from inspect import signature
from unittest.mock import sentinel

from testtools.matchers import (
    Equals,
    Is,
    IsInstance,
    Not,
)

from .. import facade
from ... import client
from ..testing import (
    AsyncCallableMock,
    TestCase,
)
from ..viscera import Origin


class TestFunctions(TestCase):
    """Tests for module functions."""

    def test__connect_matches_Origin_connect(self):
        stub, real = client.connect, Origin.connect
        self.assertSignaturesMatch(stub, real)

    def test__connect_calls_through_to_Origin(self):
        connect = self.patch(Origin, "connect", AsyncCallableMock())
        connect.return_value = sentinel.profile, sentinel.origin
        client_object = client.connect(
            sentinel.url, apikey=sentinel.apikey, insecure=sentinel.insecure)
        connect.assert_called_once_with(
            sentinel.url, apikey=sentinel.apikey, insecure=sentinel.insecure)
        self.assertThat(client_object, IsInstance(facade.Client))
        self.assertThat(client_object._origin, Is(sentinel.origin))

    def test__login_matches_Origin_login(self):
        stub, real = client.login, Origin.login
        self.assertSignaturesMatch(stub, real)

    def test__login_calls_through_to_Origin(self):
        login = self.patch(Origin, "login", AsyncCallableMock())
        login.return_value = sentinel.profile, sentinel.origin
        client_object = client.login(
            sentinel.url, username=sentinel.username,
            password=sentinel.password, insecure=sentinel.insecure)
        login.assert_called_once_with(
            sentinel.url, username=sentinel.username,
            password=sentinel.password, insecure=sentinel.insecure)
        self.assertThat(client_object, IsInstance(facade.Client))
        self.assertThat(client_object._origin, Is(sentinel.origin))

    def assertSignaturesMatch(self, stub, real):
        self.assertThat(stub, Not(Is(real)))
        sig_stub = signature(client.connect)
        sig_real = signature(Origin.connect)
        self.assertThat(sig_stub, Equals(sig_real))
