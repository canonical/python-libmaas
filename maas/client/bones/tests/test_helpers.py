"""Tests for `maas.client.bones.helpers`."""

import json
from unittest.mock import Mock
from urllib.parse import (
    urlparse,
    urlsplit,
)

import aiohttp.web
from macaroonbakery.httpbakery import Client
from testtools import ExpectedException
from testtools.matchers import (
    Equals,
    Is,
    IsInstance,
    MatchesDict,
)

from .. import (
    helpers,
    testing,
)
from ...testing import (
    AsyncCallableMock,
    make_name,
    make_name_without_spaces,
    TestCase,
)
from ...utils import (
    api_url,
    profiles,
)
from ...utils.testing import make_Credentials
from ..testing import api_descriptions
from ..testing.server import ApplicationBuilder


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


class TestFetchAPIDescriptionURLs(TestCase):
    """Tests for URL types accepted by `fetch_api_description`."""

    scenarios = (
        ("string", dict(prepare=str)),
        ("split", dict(prepare=urlsplit)),
        ("parsed", dict(prepare=urlparse)),
    )

    def test__accepts_prepared_url(self):
        description = {"foo": make_name_without_spaces("bar")}
        description_json = json.dumps(description).encode("ascii")
        fixture = self.useFixture(testing.DescriptionServer(description_json))
        description_url = self.prepare(fixture.url)  # Parse, perhaps.
        description_fetched = self.loop.run_until_complete(
            helpers.fetch_api_description(description_url))
        self.assertThat(description_fetched, Equals(description))


class TestFetchAPIDescription_APIVersions(TestCase):
    """Tests for `fetch_api_description` with multiple API versions."""

    scenarios = tuple(
        (name, dict(version=version, path=path))
        for name, version, path in testing.list_api_descriptions()
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
            AsyncCallableMock(return_value={}))

    def test__anonymous(self):
        # Connect without an apikey.
        profile = helpers.connect(
            "http://example.org:5240/MAAS/")
        helpers.fetch_api_description.assert_called_once_with(
            urlparse("http://example.org:5240/MAAS/api/2.0/"), False)
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
            urlparse("http://example.org:5240/MAAS/api/2.0/"), False)
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
            urlparse("http://example.org:5240/MAAS/api/2.0/"), True)


class TestLogin(TestCase):
    """Tests for `maas.client.utils.login.login`."""

    def setUp(self):
        super(TestLogin, self).setUp()
        self.patch(
            helpers, "authenticate",
            AsyncCallableMock(return_value=None))
        self.patch(
            helpers, "fetch_api_description",
            AsyncCallableMock(return_value={}))

    def test__anonymous(self):
        # Log-in anonymously.
        profile = helpers.login(
            "http://example.org:5240/MAAS/", anonymous=True)
        # No token was obtained, but the description was fetched.
        helpers.authenticate.assert_not_called()
        # A Profile instance was returned with no credentials.
        self.assertThat(profile, IsInstance(profiles.Profile))
        self.assertThat(profile.credentials, Is(None))

    def test__macaroon_auth_with_no_username_and_password(self):
        credentials = make_Credentials()
        self.patch(
            helpers, "authenticate_with_macaroon",
            AsyncCallableMock(return_value=credentials))
        # Log-in without a user-name or a password.
        profile = helpers.login("http://example.org:5240/MAAS/")
        # A token is obtained via macaroons, but the description was fetched.
        # The description was fetched.
        helpers.fetch_api_description.assert_called_once_with(
            urlparse("http://example.org:5240/MAAS/api/2.0/"), False)
        # The returned profile uses credentials obtained from the
        # authentication
        self.assertThat(profile, IsInstance(profiles.Profile))
        self.assertThat(profile.credentials, Is(credentials))

    def test__authenticated_when_username_and_password_provided(self):
        credentials = make_Credentials()
        helpers.authenticate.return_value = credentials
        # Log-in with a user-name and a password.
        profile = helpers.login("http://foo:bar@example.org:5240/MAAS/")
        # A token was obtained, and the description was fetched.
        helpers.authenticate.assert_called_once_with(
            "http://example.org:5240/MAAS/api/2.0/",
            "foo", "bar", insecure=False)
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
        profile = helpers.login(
            "http://example.org:5240/MAAS/", anonymous=True)
        self.assertThat(profile.url, Equals(
            api_url("http://example.org:5240/MAAS/")))

    def test__profile_is_given_default_name_based_on_URL(self):
        domain = make_name_without_spaces("domain")
        profile = helpers.login(
            "http://%s/MAAS/" % domain, anonymous=True)
        self.assertThat(profile.name, Equals(domain))

    def test__API_description_is_saved_in_profile(self):
        description = {make_name("key"): make_name("value")}
        helpers.fetch_api_description.return_value = description
        profile = helpers.login(
            "http://example.org:5240/MAAS/", anonymous=True)
        self.assertThat(profile.description, Equals(description))

    def test__API_token_is_fetched_insecurely_if_requested(self):
        helpers.login("http://foo:bar@example.org:5240/MAAS/", insecure=True)
        helpers.authenticate.assert_called_once_with(
            "http://example.org:5240/MAAS/api/2.0/",
            "foo", "bar", insecure=True)

    def test__API_description_is_fetched_insecurely_if_requested(self):
        helpers.login(
            "http://example.org:5240/MAAS/", anonymous=True, insecure=True)
        helpers.fetch_api_description.assert_called_once_with(
            urlparse("http://example.org:5240/MAAS/api/2.0/"), True)

    def test__uses_username_from_URL_if_set(self):
        helpers.login("http://foo@maas.io/", password="bar")
        helpers.authenticate.assert_called_once_with(
            "http://maas.io/api/2.0/", "foo", "bar", insecure=False)

    def test__uses_username_and_password_from_URL_if_set(self):
        helpers.login("http://foo:bar@maas.io/")
        helpers.authenticate.assert_called_once_with(
            "http://maas.io/api/2.0/", "foo", "bar", insecure=False)

    def test__uses_empty_username_and_password_in_URL_if_set(self):
        helpers.login("http://:@maas.io/")
        helpers.authenticate.assert_called_once_with(
            "http://maas.io/api/2.0/", "", "", insecure=False)


