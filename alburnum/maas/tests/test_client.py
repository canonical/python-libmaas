# Copyright 2015 Alburnum Ltd. This software is licensed under
# the GNU Affero General Public License version 3 (see LICENSE).

"""Tests for `alburnum.maas.client`."""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
)

str = None

__metaclass__ = type
__all__ = []

from fnmatch import fnmatchcase
import json
from os.path import splitext
from urlparse import (
    parse_qsl,
    urlparse,
)
from uuid import uuid1

from alburnum.maas import client
from mock import (
    ANY,
    Mock,
)
from pkg_resources import (
    resource_listdir,
    resource_stream,
)
from testscenarios import WithScenarios
from testtools import TestCase
from testtools.matchers import (
    Equals,
    MatchesStructure,
)


def load_api_descriptions():
    resource = "alburnum.maas.tests"
    for filename in resource_listdir(resource, ""):
        if fnmatchcase(filename, "api*.json"):
            name, _ = splitext(filename)
            with resource_stream(resource, filename) as stream:
                yield name, json.load(stream)


api_descriptions = list(load_api_descriptions())


class TestActionAPI(WithScenarios, TestCase):
    """Tests for `ActionAPI`."""

    scenarios = (
        (name, dict(description=description))
        for name, description in api_descriptions
    )

    def test__Version_read(self):
        session = client.SessionAPI(self.description)
        action = session.Version.read
        self.assertThat(action, MatchesStructure.byEquality(
            name="read", fullname="Version.read", method="GET",
            handler=session.Version, is_restful=True, op=None,
        ))

    def test__Nodes_deployment_status(self):
        session = client.SessionAPI(self.description, ("a", "b", "c"))
        action = session.Nodes.deployment_status
        self.assertThat(action, MatchesStructure.byEquality(
            name="deployment_status", fullname="Nodes.deployment_status",
            method="GET", handler=session.Nodes, is_restful=False,
            op="deployment_status",
        ))


class TestCallAPI(WithScenarios, TestCase):
    """Tests for `CallAPI`."""

    scenarios = (
        (name, dict(description=description))
        for name, description in api_descriptions
    )

    def test__marshals_lists_into_query_as_repeat_parameters(self):
        system_ids = list(unicode(uuid1()) for _ in xrange(3))
        session = client.SessionAPI(self.description, ("a", "b", "c"))
        call = session.Nodes.deployment_status.bind()
        call.dispatch = Mock()

        call.call(nodes=system_ids)

        call.dispatch.assert_called_once_with(ANY, ANY, ANY)
        uri, body, headers = call.dispatch.call_args[0]
        uri = urlparse(uri)
        self.assertThat(uri.path, Equals("/MAAS/api/1.0/nodes/"))
        query_expected = [('op', 'deployment_status')]
        query_expected.extend(('nodes', system_id) for system_id in system_ids)
        query_observed = parse_qsl(uri.query)
        self.assertThat(query_observed, Equals(query_expected))
