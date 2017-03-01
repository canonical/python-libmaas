"""Utilities for the MAAS client."""

__all__ = [
    "api_url",
    "coalesce",
    "get_all_subclasses",
    "parse_docstring",
    "prepare_payload",
    "retries",
    "sign",
    "Spinner",
    "vars_class",
]

from collections import Iterable
from functools import (
    lru_cache,
    partial,
)
from inspect import (
    cleandoc,
    getdoc,
)
from itertools import (
    chain,
    cycle,
    repeat,
)
import re
import sys
import threading
from time import time
from urllib.parse import (
    quote_plus,
    urlparse,
)

from oauthlib import oauth1

from .multipart import (
    build_multipart_message,
    encode_multipart_message,
)


def urlencode(data):
    """A version of `urllib.urlencode` that isn't insane.

    This only cares that `data` is an iterable of iterables. Each sub-iterable
    must be of overall length 2, i.e. a name/value pair.

    Unicode strings will be encoded to UTF-8. This is what Django expects; see
    `smart_text` in the Django documentation.
    """
    def dec(string):
        if isinstance(string, bytes):
            string = string.decode("utf-8")
        return quote_plus(string)

    return "&".join(
        "%s=%s" % (dec(name), dec(value))
        for name, value in data)


def prepare_payload(op, method, uri, data):
    """Return the URI (modified perhaps) and body and headers.

    - For GET requests, encode parameters in the query string.

    - Otherwise always encode parameters in the request body.

    - Except op; this can always go in the query string.

    :param method: The HTTP method.
    :param uri: The URI of the action.
    :param data: An iterable of ``name, value`` or ``name, opener``
        tuples (see `name_value_pair`) to pack into the body or
        query, depending on the type of request.
    """
    query = [] if op is None else [("op", op)]

    def slurp(opener):
        with opener() as fd:
            return fd.read()

    if method == "GET":
        headers, body = [], None
        query.extend(
            (name, slurp(value) if callable(value) else value)
            for name, value in data)
    else:
        # Even if data is empty, construct a multipart request body. Piston
        # (server-side) sets `request.data` to `None` if there's no payload.
        message = build_multipart_message(data)
        headers, body = encode_multipart_message(message)

    uri = urlparse(uri)._replace(query=urlencode(query)).geturl()
    return uri, body, headers


class OAuthSigner:
    """Helper class to OAuth-sign an HTTP request."""

    def __init__(
            self, token_key, token_secret, consumer_key, consumer_secret,
            realm="OAuth"):
        """Initialize a ``OAuthAuthorizer``.

        :type token_key: Unicode string.
        :type token_secret: Unicode string.
        :type consumer_key: Unicode string.
        :type consumer_secret: Unicode string.

        :param realm: Optional.
        """
        def _to_unicode(string):
            if isinstance(string, bytes):
                return string.decode("ascii")
            else:
                return string

        self.token_key = _to_unicode(token_key)
        self.token_secret = _to_unicode(token_secret)
        self.consumer_key = _to_unicode(consumer_key)
        self.consumer_secret = _to_unicode(consumer_secret)
        self.realm = _to_unicode(realm)

    def sign_request(self, url, method, body, headers):
        """Sign a request.

        :param url: The URL to which the request is to be sent.
        :param headers: The headers in the request. These will be updated with
            the signature.
        """
        # The use of PLAINTEXT here was copied from MAAS, but we should switch
        # to HMAC once it works server-side.
        client = oauth1.Client(
            self.consumer_key, self.consumer_secret, self.token_key,
            self.token_secret, signature_method=oauth1.SIGNATURE_PLAINTEXT,
            realm=self.realm)
        # To preserve API backward compatibility convert an empty string body
        # to `None`. The old "oauth" library would treat the empty string as
        # "no body", but "oauthlib" requires `None`.
        body = None if body is None or len(body) == 0 else body
        uri, signed_headers, body = client.sign(url, method, body, headers)
        headers.update(signed_headers)


def sign(uri, headers, credentials):
    """Sign the URI and headers.

    A request method of `GET` with no body content is assumed.

    :param credentials: A tuple of consumer key, token key, and token secret.
    """
    consumer_key, token_key, token_secret = credentials
    auth = OAuthSigner(token_key, token_secret, consumer_key, "")
    auth.sign_request(uri, method="GET", body=None, headers=headers)


re_paragraph_splitter = re.compile(
    r"(?:\r\n){2,}|\r{2,}|\n{2,}", re.MULTILINE)

paragraph_split = re_paragraph_splitter.split
docstring_split = partial(paragraph_split, maxsplit=1)
remove_line_breaks = lambda string: (
    " ".join(line.strip() for line in string.splitlines()))

newline = "\n"
empty = ""


