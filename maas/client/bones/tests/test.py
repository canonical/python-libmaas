"""Tests for `maas.client.bones`."""

import json
import random
from unittest.mock import ANY, Mock
from urllib.parse import parse_qsl, urlparse
from uuid import uuid1

from testtools.matchers import Equals, Is, MatchesStructure

from .. import testing
from ... import bones
from ...testing import TestCase
from ...utils.tests.test_auth import make_Credentials


class TestSessionAPI(TestCase):
    def test__fromURL_raises_SessionError_when_request_fails(self):
        fixture = self.useFixture(testing.DescriptionServer(b"bogus"))
        error = self.assertRaises(
            bones.SessionError, bones.SessionAPI.fromURL, fixture.url + "bogus/"
        )
        self.assertEqual(fixture.url + "bogus/ -> 404 Not Found", str(error))

    def test__fromURL_raises_SessionError_when_content_not_json(self):
        fixture = self.useFixture(testing.DescriptionServer())
        fixture.handler.content_type = "text/json"
        error = self.assertRaises(
            bones.SessionError, bones.SessionAPI.fromURL, fixture.url
        )
        self.assertEqual("Expected application/json, got: text/json", str(error))

    async def test__fromURL_sets_credentials_on_session(self):
        fixture = self.useFixture(testing.DescriptionServer())
        credentials = make_Credentials()
        session = await bones.SessionAPI.fromURL(fixture.url, credentials=credentials)
        self.assertIs(credentials, session.credentials)

    async def test__fromURL_sets_insecure_on_session(self):
        insecure = random.choice((True, False))
        fixture = self.useFixture(testing.DescriptionServer())
        session = await bones.SessionAPI.fromURL(fixture.url, insecure=insecure)
        self.assertThat(session.insecure, Is(insecure))

    async def test__fromURL_sets_scheme_on_session(self):
        insecure = random.choice((True, False))
        fixture = self.useFixture(testing.DescriptionServer())
        session = await bones.SessionAPI.fromURL(fixture.url, insecure=insecure)
        self.assertThat(session.scheme, Equals("http"))


class TestSessionAPI_APIVersions(TestCase):
    """Tests for `SessionAPI` with multiple API versions."""

    scenarios = tuple(
        (name, dict(version=version, path=path))
        for name, version, path in testing.list_api_descriptions()
    )

    async def test__fromURL_downloads_description(self):
        description = self.path.read_bytes()
        fixture = self.useFixture(testing.DescriptionServer(description))
        session = await bones.SessionAPI.fromURL(fixture.url)
        self.assertEqual(json.loads(description.decode("utf-8")), session.description)


class TestActionAPI_APIVersions(TestCase):
    """Tests for `ActionAPI` with multiple API versions."""

    scenarios = tuple(
        (name, dict(version=version, description=description))
        for name, version, description in testing.api_descriptions
    )

    url = "http://127.0.0.1:8080/MAAS/api/2.0/"

    def test__Version_read(self):
        session = bones.SessionAPI(self.url, self.description)
        action = session.Version.read
        self.assertThat(
            action,
            MatchesStructure.byEquality(
                name="read",
                fullname="Version.read",
                method="GET",
                handler=session.Version,
                is_restful=True,
                op=None,
            ),
        )

    def test__Machines_deployment_status(self):
        if self.version > (2, 0):
            self.skipTest("Machines.deployment_status only in <= 2.0")

        session = bones.SessionAPI(self.url, self.description, ("a", "b", "c"))
        action = session.Machines.deployment_status
        self.assertThat(
            action,
            MatchesStructure.byEquality(
                name="deployment_status",
                fullname="Machines.deployment_status",
                method="GET",
                handler=session.Machines,
                is_restful=False,
                op="deployment_status",
            ),
        )

    def test__Machines_power_parameters(self):
        session = bones.SessionAPI(self.url, self.description, ("a", "b", "c"))
        action = session.Machines.power_parameters
        self.assertThat(
            action,
            MatchesStructure.byEquality(
                name="power_parameters",
                fullname="Machines.power_parameters",
                method="GET",
                handler=session.Machines,
                is_restful=False,
                op="power_parameters",
            ),
        )


class TestCallAPI_APIVersions(TestCase):
    """Tests for `CallAPI` with multiple API versions."""

    scenarios = tuple(
        (name, dict(version=version, description=description))
        for name, version, description in testing.api_descriptions
    )

    url = "http://127.0.0.1:8080/MAAS/api/2.0/"

    def test__marshals_lists_into_query_as_repeat_parameters(self):
        system_ids = list(str(uuid1()) for _ in range(3))
        session = bones.SessionAPI(self.url, self.description, ("a", "b", "c"))
        call = session.Machines.power_parameters.bind()
        call.dispatch = Mock()

        call.call(nodes=system_ids)

        call.dispatch.assert_called_once_with(ANY, ANY, ANY)
        uri, body, headers = call.dispatch.call_args[0]
        uri = urlparse(uri)
        self.assertThat(uri.path, Equals("/MAAS/api/2.0/machines/"))
        query_expected = [("op", "power_parameters")]
        query_expected.extend(("nodes", system_id) for system_id in system_ids)
        query_observed = parse_qsl(uri.query)
        self.assertThat(query_observed, Equals(query_expected))