class TestAuthenticate(TestCase):
    """Tests for `authenticate`."""

    scenarios = tuple(
        (name, dict(version=version, description=description))
        for name, version, description in api_descriptions)

    async def test__obtains_credentials_from_server(self):
        builder = ApplicationBuilder(self.description)

        @builder.handle("anon:Version.read")
        async def version(request):
            return {"capabilities": ["authenticate-api"]}

        credentials = make_Credentials()
        parameters = None

        @builder.route("POST", "/accounts/authenticate/")
        async def deploy(request):
            nonlocal parameters
            parameters = await request.post()
            return {
                "consumer_key": credentials.consumer_key,
                "token_key": credentials.token_key,
                "token_secret": credentials.token_secret,
            }

        username = make_name_without_spaces("username")
        password = make_name_without_spaces("password")

        async with builder.serve() as baseurl:
            credentials_observed = await helpers.authenticate(
                baseurl, username, password)

        self.assertThat(
            credentials_observed, Equals(credentials))
        self.assertThat(
            parameters, MatchesDict({
                "username": Equals(username),
                "password": Equals(password),
                "consumer": IsInstance(str),
            }))

    async def test__raises_error_when_server_does_not_support_authn(self):
        builder = ApplicationBuilder(self.description)

        @builder.handle("anon:Version.read")
        async def version(request):
            return {"capabilities": []}

        async with builder.serve() as baseurl:
            with ExpectedException(helpers.LoginNotSupported):
                await helpers.authenticate(baseurl, "username", "password")

    async def test__raises_error_when_server_rejects_credentials(self):
        builder = ApplicationBuilder(self.description)

        @builder.handle("anon:Version.read")
        async def version(request):
            return {"capabilities": ["authenticate-api"]}

        @builder.route("POST", "/accounts/authenticate/")
        async def deploy(request):
            raise aiohttp.web.HTTPForbidden()

        async with builder.serve() as baseurl:
            with ExpectedException(helpers.RemoteError):
                await helpers.authenticate(baseurl, "username", "password")


class TestAuthenticateWithMacaroon(TestCase):

    def setUp(self):
        super().setUp()
        self.mock_client_request = self.patch(Client, "request")
        self.token_result = {
            'consumer_key': 'abc', 'token_key': '123', 'token_secret': 'xyz'}
        self.mock_response = Mock()
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = self.token_result
        self.mock_client_request.return_value = self.mock_response

    async def test__authenticate_with_bakery_creates_token(self):
        credentials = await helpers.authenticate_with_macaroon(
            "http://example.com")
        self.assertEqual(credentials, "abc:123:xyz")
        # a call to create an API token is made
        self.mock_client_request.assert_called_once_with(
            "POST",
            "http://example.com/account/?op=create_authorisation_token",
            verify=True)

    async def test__authenticate_failed_request(self):
        self.mock_response.status_code = 500
        self.mock_response.text = "error!"
        try:
            await helpers.authenticate_with_macaroon("http://example.com")
        except helpers.LoginError as e:
            self.assertEqual(str(e), "Login failed: error!")
        else:
            self.fail("LoginError not raised")


class TestDeriveResourceName(TestCase):
    """Tests for `derive_resource_name`."""

    def test__removes_Anon_prefix(self):
        self.assertThat(
            helpers.derive_resource_name("AnonFooBar"),
            Equals("FooBar"))

    def test__removes_Handler_suffix(self):
        self.assertThat(
            helpers.derive_resource_name("FooBarHandler"),
            Equals("FooBar"))

    def test__normalises_Maas_to_MAAS(self):
        self.assertThat(
            helpers.derive_resource_name("Maas"),
            Equals("MAAS"))

    def test__does_all_the_above(self):
        self.assertThat(
            helpers.derive_resource_name("AnonMaasHandler"),
            Equals("MAAS"))
