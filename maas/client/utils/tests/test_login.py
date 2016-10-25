"""Tests for `maas.client.utils.login`."""

__all__ = []

from urllib.parse import urlparse

from testtools.matchers import (
    Equals,
    Is,
    IsInstance,
)

from .. import (
    api_url,
    login,
    profiles,
)
from .test_auth import make_credentials
from ...testing import (
    make_name_without_spaces,
    TestCase,
)


class TestLogin(TestCase):
    """Tests for `maas.client.utils.login.login`."""

    def setUp(self):
        super(TestLogin, self).setUp()
        self.patch(login, "obtain_token").return_value = None
        self.patch(login, "fetch_api_description").return_value = {}

    def test__anonymous_when_neither_username_nor_password_provided(self):
        # Log-in without a user-name or a password.
        profile = login.login("http://example.org:5240/MAAS/")
        # No token was obtained, but the description was fetched.
        login.obtain_token.assert_not_called()
        login.fetch_api_description.assert_called_once_with(
            urlparse("http://example.org:5240/MAAS/api/2.0/"),
            None, False)
        # A Profile instance was returned with no credentials.
        self.assertThat(profile, IsInstance(profiles.Profile))
        self.assertThat(profile.credentials, Is(None))

    def test__authenticated_when_username_and_password_provided(self):
        credentials = login.obtain_token.return_value = make_credentials()
        # Log-in with a user-name and a password.
        profile = login.login("http://foo:bar@example.org:5240/MAAS/")
        # A token was obtained, and the description was fetched.
        login.obtain_token.assert_called_once_with(
            "http://example.org:5240/MAAS/api/2.0/",
            "foo", "bar", insecure=False)
        login.fetch_api_description.assert_called_once_with(
            urlparse("http://example.org:5240/MAAS/api/2.0/"),
            credentials, False)
        # A Profile instance was returned with the expected credentials.
        self.assertThat(profile, IsInstance(profiles.Profile))
        self.assertThat(profile.credentials, Is(credentials))

    def test__complains_when_username_but_not_password(self):
        self.assertRaises(
            login.UsernameWithoutPassword, login.login,
            "http://example.org:5240/MAAS/", username="alice")

    def test__complains_when_password_but_not_username(self):
        self.assertRaises(
            login.PasswordWithoutUsername, login.login,
            "http://example.org:5240/MAAS/", password="wonderland")

    def test__complains_when_username_in_URL_and_passed_explicitly(self):
        self.assertRaises(
            login.LoginError, login.login,
            "http://foo:bar@example.org:5240/MAAS/", username="alice")

    def test__complains_when_empty_username_in_URL_and_passed_explicitly(self):
        self.assertRaises(
            login.LoginError, login.login,
            "http://:bar@example.org:5240/MAAS/", username="alice")

    def test__complains_when_password_in_URL_and_passed_explicitly(self):
        self.assertRaises(
            login.LoginError, login.login,
            "http://foo:bar@example.org:5240/MAAS/", password="wonderland")

    def test__complains_when_empty_password_in_URL_and_passed_explicitly(self):
        self.assertRaises(
            login.LoginError, login.login,
            "http://foo:@example.org:5240/MAAS/", password="wonderland")

    def test__URL_is_normalised_to_point_at_API_endpoint(self):
        profile = login.login("http://example.org:5240/MAAS/")
        self.assertThat(profile.url, Equals(
            api_url("http://example.org:5240/MAAS/")))

    def test__profile_is_given_default_name_based_on_URL(self):
        domain = make_name_without_spaces("domain")
        profile = login.login("http://%s/MAAS/" % domain)
        self.assertThat(profile.name, Equals(domain))

    def test__API_description_is_saved_in_profile(self):
        description = login.fetch_api_description.return_value = {"foo": "bar"}
        profile = login.login("http://example.org:5240/MAAS/")
        self.assertThat(profile.description, Equals(description))

    def test__API_token_is_fetched_insecurely_if_requested(self):
        login.login("http://foo:bar@example.org:5240/MAAS/", insecure=True)
        login.obtain_token.assert_called_once_with(
            "http://example.org:5240/MAAS/api/2.0/",
            "foo", "bar", insecure=True)

    def test__API_description_is_fetched_insecurely_if_requested(self):
        login.login("http://example.org:5240/MAAS/", insecure=True)
        login.fetch_api_description.assert_called_once_with(
            urlparse("http://example.org:5240/MAAS/api/2.0/"),
            None, True)

    def test__uses_username_from_URL_if_set(self):
        login.login("http://foo@maas.io/", password="bar")
        login.obtain_token.assert_called_once_with(
            "http://maas.io/api/2.0/", "foo", "bar", insecure=False)

    def test__uses_username_and_password_from_URL_if_set(self):
        login.login("http://foo:bar@maas.io/")
        login.obtain_token.assert_called_once_with(
            "http://maas.io/api/2.0/", "foo", "bar", insecure=False)

    def test__uses_empty_username_and_password_in_URL_if_set(self):
        login.login("http://:@maas.io/")
        login.obtain_token.assert_called_once_with(
            "http://maas.io/api/2.0/", "", "", insecure=False)
