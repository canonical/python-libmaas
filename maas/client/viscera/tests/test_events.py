"""Test for `maas.client.viscera.events`."""

from datetime import datetime
from itertools import (
    chain,
    count,
)
import random
from unittest.mock import sentinel

from testtools.matchers import (
    Equals,
    IsInstance,
)

from .. import events
from ...testing import (
    make_mac_address,
    make_name_without_spaces,
    make_range,
    TestCase,
)
from ..testing import bind


event_ids = count(1)


def make_Event_dict():
    return {
        "id": next(event_ids),
        "type": make_name_without_spaces("event-type"),
        "node": random.randint(1, 99),
        "hostname": make_name_without_spaces("host"),
        "level": random.choice(list(events.Level)),
        "created": datetime.utcnow().strftime("%a, %d %b. %Y %H:%M:%S"),
        "description": make_name_without_spaces("description"),
    }


def make_origin():
    # Create a new origin with Events and Event. The former refers to the
    # latter via the origin, hence why it must be bound.
    origin = bind(events.Events, events.Event)
    # Prepare a sensible default response from Events.query.
    events_query = origin.session.handlers[events.Events.__name__].query
    events_query.return_value = make_queried_events()
    return origin


def make_queried_events():
    """Mimic the object returned from a query."""
    return {
        "events": [], "prev_uri": sentinel.prev_uri,
        "next_uri": sentinel.next_uri,
    }


class TestEventsQuery(TestCase):
    """Tests for `Events.query`."""

    def test__query_without_arguments_results_in_empty_bones_query(self):
        obj = make_origin().Events
        obj.query()
        obj._handler.query.assert_called_once_with()

    def test__query_arguments_are_assembled_and_passed_to_bones_handler(self):
        obj = make_origin().Events
        arguments = {
            "hostnames": (
                make_name_without_spaces("hostname"),
                make_name_without_spaces("hostname"),
            ),
            "domains": (
                make_name_without_spaces("domain"),
                make_name_without_spaces("domain"),
            ),
            "zones": (
                make_name_without_spaces("zone"),
                make_name_without_spaces("zone"),
            ),
            "macs": (
                make_mac_address(),
                make_mac_address(),
            ),
            "system_ids": (
                make_name_without_spaces("system-id"),
                make_name_without_spaces("system-id"),
            ),
            "agent_name": make_name_without_spaces("agent"),
            "level": random.choice(list(events.Level)),
            "limit": random.randrange(1, 1000),
        }
        obj.query(**arguments)
        expected = {
            "hostname": list(arguments["hostnames"]),
            "domain": list(arguments["domains"]),
            "zone": list(arguments["zones"]),
            "mac_address": list(arguments["macs"]),
            "id": list(arguments["system_ids"]),
            "agent_name": [arguments["agent_name"]],
            "level": [arguments["level"].name],
            "limit": [str(arguments["limit"])],
        }
        obj._handler.query.assert_called_once_with(**expected)

    def test__query_level_is_normalised(self):
        obj = make_origin().Events
        for level in events.Level:
            for value in (level, level.name, level.value):
                obj._handler.query.reset_mock()
                obj.query(level=value)
                obj._handler.query.assert_called_once_with(level=[level.name])

    def test__query_before_argument_is_passed_to_bones_handler(self):
        obj = make_origin().Events
        before = random.randint(1, 1000)
        obj.query(before=before)
        obj._handler.query.assert_called_once_with(before=[str(before)])

    def test__query_after_argument_is_passed_to_bones_handler(self):
        obj = make_origin().Events
        after = random.randint(1, 1000)
        obj.query(after=after)
        obj._handler.query.assert_called_once_with(after=[str(after)])

    def test__cannot_query_with_both_before_and_after(self):
        self.assertRaises(ValueError, events.Events.query, before=2, after=1)


class TestEvents(TestCase):
    """Tests for `Events`."""

    def test__prev_requests_page_of_older_events(self):
        obj = make_origin().Events
        evts = obj({
            "events": [],
            "prev_uri": "endpoint?before=100&limit=20&foo=abc",
            "next_uri": "endpoint?after=119&limit=20&foo=123",
        })
        self.assertThat(evts.prev(), IsInstance(events.Events))
        evts._handler.query.assert_called_once_with(
            before=["100"], limit=["20"], foo=["abc"],
        )

    def test__next_requests_page_of_newer_events(self):
        obj = make_origin().Events
        evts = obj({
            "events": [],
            "prev_uri": "endpoint?before=100&limit=20&foo=abc",
            "next_uri": "endpoint?after=119&limit=20&foo=123",
        })
        self.assertThat(evts.next(), IsInstance(events.Events))
        evts._handler.query.assert_called_once_with(
            after=["119"], limit=["20"], foo=["123"],
        )

    def test__forwards_returns_a_continuous_iterator(self):
        pages = [
            {
                "events": [make_Event_dict() for _ in make_range()],
                "prev_uri": "?going=backwards",
                "next_uri": "?going=forwards",
            },
            {
                "events": [make_Event_dict() for _ in make_range()],
                "prev_uri": "?going=backwards",
                "next_uri": "?going=forwards",
            },
            # An empty page is taken to mean "stop".
            {
                "events": [],
                "prev_uri": "?going=backwards",
                "next_uri": "?going=forwards",
            },
        ]
        obj = make_origin().Events
        obj._handler.query.side_effect = pages
        self.assertThat(
            [evt._data for evt in obj.query().forwards()],
            Equals(list(chain.from_iterable(
                reversed(page["events"]) for page in pages))))
        # The query parameters in next_uri get passed through to bones.
        obj._handler.query.assert_called_with(going=["forwards"])

    def test__backwards_returns_a_continuous_iterator(self):
        pages = [
            {
                "events": [make_Event_dict() for _ in make_range()],
                "prev_uri": "?going=backwards",
                "next_uri": "?going=forwards",
            },
            {
                "events": [make_Event_dict() for _ in make_range()],
                "prev_uri": "?going=backwards",
                "next_uri": "?going=forwards",
            },
            # An empty page is taken to mean "stop".
            {
                "events": [],
                "prev_uri": "?going=backwards",
                "next_uri": "?going=forwards",
            },
        ]
        obj = make_origin().Events
        obj._handler.query.side_effect = pages
        self.assertThat(
            [evt._data for evt in obj.query().backwards()],
            Equals(list(chain.from_iterable(
                page["events"] for page in pages))))
        # The query parameters in prev_uri get passed through to bones.
        obj._handler.query.assert_called_with(going=["backwards"])
