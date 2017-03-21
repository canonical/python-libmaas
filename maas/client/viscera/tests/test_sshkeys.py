"""Test for `maas.client.viscera.sshkeys`."""

from .. import sshkeys

from ...testing import (
    make_string_without_spaces,
    TestCase,
)

from ..testing import bind


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
