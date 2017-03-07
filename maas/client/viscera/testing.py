""" Testing framework for maas.client.viscera """

__all__ = [
    'bind',
]

from collections import Mapping
from itertools import chain
from unittest.mock import Mock

from . import OriginBase
from ..testing import AsyncCallableMock


def bind(*objects, session=None):
    """Bind `objects` into a new `Origin` derived from `session`.

    The origin is constructed using `maas.client.viscera.OriginBase` hence
    the only other objects that one object may refer to are those given in
    `objects`. It's exactly like a minimally populated `Origin`.

    If provided, `session` is used when constructing the `OriginBase`
    instance, otherwise a mock is substituted. This mock has an empty
    `handlers` mapping.

    :param objects: Any number of `Object` classes, or mappings of `Object`
        classes from the names with which they should be bound in the origin
        that's created and returned.
    :param session: A `bones.SessionAPI` instance.
    :return: An `OriginBase` instance.
    """
    def _flatten_to_items(thing):
        if isinstance(thing, Mapping):
            yield from thing.items()
        else:
            yield thing.__name__, thing

    objects = map(_flatten_to_items, objects)
    objects = chain.from_iterable(objects)
    objects = dict(objects)

    if session is None:
        session = Mock(name="session")
        session.handlers = {
            name: AsyncCallableMock(name="handler(%s)" % name)
            for name in objects
        }

    return OriginBase(session, objects=objects)
