"""Tests for `maas.client.utils.connect`."""

__all__ = []

from urllib.parse import urlparse

from testtools.matchers import (
    Equals,
    Is,
    IsInstance,
)

from .. import (
    api_url,
    connect,
    profiles,
)
from ...bones import helpers
from ...testing import (
    AsyncMock,
    make_name_without_spaces,
    TestCase,
)
from .test_auth import make_credentials


class TestConnect(TestCase):
    """Tests for `maas.client.utils.connect.connect`."""

    def setUp(self):
        super(TestConnect, self).setUp()
        self.patch(
            helpers, "fetch_api_description",
            AsyncMock(return_value={}))

    def test__anonymous_when_no_apikey_provided(self):
        # Connect without an apikey.
        profile = connect.connect("http://example.org:5240/MAAS/")
        helpers.fetch_api_description.assert_called_once_with(
            urlparse("http://example.org:5240/MAAS/api/2.0/"),
            None, False)
        # A Profile instance was returned with no credentials.
        self.assertThat(profile, IsInstance(profiles.Profile))
        self.assertThat(profile.credentials, Is(None))

    def test__connected_when_apikey_provided(self):
        credentials = make_credentials()
        # Connect with an apikey.
        profile = connect.connect(
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
            connect.ConnectError, connect.connect,
            "http://foo:bar@example.org:5240/MAAS/")

    def test__complains_when_password_in_URL(self):
        self.assertRaises(
            connect.ConnectError, connect.connect,
            "http://:bar@example.org:5240/MAAS/")

    def test__URL_is_normalised_to_point_at_API_endpoint(self):
        profile = connect.connect("http://example.org:5240/MAAS/")
        self.assertThat(profile.url, Equals(
            api_url("http://example.org:5240/MAAS/")))

    def test__profile_is_given_default_name_based_on_URL(self):
        domain = make_name_without_spaces("domain")
        profile = connect.connect("http://%s/MAAS/" % domain)
        self.assertThat(profile.name, Equals(domain))

    def test__API_description_is_saved_in_profile(self):
        description = helpers.fetch_api_description.return_value = {
            "foo": "bar"}
        profile = connect.connect("http://example.org:5240/MAAS/")
        self.assertThat(profile.description, Equals(description))

    def test__API_description_is_fetched_insecurely_if_requested(self):
        connect.connect("http://example.org:5240/MAAS/", insecure=True)
        helpers.fetch_api_description.assert_called_once_with(
            urlparse("http://example.org:5240/MAAS/api/2.0/"),
            None, True)
