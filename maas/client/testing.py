"""Testing framework for `maas.client`."""

__all__ = [
    "make_file",
    "make_mac_address",
    "make_name",
    "make_name_without_spaces",
    "make_string",
    "make_string_without_spaces",
    "pick_bool",
    "randrange",
    "TestCase",
]

import doctest
from functools import partial
from itertools import (
    islice,
    repeat,
)
from os import path
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


def make_file(location, name=None, contents=None):
    """Create a file, and write data to it.

    Prefer the eponymous convenience wrapper in
    :class:`maastesting.testcase.MAASTestCase`.  It creates a temporary
    directory and arranges for its eventual cleanup.

    :param location: Directory.  Use a temporary directory for this, and
        make sure it gets cleaned up after the test!
    :param name: Optional name for the file.  If none is given, one will
        be made up.
    :param contents: Optional contents for the file.  If omitted, some
        arbitrary ASCII text will be written.
    :type contents: unicode, but containing only ASCII characters.
    :return: Path to the file.
    """
    if name is None:
        name = make_string()
    if contents is None:
        contents = make_string().encode('ascii')
    filename = path.join(location, name)
    with open(filename, 'wb') as f:
        f.write(contents)
    return filename


def make_mac_address(delimiter=":"):
    """Make a MAC address string with the given delimiter."""
    octets = islice(random_octets, 6)
    return delimiter.join(format(octet, "02x") for octet in octets)


def pick_bool():
    """Return either `True` or `False` at random."""
    return random.choice((True, False))


def randrange(cmin=1, cmax=9):
    """Yield a random number of times between `cmin` and `cmax`."""
    return range(random.randint(cmin, cmax))


class WithScenarios(testscenarios.WithScenarios):
    """Variant of testscenarios_' that provides ``__call__``."""

    def __call__(self, result=None):
        if self._get_scenarios():
            for test in testscenarios.generate_scenarios(self):
                test.__call__(result)
        else:
            super(WithScenarios, self).__call__(result)


class TestCase(WithScenarios, testcase.TestCase):

    def make_dir(self):
        """Create a temporary directory.

        This is a convenience wrapper around a fixture incantation.  That's
        the only reason why it's on the test case and not in a factory.
        """
        return self.useFixture(TempDir()).path

    def make_file(self, name=None, contents=None):
        """Create, and write to, a file.

        This is a convenience wrapper around `make_dir` and a factory
        call.  It ensures that the file is in a directory that will be
        cleaned up at the end of the test.
        """
        return make_file(self.make_dir(), name, contents)

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
