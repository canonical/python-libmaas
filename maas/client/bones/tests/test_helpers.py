"""Tests for `maas.client.bones.helpers`."""

import json
from urllib.parse import urlparse

from testtools.matchers import (
    Equals,
    Is,
    IsInstance,
)

from .. import (
    helpers,
    testing,
)
from ...testing import (
    AsyncMock,
    make_name,
    make_name_without_spaces,
    TestCase,
)
from ...utils import (
    api_url,
    profiles,
)
from ...utils.testing import make_Credentials


class TestFetchAPIDescription(TestCase):
    """Tests for `fetch_api_description`."""

    def test__raises_RemoteError_when_request_fails(self):
        fixture = self.useFixture(testing.DescriptionServer(b"bogus"))
        error = self.assertRaises(
            helpers.RemoteError, self.loop.run_until_complete,
            helpers.fetch_api_description(fixture.url + "bogus/"))
        self.assertEqual(
            fixture.url + "bogus/ -> 404 Not Found",
            str(error))

    def test__raises_RemoteError_when_content_not_json(self):
        fixture = self.useFixture(testing.DescriptionServer())
        fixture.handler.content_type = "text/json"
        error = self.assertRaises(
            helpers.RemoteError, self.loop.run_until_complete,
            helpers.fetch_api_description(fixture.url))
        self.assertEqual(
            "Expected application/json, got: text/json",
            str(error))


class TestFetchAPIDescription_APIVersions(TestCase):
    """Tests for `fetch_api_description` with multiple API versions."""

    scenarios = tuple(
        (name, dict(path=path))
        for name, path in testing.list_api_descriptions()
    )

    def test__downloads_description(self):
        description = self.path.read_bytes()
        fixture = self.useFixture(testing.DescriptionServer(description))
        description_fetched = self.loop.run_until_complete(
            helpers.fetch_api_description(fixture.url))
        self.assertThat(
            description_fetched, Equals(
                json.loads(description.decode("utf-8"))))


class TestConnect(TestCase):
    """Tests for `maas.client.utils.connect.connect`."""

    def setUp(self):
        super(TestConnect, self).setUp()
        self.patch(
            helpers, "fetch_api_description",
            AsyncMock(return_value={}))

    def test__anonymous_when_no_apikey_provided(self):
        # Connect without an apikey.
        profile = helpers.connect("http://example.org:5240/MAAS/")
        helpers.fetch_api_description.assert_called_once_with(
            urlparse("http://example.org:5240/MAAS/api/2.0/"),
            None, False)
        # A Profile instance was returned with no credentials.
        self.assertThat(profile, IsInstance(profiles.Profile))
        self.assertThat(profile.credentials, Is(None))

    def test__connected_when_apikey_provided(self):
        credentials = make_Credentials()
        # Connect with an apikey.
        profile = helpers.connect(
            "http://example.org:5240/MAAS/", apikey=str(credentials))
        # The description was fetched.
        helpers.fetch_api_description.assert_called_once_with(
            urlparse("http://example.org:5240/MAAS/api/2.0/"),
            credentials, False)
        # A Profile instance was returned with the expected credentials.
        self.assertThat(profile, IsInstance(profiles.Profile))
        self.assertThat(profile.credentials, Equals(credentials))

    def test__complains_when_username_in_URL(self):
        self.assertRaises(
            helpers.ConnectError, helpers.connect,
            "http://foo:bar@example.org:5240/MAAS/")

    def test__complains_when_password_in_URL(self):
        self.assertRaises(
            helpers.ConnectError, helpers.connect,
            "http://:bar@example.org:5240/MAAS/")

    def test__URL_is_normalised_to_point_at_API_endpoint(self):
        profile = helpers.connect("http://example.org:5240/MAAS/")
        self.assertThat(profile.url, Equals(
            api_url("http://example.org:5240/MAAS/")))

    def test__profile_is_given_default_name_based_on_URL(self):
        domain = make_name_without_spaces("domain")
        profile = helpers.connect("http://%s/MAAS/" % domain)
        self.assertThat(profile.name, Equals(domain))

    def test__API_description_is_saved_in_profile(self):
        description = helpers.fetch_api_description.return_value = {
            "foo": "bar"}
        profile = helpers.connect("http://example.org:5240/MAAS/")
        self.assertThat(profile.description, Equals(description))

    def test__API_description_is_fetched_insecurely_if_requested(self):
        helpers.connect("http://example.org:5240/MAAS/", insecure=True)
        helpers.fetch_api_description.assert_called_once_with(
            urlparse("http://example.org:5240/MAAS/api/2.0/"),
            None, True)


