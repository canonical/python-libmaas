"""Tests for `maas.client.bones`."""

__all__ = []

from fnmatch import fnmatchcase
import http
import http.server
import json
from os.path import splitext
from pathlib import Path
import re
import ssl
import threading
from unittest.mock import (
    ANY,
    Mock,
    sentinel,
)
from urllib.parse import (
    parse_qsl,
    urlparse,
)
from uuid import uuid1

import fixtures
import httplib2
from pkg_resources import (
    resource_filename,
    resource_listdir,
)
from testtools.matchers import (
    Equals,
    MatchesStructure,
)

from ... import bones
from ...testing import TestCase
from ...utils.tests.test_auth import make_credentials


def list_api_descriptions():
    for filename in resource_listdir(__name__, "."):
        if fnmatchcase(filename, "api*.json"):
            path = resource_filename(__name__, filename)
            name, _ = splitext(filename)
            yield name, Path(path)


class DescriptionHandler(http.server.BaseHTTPRequestHandler):
    """An HTTP request handler that serves only API descriptions.

    The `desc` attribute ought to be specified, for example by subclassing, or
    by using the `make` class-method.

    The `content_type` attribute can be overridden to simulate a different
    Content-Type header for the description.
    """

    # Override these in subclasses.
    description = b'{"resources": []}'
    content_type = "application/json"

    @classmethod
    def make(cls, description=description):
        return type(
            "DescriptionHandler", (cls, ),
            {"description": description},
        )

    def setup(self):
        super(DescriptionHandler, self).setup()
        self.logs = []

    def log_message(self, *args):
        """By default logs go to stdout/stderr. Instead, capture them."""
        self.logs.append(args)

    def do_GET(self):
        version_match = re.match(r"/MAAS/api/([0-9.]+)/describe/$", self.path)
        if version_match is None:
            self.send_error(http.HTTPStatus.NOT_FOUND)
        else:
            self.send_response(http.HTTPStatus.OK)
            self.send_header("Content-Type", self.content_type)
            self.send_header("Content-Length", str(len(self.description)))
            self.end_headers()
            self.wfile.write(self.description)


class DescriptionServer(fixtures.Fixture):
    """Fixture to start up an HTTP server for API descriptions only.

    :ivar handler: A `DescriptionHandler` subclass.
    :ivar server: An `http.server.HTTPServer` instance.
    :ivar url: A URL that points to the API that `server` is mocking.
    """

    def __init__(self, description=DescriptionHandler.description):
        super(DescriptionServer, self).__init__()
        self.description = description

    def _setUp(self):
        self.handler = DescriptionHandler.make(self.description)
        self.server = http.server.HTTPServer(("", 0), self.handler)
        self.url = "http://%s:%d/MAAS/api/2.0/" % self.server.server_address
        threading.Thread(target=self.server.serve_forever).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)


class TestSessionAPI(TestCase):

    def test__fromURL_raises_SessionError_when_TLS_fails(self):
        request = self.patch(httplib2.Http, "request")
        request.side_effect = ssl.SSLError
        error = self.assertRaises(
            bones.SessionError, bones.SessionAPI.fromURL, "")
        self.assertEqual("Certificate verification failed.", str(error))

    def test__fromURL_raises_SessionError_when_request_fails(self):
        fixture = self.useFixture(DescriptionServer(b"bogus"))
        error = self.assertRaises(
            bones.SessionError, bones.SessionAPI.fromURL,
            fixture.url + "bogus/")
        self.assertEqual(
            fixture.url + "bogus/ -> 404 Not Found",
            str(error))

    def test__fromURL_raises_SessionError_when_content_not_json(self):
        fixture = self.useFixture(DescriptionServer())
        fixture.handler.content_type = "text/json"
        error = self.assertRaises(
            bones.SessionError, bones.SessionAPI.fromURL, fixture.url)
        self.assertEqual(
            "Expected application/json, got: text/json",
            str(error))

    def test__fromURL_sets_credentials_on_session(self):
        fixture = self.useFixture(DescriptionServer())
        credentials = make_credentials()
        session = bones.SessionAPI.fromURL(
            fixture.url, credentials=credentials)
        self.assertIs(credentials, session.credentials)

    def test__fromURL_sets_insecure_on_session(self):
        fixture = self.useFixture(DescriptionServer())
        session = bones.SessionAPI.fromURL(
            fixture.url, insecure=sentinel.insecure)
        self.assertIs(sentinel.insecure, session.insecure)


class TestSessionAPI_APIVersions(TestCase):
    """Tests for `SessionAPI` with multiple API versions."""

    scenarios = tuple(
        (name, dict(path=path))
        for name, path in list_api_descriptions()
    )

    def test__fromURL_downloads_description(self):
        description = self.path.read_bytes()
        fixture = self.useFixture(DescriptionServer(description))
        session = bones.SessionAPI.fromURL(fixture.url)
        self.assertEqual(
            json.loads(description.decode("utf-8")),
            session.description)


def load_api_descriptions():
    for name, path in list_api_descriptions():
        description = path.read_text("utf-8")
        yield name, json.loads(description)


api_descriptions = list(load_api_descriptions())
assert len(api_descriptions) != 0


class TestActionAPI_APIVersions(TestCase):
    """Tests for `ActionAPI` with multiple API versions."""

    scenarios = tuple(
        (name, dict(description=description))
        for name, description in api_descriptions
    )

    def test__Version_read(self):
        session = bones.SessionAPI(self.description)
        action = session.Version.read
        self.assertThat(action, MatchesStructure.byEquality(
            name="read", fullname="Version.read", method="GET",
            handler=session.Version, is_restful=True, op=None,
        ))

    def test__Machines_deployment_status(self):
        session = bones.SessionAPI(self.description, ("a", "b", "c"))
        action = session.Machines.deployment_status
        self.assertThat(action, MatchesStructure.byEquality(
            name="deployment_status", fullname="Machines.deployment_status",
            method="GET", handler=session.Machines, is_restful=False,
            op="deployment_status",
        ))


class TestCallAPI_APIVersions(TestCase):
    """Tests for `CallAPI` with multiple API versions."""

    scenarios = tuple(
        (name, dict(description=description))
        for name, description in api_descriptions
    )

    def test__marshals_lists_into_query_as_repeat_parameters(self):
        system_ids = list(str(uuid1()) for _ in range(3))
        session = bones.SessionAPI(self.description, ("a", "b", "c"))
        call = session.Machines.deployment_status.bind()
        call.dispatch = Mock()

        call.call(nodes=system_ids)

        call.dispatch.assert_called_once_with(ANY, ANY, ANY)
        uri, body, headers = call.dispatch.call_args[0]
        uri = urlparse(uri)
        self.assertThat(uri.path, Equals("/MAAS/api/2.0/machines/"))
        query_expected = [('op', 'deployment_status')]
        query_expected.extend(('nodes', system_id) for system_id in system_ids)
        query_observed = parse_qsl(uri.query)
        self.assertThat(query_observed, Equals(query_expected))
