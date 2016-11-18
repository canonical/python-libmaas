"""Asynchronous helpers, for use with `asyncio`."""

__all__ = [
    "asynchronous",
    "Asynchronous",
    "is_loop_running",
]

from asyncio import get_event_loop
from functools import wraps
from inspect import (
    isawaitable,
    iscoroutinefunction,
)


def asynchronous(func):
    """Return `func` in a "smart" asynchronous-aware wrapper.

    If `func` is called within the event-loop — i.e. when it is running — this
    returns the result of `func` without alteration. However, when called from
    outside of the event-loop, and the result is awaitable, the result will be
    passed though the current event-loop's `run_until_complete` method.

    In other words, this automatically blocks when calling an asynchronous
    function from outside of the event-loop, and so makes interactive use of
    these APIs far more intuitive.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        eventloop = get_event_loop()
        result = func(*args, **kwargs)
        if not eventloop.is_running():
            while isawaitable(result):
                result = eventloop.run_until_complete(result)
        return result

    return wrapper


class Asynchronous(type):
    """Metaclass that wraps callable attributes with `asynchronous`.

    Use this to create classes instances of which work naturally when working
    with them interactively.
    """

    def __new__(cls, name, bases, attrs):
        attrs.setdefault("__slots__", ())
        attrs = {name: _maybe_wrap(value) for name, value in attrs.items()}
        return super(Asynchronous, cls).__new__(cls, name, bases, attrs)


def _maybe_wrap(attribute):
    """Helper for `Asynchronous`."""
    if iscoroutinefunction(attribute):
        return asynchronous(attribute)
    if isinstance(attribute, (classmethod, staticmethod)):
        if iscoroutinefunction(attribute.__func__):
            return attribute.__class__(asynchronous(attribute.__func__))
    return attribute


def is_loop_running():
    """Is the current event-loop running right now?

    Then we don't want to block, do we?
    """
    return get_event_loop().is_running()