class TestLogin(TestCase):
    """Tests for `maas.client.utils.login.login`."""

    def setUp(self):
        super(TestLogin, self).setUp()
        self.patch(helpers, "obtain_token").return_value = None
        self.patch(
            helpers, "fetch_api_description",
            AsyncMock(return_value={}))

    def test__anonymous_when_neither_username_nor_password_provided(self):
        # Log-in without a user-name or a password.
        profile = helpers.login("http://example.org:5240/MAAS/")
        # No token was obtained, but the description was fetched.
        helpers.obtain_token.assert_not_called()
        helpers.fetch_api_description.assert_called_once_with(
            urlparse("http://example.org:5240/MAAS/api/2.0/"),
            None, False)
        # A Profile instance was returned with no credentials.
        self.assertThat(profile, IsInstance(profiles.Profile))
        self.assertThat(profile.credentials, Is(None))

    def test__authenticated_when_username_and_password_provided(self):
        credentials = make_Credentials()
        helpers.obtain_token.return_value = credentials
        # Log-in with a user-name and a password.
        profile = helpers.login("http://foo:bar@example.org:5240/MAAS/")
        # A token was obtained, and the description was fetched.
        helpers.obtain_token.assert_called_once_with(
            "http://example.org:5240/MAAS/api/2.0/",
            "foo", "bar", insecure=False)
        helpers.fetch_api_description.assert_called_once_with(
            urlparse("http://example.org:5240/MAAS/api/2.0/"),
            credentials, False)
        # A Profile instance was returned with the expected credentials.
        self.assertThat(profile, IsInstance(profiles.Profile))
        self.assertThat(profile.credentials, Is(credentials))

    def test__complains_when_username_but_not_password(self):
        self.assertRaises(
            helpers.UsernameWithoutPassword, helpers.login,
            "http://example.org:5240/MAAS/", username="alice")

    def test__complains_when_password_but_not_username(self):
        self.assertRaises(
            helpers.PasswordWithoutUsername, helpers.login,
            "http://example.org:5240/MAAS/", password="wonderland")

    def test__complains_when_username_in_URL_and_passed_explicitly(self):
        self.assertRaises(
            helpers.LoginError, helpers.login,
            "http://foo:bar@example.org:5240/MAAS/", username="alice")

    def test__complains_when_empty_username_in_URL_and_passed_explicitly(self):
        self.assertRaises(
            helpers.LoginError, helpers.login,
            "http://:bar@example.org:5240/MAAS/", username="alice")

    def test__complains_when_password_in_URL_and_passed_explicitly(self):
        self.assertRaises(
            helpers.LoginError, helpers.login,
            "http://foo:bar@example.org:5240/MAAS/", password="wonderland")

    def test__complains_when_empty_password_in_URL_and_passed_explicitly(self):
        self.assertRaises(
            helpers.LoginError, helpers.login,
            "http://foo:@example.org:5240/MAAS/", password="wonderland")

    def test__URL_is_normalised_to_point_at_API_endpoint(self):
        profile = helpers.login("http://example.org:5240/MAAS/")
        self.assertThat(profile.url, Equals(
            api_url("http://example.org:5240/MAAS/")))

    def test__profile_is_given_default_name_based_on_URL(self):
        domain = make_name_without_spaces("domain")
        profile = helpers.login("http://%s/MAAS/" % domain)
        self.assertThat(profile.name, Equals(domain))

    def test__API_description_is_saved_in_profile(self):
        description = {make_name("key"): make_name("value")}
        helpers.fetch_api_description.return_value = description
        profile = helpers.login("http://example.org:5240/MAAS/")
        self.assertThat(profile.description, Equals(description))

    def test__API_token_is_fetched_insecurely_if_requested(self):
        helpers.login("http://foo:bar@example.org:5240/MAAS/", insecure=True)
        helpers.obtain_token.assert_called_once_with(
            "http://example.org:5240/MAAS/api/2.0/",
            "foo", "bar", insecure=True)

    def test__API_description_is_fetched_insecurely_if_requested(self):
        helpers.login("http://example.org:5240/MAAS/", insecure=True)
        helpers.fetch_api_description.assert_called_once_with(
            urlparse("http://example.org:5240/MAAS/api/2.0/"),
            None, True)

    def test__uses_username_from_URL_if_set(self):
        helpers.login("http://foo@maas.io/", password="bar")
        helpers.obtain_token.assert_called_once_with(
            "http://maas.io/api/2.0/", "foo", "bar", insecure=False)

    def test__uses_username_and_password_from_URL_if_set(self):
        helpers.login("http://foo:bar@maas.io/")
        helpers.obtain_token.assert_called_once_with(
            "http://maas.io/api/2.0/", "foo", "bar", insecure=False)

    def test__uses_empty_username_and_password_in_URL_if_set(self):
        helpers.login("http://:@maas.io/")
        helpers.obtain_token.assert_called_once_with(
            "http://maas.io/api/2.0/", "", "", insecure=False)
