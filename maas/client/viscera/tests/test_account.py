"""Test for `maas.client.viscera.account`."""

from testtools.matchers import (
    Equals,
    IsInstance,
    MatchesAll,
)

from .. import account
from ...testing import (
    make_name_without_spaces,
    TestCase,
)
from ...utils import creds
from ...utils.testing import make_Credentials
from ..testing import bind


def make_origin():
    # Create a new origin with Account.
    return bind(account.Account)


class TestAccount(TestCase):

    def test__create_credentials_returns_Credentials(self):
        consumer_key = make_name_without_spaces('consumer_key'),
        token_key = make_name_without_spaces('token_key'),
        token_secret = make_name_without_spaces('token_secret'),

        origin = make_origin()
        create_authorisation_token = (
            origin.Account._handler.create_authorisation_token)
        create_authorisation_token.return_value = {
            "consumer_key": consumer_key, "token_key": token_key,
            "token_secret": token_secret,
        }

        credentials = origin.Account.create_credentials()
        self.assertThat(credentials, MatchesAll(
            IsInstance(creds.Credentials),
            Equals((consumer_key, token_key, token_secret)),
        ))

    def test__create_credentials_ignores_other_keys_in_response(self):
        consumer_key = make_name_without_spaces('consumer_key'),
        token_key = make_name_without_spaces('token_key'),
        token_secret = make_name_without_spaces('token_secret'),

        origin = make_origin()
        create_authorisation_token = (
            origin.Account._handler.create_authorisation_token)
        create_authorisation_token.return_value = {
            "name": "cookie-monster", "fur-colour": "blue",
            "consumer_key": consumer_key, "token_key": token_key,
            "token_secret": token_secret,
        }

        credentials = origin.Account.create_credentials()
        self.assertThat(credentials, MatchesAll(
            IsInstance(creds.Credentials),
            Equals((consumer_key, token_key, token_secret)),
        ))

    def test__delete_credentials_sends_token_key(self):
        origin = make_origin()
        delete_authorisation_token = (
            origin.Account._handler.delete_authorisation_token)
        delete_authorisation_token.return_value = None
        credentials = make_Credentials()

        origin.Account.delete_credentials(credentials)

        delete_authorisation_token.assert_called_once_with(
            token_key=credentials.token_key)
