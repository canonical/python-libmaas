"""Testing framework for `maas.client`."""

__all__ = [
    "AsyncAwaitableMock",
    "AsyncCallableMock",
    "AsyncContextMock",
    "AsyncIterableMock",
    "make_bytes",
    "make_mac_address",
    "make_name",
    "make_name_without_spaces",
    "make_range",
    "make_string",
    "make_string_without_spaces",
    "pick_bool",
    "TestCase",
]

import asyncio
import doctest
from functools import partial
from itertools import (
    islice,
    repeat,
)
from pathlib import Path
import random
import string
from unittest import mock

from fixtures import TempDir
import testscenarios
from testtools import testcase
from testtools.matchers import DocTestMatches


random_letters = map(
    random.choice, repeat(string.ascii_letters + string.digits))

random_letters_with_spaces = map(
    random.choice, repeat(string.ascii_letters + string.digits + ' '))

random_octet = partial(random.randint, 0, 255)

random_octets = iter(random_octet, None)


def make_string(size=10):
    """Make a random human-readable string."""
    return "".join(islice(random_letters_with_spaces, size))


def make_string_without_spaces(size=10):
    """Make a random human-readable string WITHOUT spaces."""
    return "".join(islice(random_letters, size))


def make_name(prefix="name", sep='-', size=6):
    """Make a random name.

    :param prefix: Optional prefix. Defaults to "name".
    :param sep: Separator that will go between the prefix and the random
        portion of the name. Defaults to a dash.
    :param size: Length of the random portion of the name.
    :return: A randomized unicode string.
    """
    return prefix + sep + make_string(size)


def make_name_without_spaces(prefix="name", sep='-', size=6):
    """Make a random name WITHOUT spaces.

    :param prefix: Optional prefix. Defaults to "name".
    :param sep: Separator that will go between the prefix and the random
        portion of the name. Defaults to a dash.
    :param size: Length of the random portion of the name.
    :return: A randomized unicode string.
    """
    return prefix + sep + make_string_without_spaces(size)


def make_bytes(size=10):
    """Make a random byte string."""
    return bytes(islice(random_octets, size))


def make_mac_address(delimiter=":"):
    """Make a MAC address string with the given delimiter."""
    octets = islice(random_octets, 6)
    return delimiter.join(format(octet, "02x") for octet in octets)


def make_range(cmin=1, cmax=9):
    """Return a range of random length between `cmin` and `cmax`."""
    return range(random.randint(cmin, cmax))


def pick_bool():
    """Return either `True` or `False` at random."""
    return random.choice((True, False))


class WithScenarios(testscenarios.WithScenarios):
    """Variant of testscenarios_' that provides ``__call__``."""

    def __call__(self, result=None):
        if self._get_scenarios():
            for test in testscenarios.generate_scenarios(self):
                test.__call__(result)
        else:
            super(WithScenarios, self).__call__(result)


class TestCase(WithScenarios, testcase.TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self.loop = asyncio.new_event_loop()
        self.addCleanup(self.loop.close)
        asyncio.set_event_loop(self.loop)

    def makeDir(self):
        """Create a temporary directory.

        This creates a new temporary directory. This will be removed during
        test tear-down.

        :return: The path to the directory, as a `pathlib.Path`.
        """
        tempdir = self.useFixture(TempDir())
        return Path(tempdir.path)

    def makeFile(self, name=None, contents=None, location=None):
        """Create a file, and write data to it.

        This creates a new file `name` in `location` and fills it with
        `contents`. This file will be removed during test tear-down.

        :param name: Name for the file; optional. If omitted, a random name
            will be chosen.
        :param contents: Contents for the file; optional. If omitted, some
            arbitrary bytes will be written.
        :param location: Path to a directory; optional. If omitted, a new
            temporary directory will be created with `makeDir`.

        :return: The path to the file, as a `pathlib.Path`.
        """
        location = self.makeDir() if location is None else Path(location)
        filepath = location.joinpath(make_string() if name is None else name)
        filepath.write_bytes(make_bytes() if contents is None else contents)
        return filepath

    def assertDocTestMatches(self, expected, observed, flags=None):
        """See if `observed` matches `expected`, a doctest sample.

        By default uses the doctest flags `NORMALIZE_WHITESPACE` and
        `ELLIPSIS`.
        """
        if flags is None:
            flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
        self.assertThat(observed, DocTestMatches(expected, flags))

    def patch(self, obj, attribute, value=mock.sentinel.unset):
        """Patch `obj.attribute` with `value`.

        If `value` is unspecified, a new `MagicMock` will be created and
        patched-in instead. Its ``__name__`` attribute will be set to
        `attribute` or the ``__name__`` of the replaced object if `attribute`
        is not given.

        This is a thin customisation of `testtools.TestCase.patch`, so refer
        to that in case of doubt.

        :return: The patched-in object.
        """
        if isinstance(attribute, bytes):
            attribute = attribute.decode("ascii")
        if value is mock.sentinel.unset:
            value = mock.MagicMock(__name__=attribute)
        super(TestCase, self).patch(obj, attribute, value)
        return value


class AsyncAwaitableMock(mock.Mock):
    """Mock that is "future-like"; see PEP-492.

    The new `await` syntax chokes on arguments that are not future-like, i.e.
    have an `__await__` call, so we have to fool it.

    This passes calls to `__await__` through to `__call__`.
    """

    async def __await__(_mock_self, *args, **kwargs):
        return _mock_self(*args, **kwargs)


class AsyncCallableMock(mock.Mock):
    """Mock which ensures calls are "future-like"; see PEP-492.

    As in, calls to this mock return `return_value` or `side_effect` as usual,
    but these are awaitable, or native coroutines.
    """

    async def __call__(_mock_self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


class AsyncContextMock(mock.Mock):
    """Mock that acts as an async context manager; see PEP-492.

    It's not enough to mock `__aenter__` and `__aexit__` because Python
    obtains these callable attributes from the context manager's *type*. See
    https://www.python.org/dev/peps/pep-0492/#new-syntax. This is consistent
    with how non-asynchronous context managers work, but it's counterintuitive
    nonetheless.

    This returns itself from `__aenter__` and `None` from `__aexit__`.
    """

    async def __aenter__(_mock_self):
        return _mock_self

    async def __aexit__(_mock_self, *exc_info):
        return None


class AsyncIterableMock(mock.Mock):
    """Mock that can be asynchronously iterated; see PEP-492.

    This returns itself from `__aiter__` and passes through calls to
    `__anext__` to `__call__`.
    """

    def __aiter__(_mock_self):
        return _mock_self

    async def __anext__(_mock_self):
        return _mock_self()
