"""Objects for events."""

__all__ = [
    "Events",
]

from datetime import datetime
import enum
from functools import partial
import logging
from typing import (
    Iterable,
    Union,
)
from urllib.parse import (
    parse_qs,
    urlparse,
)

import pytz

from . import (
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
)
from ..utils.typecheck import typed

#
# The query API call returns:
#
#     dict(
#         count=displayed_events_count,
#         events=[...],
#         next_uri=next_uri,
#         prev_uri=prev_uri,
#     )
#
# An event looks like:
#
#     dict(
#         node=event.node.system_id,
#         hostname=event.node.hostname,
#         id=event.id,
#         level=event.type.level_str,
#         created=event.created.strftime('%a, %d %b. %Y %H:%M:%S'),
#         type=event.type.description,
#         description=event.description
#     )
#
# Notes:
# 1. displayed_events_count is len(events). In other words, superfluous.
#


class Level(enum.IntEnum):
    """Logging levels used in MAAS.

    They happen to correspond to levels in the `logging` module.
    """

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    @classmethod
    def normalise(cls, level):
        """Convert the given level into a `Level`.

        :param level: A `Level` instance, a string that matches the name of a
            level, or an integer matching the value of a level.
        :raise ValueError: If the level cannot be found.
        """
        try:
            return cls[level]
        except KeyError:
            return cls(level)


class EventsType(ObjectType):
    """Metaclass for `Events`."""

    Level = Level

    @typed
    def query(
            cls, *,
            hostnames: Iterable[str]=None,
            domains: Iterable[str]=None,
            zones: Iterable[str]=None,
            macs: Iterable[str]=None,
            system_ids: Iterable[str]=None,
            agent_name: str=None,
            level: Union[Level, int, str]=None,
            after: int=None,
            limit: int=None):
        """Query MAAS for matching events."""

        params = {}

        if hostnames is not None:
            params["hostname"] = list(hostnames)
        if domains is not None:
            params["domain"] = list(domains)
        if zones is not None:
            params["zone"] = list(zones)
        if macs is not None:
            params["mac_address"] = list(macs)
        if system_ids is not None:
            params["id"] = list(system_ids)
        if agent_name is not None:
            params["agent_name"] = [agent_name]
        if level is not None:
            level = Level.normalise(level)
            params["level"] = [level.name]
        if after is not None:
            params["after"] = ["{:d}".format(after)]
        if limit is not None:
            params["limit"] = ["{:d}".format(limit)]

        data = cls._handler.query(**params)
        return cls(data)


def parse_created_timestamp(created):
    created = datetime.strptime(created, "%a, %d %b. %Y %H:%M:%S")
    return created.replace(tzinfo=pytz.UTC)


class Events(ObjectSet, metaclass=EventsType):
    """MAAS event information."""

    __slots__ = "_prev_uri", "_next_uri"

    def __init__(self, eventmap):
        events = map(self._object, eventmap["events"])
        super(Events, self).__init__(events)
        self._prev_uri = eventmap["prev_uri"]
        self._next_uri = eventmap["next_uri"]

    def _fetch(self, uri, count):
        query = urlparse(uri).query
        params = parse_qs(query, errors="strict")

        if count is None:
            if "limit" in params:
                pass  # Stick to the current limit.
            else:
                params["limit"] = ["{:d}".format(min(1, len(self)))]
        else:
            params["limit"] = ["{:d}".format(count)]

        data = self._handler.query(**params)
        return self.__class__(data)

    def prev(self, count=None):
        return self._fetch(self._prev_uri, count)

    def next(self, count=None):
        return self._fetch(self._next_uri, count)


def truncate(length, text):  # TODO: Move into utils.
    """Truncate the given text to the given length.

    If the text is longer than the ``length``, return a new string that
    contains ``length - 1`` characters of text followed by an ellipsis.
    Otherwise return the given text unaltered.
    """
    if len(text) > length:
        return text[:length - 1] + "…"
    else:
        return text


class Event(Object):
    """An event."""

    event_id = ObjectField(
        "id", readonly=True)
    event_type = ObjectField(
        "type", readonly=True)

    system_id = ObjectField(
        "node", readonly=True)
    hostname = ObjectField(
        "hostname", readonly=True)

    level = ObjectField.Checked(
        "level", Level.normalise, readonly=True)
    created = ObjectField.Checked(
        "created", parse_created_timestamp, readonly=True)

    description = ObjectField(
        "description", readonly=True)
    description_short = ObjectField.Checked(
        "description", partial(truncate, 50), readonly=True)

    def __repr__(self):
        return (
            "<{self.__class__.__name__} {self.created:%Y-%m-%d %H:%M:%S} "
            "{self.level.name} {self.hostname} {self.description_short!r}>"
        ).format(self=self)
