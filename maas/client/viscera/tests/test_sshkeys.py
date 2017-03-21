"""Test for `maas.client.viscera.sshkeys`."""

import random

from .. import sshkeys

from ...testing import (
    make_string_without_spaces,
    TestCase,
)

from ..testing import bind

from testtools.matchers import Equals


def make_origin():
    return bind(sshkeys.SSHKeys, sshkeys.SSHKey)


class TestSSHKeys(TestCase):

    def test__sshkeys_create(self):
        """ SSHKeys.create() returns a new SSHKey. """
        SSHKeys = make_origin().SSHKeys
        key = make_string_without_spaces()
        SSHKeys._handler.create.return_value = {
            "id": 1,
            "key": key,
            "keysource": "",
        }
        SSHKeys.create(key=key)
        SSHKeys._handler.create.assert_called_once_with(
            key=key
        )

    def test__sshkeys_read(self):
        """ SSHKeys.read() returns a list of SSH keys. """
        SSHKeys = make_origin().SSHKeys
        keys = [
            {
                "id": random.randint(0, 100),
                "key": make_string_without_spaces(),
                "keysource": "",
            }
            for _ in range(3)
        ]
        SSHKeys._handler.read.return_value = keys
        ssh_keys = SSHKeys.read()
        self.assertThat(len(ssh_keys), Equals(3))


class TestSSHKey(TestCase):

    def test__sshkey_read(self):
        """ SSHKeys.read() returns a single SSH key. """
        SSHKey = make_origin().SSHKey
        key_id = random.randint(0, 100)
        key_dict = {
            "id": key_id,
            "key": make_string_without_spaces(),
            "keysource": "",
        }
        SSHKey._handler.read.return_value = key_dict
        self.assertThat(SSHKey.read(id=key_id), Equals(SSHKey(key_dict)))
