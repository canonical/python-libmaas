"""Test for `maas.client.viscera.sshkeys`."""

from maas.client.viscera import Origin

from .. import sshkeys

from ...testing import TestCase
from ..testing import bind

def make_origin():
    return bind(sshkeys.SSHKeys, sshkeys.SSHKey)

class TestSSHKeys(TestCase):

    def test__sshkeys_read(self):
        """ SSHKeys.read() returns all SSH keys. """
        SSHKeys = make_origin().SSHKeys
        # create a list of dicts for read() to return
        self.assertThat(SSHKeys.read(), Equals())

    def test__sshkeys_create(self):
        """ SSHKeys.create() returns a new SSHKey. """
        SSHKeys = make_origin().SSHKeys
        SSHKeys._handler.create.return_value = {
            "id": 1,
            "key": "jeqqirevireveriv02329329mcie",
            "keysource": "",
        }
        SSHKeys._handler.create.assert_called_once_with(
            key="jeqqirevireveriv02329329mcie"
        )

class TestSSHKey(TestCase):

    def test__sshkey_read(self):
        """ SSHKey.read(id) returns a single SSHKey. """
        SSHKey = make_origin().SSHKey
        sshkey = SSHKey()

    def test__sshkey_update(self):
        """ SSHKey.update(id, ...) returns an updated SSHKey. """
