"""Test for `alburnum.maas.viscera.events`."""

__all__ = []

import random
from unittest.mock import MagicMock

from alburnum.maas.testing import (
    make_mac_address,
    make_name_without_spaces,
    TestCase,
)
from testtools.matchers import IsInstance

from .. import events


def bind(cls, origin=None, handler=None):
    return cls.bind(
        (MagicMock() if origin is None else origin),
        (MagicMock() if handler is None else handler),
        name=(cls.__name__ + "#Test"),
    )


class TestEventsQuery(TestCase):
    """Tests for `Events.query`."""

    def test__query_without_arguments_results_in_empty_bones_query(self):
        obj = bind(events.Events)
        obj.query()
        obj._handler.query.assert_called_once_with()

    def test__query_arguments_are_assembled_and_passed_to_bones_handler(self):
        obj = bind(events.Events)
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
        for level in events.Level:
            for value in (level, level.name, level.value):
                obj = bind(events.Events)
                obj.query(level=value)
                obj._handler.query.assert_called_once_with(level=[level.name])

    def test__query_before_argument_is_passed_to_bones_handler(self):
        obj = bind(events.Events)
        before = random.randint(1, 1000)
        obj.query(before=before)
        obj._handler.query.assert_called_once_with(before=[str(before)])

    def test__query_after_argument_is_passed_to_bones_handler(self):
        obj = bind(events.Events)
        after = random.randint(1, 1000)
        obj.query(after=after)
        obj._handler.query.assert_called_once_with(after=[str(after)])

    def test__cannot_query_with_both_before_and_after(self):
        self.assertRaises(ValueError, events.Events.query, before=2, after=1)


class TestEvents(TestCase):
    """Tests for `Events`."""

    def test__prev_requests_page_of_older_events(self):
        obj = bind(events.Events)
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
        obj = bind(events.Events)
        evts = obj({
            "events": [],
            "prev_uri": "endpoint?before=100&limit=20&foo=abc",
            "next_uri": "endpoint?after=119&limit=20&foo=123",
        })
        self.assertThat(evts.next(), IsInstance(events.Events))
        evts._handler.query.assert_called_once_with(
            after=["119"], limit=["20"], foo=["123"],
        )
