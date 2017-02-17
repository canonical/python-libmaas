"""Tests for `maas.client`."""

__all__ = []

from inspect import (
    getdoc,
    signature,
)

from testtools.matchers import (
    Equals,
    Is,
    Not,
)

from ... import client
from ..testing import TestCase
from ..viscera import Origin


class TestStubs(TestCase):
    """Tests that stubs match their concrete counterparts."""

    def setUp(self):
        super(TestStubs, self).setUp()
        client._load()  # Ensure the stubs have been replaced.

    def test__connect_stub_matches_Origin_connect(self):
        stub, real = client._connect, client.connect
        self.assertThat(real, Equals(Origin.connect))
        self.assertSignaturesAndDocsMatch(stub, real)

    def test__login_stub_matches_Origin_login(self):
        stub, real = client._login, client.login
        self.assertThat(real, Equals(Origin.login))
        self.assertSignaturesAndDocsMatch(stub, real)

    def assertSignaturesAndDocsMatch(self, stub, real):
        self.assertThat(stub, Not(Is(real)))
        sig_stub = signature(client._connect)
        sig_real = signature(client.connect)
        self.assertThat(sig_stub, Equals(sig_real))
        doc_real = getdoc(real)
        doc_stub = getdoc(stub)
        self.assertThat(doc_stub, Equals(doc_real))