@lru_cache(2**10)
def parse_docstring(thing):
    """Parse a Python docstring, or the docstring found on `thing`.

    :return: a ``(title, body)`` tuple. As per docstring convention, title is
        the docstring's first paragraph and body is the rest.
    """
    assert not isinstance(thing, bytes)
    doc = cleandoc(thing) if isinstance(thing, str) else getdoc(thing)
    doc = empty if doc is None else doc
    assert not isinstance(doc, bytes)
    # Break the docstring into two parts: title and body.
    parts = docstring_split(doc)
    if len(parts) == 2:
        title, body = parts[0], parts[1]
    else:
        title, body = parts[0], empty
    # Remove line breaks from the title line.
    title = remove_line_breaks(title)
    # Normalise line-breaks on newline.
    body = body.replace("\r\n", newline).replace("\r", newline)
    return title, body


def ensure_trailing_slash(string):
    """Ensure that `string` has a trailing forward-slash."""
    return (string + "/") if not string.endswith("/") else string


def api_url(string):
    """Ensure that `string` looks like a URL to the API.

    This ensures that the API version is specified explicitly (i.e. the path
    ends with /api/{version}). If not, version 2.0 is selected. It also
    ensures that the path ends with a forward-slash.

    This is suitable for use as an argument type with argparse.
    """
    url = urlparse(string)
    url = url._replace(path=ensure_trailing_slash(url.path))
    if re.search("/api/[0-9.]+/?$", url.path) is None:
        url = url._replace(path=url.path + "api/2.0/")
    return url.geturl()


def get_all_subclasses(cls):
    """Get all subclasses of `cls`, recursively."""
    for cls in cls.__subclasses__():
        yield from get_all_subclasses(cls)
        yield cls


def vars_class(cls):
    """Return a dict of vars for the given class, including all ancestors.

    This differs from the usual behaviour of `vars` which returns attributes
    belonging to the given class and not its ancestors.
    """
    return dict(chain.from_iterable(
        vars(cls).items() for cls in reversed(cls.__mro__)))


def retries(timeout=30, intervals=1, time=time):
    """Helper for retrying something, sleeping between attempts.

    Returns a generator that yields ``(elapsed, remaining, wait)`` tuples,
    giving times in seconds. The last item, `wait`, is the suggested amount of
    time to sleep before trying again.

    :param timeout: From now, how long to keep iterating, in seconds. This can
        be specified as a number, or as an iterable. In the latter case, the
        iterator is advanced each time an interval is needed. This allows for
        back-off strategies.
    :param intervals: The sleep between each iteration, in seconds, an an
        iterable from which to obtain intervals.
    :param time: A callable that returns the current time in seconds.
    """
    start = time()
    end = start + timeout

    if isinstance(intervals, Iterable):
        intervals = iter(intervals)
    else:
        intervals = repeat(intervals)

    return gen_retries(start, end, intervals, time)


def gen_retries(start, end, intervals, time=time):
    """Helper for retrying something, sleeping between attempts.

    Yields ``(elapsed, remaining, wait)`` tuples, giving times in seconds. The
    last item, `wait`, is the suggested amount of time to sleep before trying
    again.

    This function works in concert with `retries`. It's split out so that
    `retries` can capture the correct start time rather than the time at which
    it is first iterated.

    :param start: The start time, in seconds, of this generator. This must be
        congruent with the `IReactorTime` argument passed to this generator.
    :param end: The desired end time, in seconds, of this generator. This must
        be congruent with the `IReactorTime` argument passed to this
        generator.
    :param intervals: A iterable of intervals, each in seconds, which should
        be used as hints for the `wait` value that's generated.
    :param time: A callable that returns the current time in seconds.
    """
    for interval in intervals:
        now = time()
        if now < end:
            wait = min(interval, end - now)
            yield now - start, end - now, wait
        else:
            yield now - start, end - now, 0
            break


def coalesce(*values, default=None):
    """Return the first argument that is not `None`.

    If all arguments are `None`, return `default`, which is `None` by default.

    Similar to PostgreSQL's `COALESCE` function.
    """
    for value in values:
        if value is not None:
            return value
    else:
        return default


class Spinner:
    """Display a spinner at the terminal, if it's a TTY.

    Use as a context manager.
    """

    def __init__(self, frames='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏', stream=sys.stdout):
        super(Spinner, self).__init__()
        self.frames = frames
        self.stream = stream

    def __enter__(self):
        if self.stream.isatty():
            frames = cycle(self.frames)
            stream = self.stream
            done = threading.Event()

            def run():
                # Disable cursor.
                stream.write("\033[?25l")
                stream.flush()
                try:
                    # Write out successive frames (and a backspace) every 0.1
                    # seconds until done is set.
                    while not done.wait(0.1):
                        stream.write("%s\b" % next(frames))
                        stream.flush()
                finally:
                    # Enable cursor.
                    stream.write("\033[?25h")
                    stream.flush()

            self.__done = done
            self.__thread = threading.Thread(target=run)
            self.__thread.start()

    def __exit__(self, *exc_info):
        if self.stream.isatty():
            self.__done.set()
            self.__thread.join()
