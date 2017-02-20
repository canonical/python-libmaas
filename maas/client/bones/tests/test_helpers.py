"""Tests for `maas.client.utils.remote`."""

import json

from testtools.matchers import Equals

from .. import testing
from ...testing import (
    make_name,
    TestCase,
)
from ...utils.auth import Credentials
from ..helpers import (
    fetch_api_description,
    RemoteError,
)


def make_credentials():
    return Credentials(
        make_name('consumer_key'),
        make_name('token_key'),
        make_name('secret_key'),
    )


class TestFetchAPIDescription(TestCase):
    """Tests for `fetch_api_description`."""

    def test__raises_RemoteError_when_request_fails(self):
        fixture = self.useFixture(testing.DescriptionServer(b"bogus"))
        error = self.assertRaises(
            RemoteError, self.loop.run_until_complete,
            fetch_api_description(fixture.url + "bogus/"))
        self.assertEqual(
            fixture.url + "bogus/ -> 404 Not Found",
            str(error))

    def test__raises_RemoteError_when_content_not_json(self):
        fixture = self.useFixture(testing.DescriptionServer())
        fixture.handler.content_type = "text/json"
        error = self.assertRaises(
            RemoteError, self.loop.run_until_complete,
            fetch_api_description(fixture.url))
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
            fetch_api_description(fixture.url))
        self.assertThat(
            description_fetched, Equals(
                json.loads(description.decode("utf-8"))))
