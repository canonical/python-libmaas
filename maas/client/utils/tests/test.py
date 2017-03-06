"""Tests for `maas.client.utils`."""

import base64
from functools import partial
from itertools import cycle
import os
import os.path
from unittest.mock import sentinel

from testtools.matchers import (
    AfterPreprocessing,
    Equals,
    Is,
    MatchesListwise,
)
from twisted.internet.task import Clock

from ... import utils
from ...testing import (
    make_name_without_spaces,
    make_string,
    TestCase,
)


class TestMAASOAuth(TestCase):

    def test_OAuthSigner_sign_request_adds_header(self):
        token_key = make_name_without_spaces("token-key")
        token_secret = make_name_without_spaces("token-secret")
        consumer_key = make_name_without_spaces("consumer-key")
        consumer_secret = make_name_without_spaces("consumer-secret")
        realm = make_name_without_spaces("realm")

        headers = {}
        auth = utils.OAuthSigner(
            token_key=token_key, token_secret=token_secret,
            consumer_key=consumer_key, consumer_secret=consumer_secret,
            realm=realm)
        auth.sign_request('http://example.com/', "GET", None, headers)

        self.assertIn('Authorization', headers)
        authorization = headers["Authorization"]
        self.assertIn('realm="%s"' % realm, authorization)
        self.assertIn('oauth_token="%s"' % token_key, authorization)
        self.assertIn('oauth_consumer_key="%s"' % consumer_key, authorization)
        self.assertIn('oauth_signature="%s%%26%s"' % (
            consumer_secret, token_secret), authorization)

    def test_sign_adds_header(self):
        token_key = make_name_without_spaces("token-key")
        token_secret = make_name_without_spaces("token-secret")
        consumer_key = make_name_without_spaces("consumer-key")

        headers = {}
        utils.sign('http://example.com/', headers, (
            consumer_key, token_key, token_secret))

        self.assertIn('Authorization', headers)
        authorization = headers["Authorization"]
        self.assertIn('realm="OAuth"', authorization)
        self.assertIn('oauth_token="%s"' % token_key, authorization)
        self.assertIn('oauth_consumer_key="%s"' % consumer_key, authorization)
        self.assertIn('oauth_signature="%%26%s"' % token_secret, authorization)


class TestPayloadPreparation(TestCase):
    """Tests for `prepare_payload`."""

    uri_base = "http://example.com/MAAS/api/2.0/"

    # Scenarios for ReSTful operations; i.e. without an "op" parameter.
    scenarios_without_op = (
        # Without data, all requests have an empty request body and no extra
        # headers.
        ("create",
         {"method": "POST", "data": [],
          "expected_uri": uri_base,
          "expected_body": sentinel.body,
          "expected_headers": sentinel.headers}),
        ("read",
         {"method": "GET", "data": [],
          "expected_uri": uri_base,
          "expected_body": None,
          "expected_headers": []}),
        ("update",
         {"method": "PUT", "data": [],
          "expected_uri": uri_base,
          "expected_body": sentinel.body,
          "expected_headers": sentinel.headers}),
        ("delete",
         {"method": "DELETE", "data": [],
          "expected_uri": uri_base,
          "expected_body": sentinel.body,
          "expected_headers": sentinel.headers}),
        # With data, PUT, POST, and DELETE requests have their body and
        # extra headers prepared by build_multipart_message and
        # encode_multipart_message. For GET requests, the data is
        # encoded into the query string, and both the request body and
        # extra headers are empty.
        ("create-with-data",
         {"method": "POST", "data": [("foo", "bar"), ("foo", "baz")],
          "expected_uri": uri_base,
          "expected_body": sentinel.body,
          "expected_headers": sentinel.headers}),
        ("read-with-data",
         {"method": "GET", "data": [("foo", "bar"), ("foo", "baz")],
          "expected_uri": uri_base + "?foo=bar&foo=baz",
          "expected_body": None,
          "expected_headers": []}),
        ("update-with-data",
         {"method": "PUT", "data": [("foo", "bar"), ("foo", "baz")],
          "expected_uri": uri_base,
          "expected_body": sentinel.body,
          "expected_headers": sentinel.headers}),
        ("delete-with-data",
         {"method": "DELETE", "data": [("foo", "bar"), ("foo", "baz")],
          "expected_uri": uri_base,
          "expected_body": sentinel.body,
          "expected_headers": sentinel.headers}),
        )

    # Scenarios for non-ReSTful operations; i.e. with an "op" parameter.
    scenarios_with_op = (
        # Without data, all requests have an empty request body and no extra
        # headers. The operation is encoded into the query string.
        ("create",
         {"method": "POST", "data": [],
          "expected_uri": uri_base + "?op=something",
          "expected_body": sentinel.body,
          "expected_headers": sentinel.headers}),
        ("read",
         {"method": "GET", "data": [],
          "expected_uri": uri_base + "?op=something",
          "expected_body": None,
          "expected_headers": []}),
        ("update",
         {"method": "PUT", "data": [],
          "expected_uri": uri_base + "?op=something",
          "expected_body": sentinel.body,
          "expected_headers": sentinel.headers}),
        ("delete",
         {"method": "DELETE", "data": [],
          "expected_uri": uri_base + "?op=something",
          "expected_body": sentinel.body,
          "expected_headers": sentinel.headers}),
        # With data, PUT, POST, and DELETE requests have their body and
        # extra headers prepared by build_multipart_message and
        # encode_multipart_message. For GET requests, the data is
        # encoded into the query string, and both the request body and
        # extra headers are empty. The operation is encoded into the
        # query string.
        ("create-with-data",
         {"method": "POST", "data": [("foo", "bar"), ("foo", "baz")],
          "expected_uri": uri_base + "?op=something",
          "expected_body": sentinel.body,
          "expected_headers": sentinel.headers}),
        ("read-with-data",
         {"method": "GET", "data": [("foo", "bar"), ("foo", "baz")],
          "expected_uri": uri_base + "?op=something&foo=bar&foo=baz",
          "expected_body": None,
          "expected_headers": []}),
        ("update-with-data",
         {"method": "PUT", "data": [("foo", "bar"), ("foo", "baz")],
          "expected_uri": uri_base + "?op=something",
          "expected_body": sentinel.body,
          "expected_headers": sentinel.headers}),
        ("delete-with-data",
         {"method": "DELETE", "data": [("foo", "bar"), ("foo", "baz")],
          "expected_uri": uri_base + "?op=something",
          "expected_body": sentinel.body,
          "expected_headers": sentinel.headers}),
        )

    scenarios_without_op = tuple(
        ("%s-without-op" % name, dict(scenario, op=None))
        for name, scenario in scenarios_without_op)

    scenarios_with_op = tuple(
        ("%s-with-op" % name, dict(scenario, op="something"))
        for name, scenario in scenarios_with_op)

    scenarios = scenarios_without_op + scenarios_with_op

    def test_prepare_payload(self):
        # Patch build_multipart_message and encode_multipart_message to
        # match the scenarios.
        build_multipart = self.patch(utils, "build_multipart_message")
        build_multipart.return_value = sentinel.message
        encode_multipart = self.patch(utils, "encode_multipart_message")
        encode_multipart.return_value = sentinel.headers, sentinel.body
        # The payload returned is a 3-tuple of (uri, body, headers). Pass
        # `data` as an iterator to ensure that it works with non-sized types.
        payload = utils.prepare_payload(
            op=self.op, method=self.method,
            uri=self.uri_base, data=iter(self.data))
        expected = (
            Equals(self.expected_uri),
            Equals(self.expected_body),
            Equals(self.expected_headers),
            )
        self.assertThat(payload, MatchesListwise(expected))
        # encode_multipart_message, when called, is passed the data
        # unadulterated.
        if self.expected_body is sentinel.body:
            encode_multipart.assert_called_once_with(sentinel.message)


class TestPayloadPreparationWithFiles(TestCase):
    """Tests for `prepare_payload` involving files."""

    def test_files_are_included(self):
        parameter = make_string()
        contents = os.urandom(5)
        filepath = self.makeFile(contents=contents)
        # Writing the parameter as "parameter@=filename" on the
        # command-line causes name_value_pair() to return a `name,
        # opener` tuple, where `opener` is a callable that returns an
        # open file handle.
        data = [(parameter, partial(filepath.open, "rb"))]
        uri, body, headers = utils.prepare_payload(
            op=None, method="POST", uri="http://localhost", data=data)

        expected_body_template = """\
            --...
            Content-Transfer-Encoding: base64
            Content-Disposition: form-data; ...name="%s"; ...name="%s"
            MIME-Version: 1.0
            Content-Type: application/octet-stream

            %s
            --...--
            """
        expected_body = expected_body_template % (
            parameter, parameter, base64.b64encode(contents).decode("ascii"))

        self.assertDocTestMatches(expected_body, body.decode("ascii"))


class TestDocstringParsing(TestCase):
    """Tests for docstring parsing with `parse_docstring`."""

    scenarios = (
        ("normal", dict(parse=utils.parse_docstring)),
    )

    def test_basic(self):
        self.assertEqual(
            ("Title", "Body"),
            self.parse("Title\n\nBody"))
        self.assertEqual(
            ("A longer title", "A longer body"),
            self.parse("A longer title\n\nA longer body"))

    def test_no_body(self):
        # parse_docstring returns an empty string when there's no body.
        self.assertEqual(
            ("Title", ""),
            self.parse("Title\n\n"))
        self.assertEqual(
            ("Title", ""),
            self.parse("Title"))

    def test_unwrapping(self):
        # parse_docstring unwraps the title paragraph, and dedents the body
        # paragraphs.
        self.assertEqual(
            ("Title over two lines",
             "Paragraph over\ntwo lines\n\n"
             "Another paragraph\nover two lines"),
            self.parse("""
                Title over
                two lines

                Paragraph over
                two lines

                Another paragraph
                over two lines
                """))

    def test_gets_docstring_from_function(self):
        # parse_docstring can extract the docstring when the argument passed
        # is not a string type.
        def example():
            """Title.

            Body.
            """
        self.assertEqual(
            ("Title.", "Body."),
            self.parse(example))

    def test_normalises_whitespace(self):
        # parse_docstring can parse CRLF/CR/LF text, but always emits LF (\n,
        # new-line) separated text.
        self.assertEqual(
            ("long title", ""),
            self.parse("long\r\ntitle"))
        self.assertEqual(
            ("title", "body1\n\nbody2"),
            self.parse("title\n\nbody1\r\rbody2"))


class TestFunctions(TestCase):
    """Tests for miscellaneous functions in `maas.client.utils`."""

    def test_api_url(self):
        transformations = list({
            "http://example.com/": "http://example.com/api/2.0/",
            "http://example.com/foo": "http://example.com/foo/api/2.0/",
            "http://example.com/foo/": "http://example.com/foo/api/2.0/",
            "http://example.com/api/7.9": "http://example.com/api/7.9/",
            "http://example.com/api/7.9/": "http://example.com/api/7.9/",
            }.items())
        urls = [url for url, url_out in transformations]
        urls_out = [url_out for url, url_out in transformations]
        expected = [
            AfterPreprocessing(utils.api_url, Equals(url_out))
            for url_out in urls_out
            ]
        self.assertThat(urls, MatchesListwise(expected))

    def test_coalesce(self):
        self.assertThat(utils.coalesce("abc"), Equals("abc"))
        self.assertThat(utils.coalesce(None, "abc"), Equals("abc"))
        self.assertThat(utils.coalesce("abc", None), Equals("abc"))
        self.assertThat(utils.coalesce("abc", "def"), Equals("abc"))
        self.assertThat(utils.coalesce(default="foo"), Equals("foo"))
        self.assertThat(utils.coalesce(None, default="foo"), Equals("foo"))
        self.assertThat(utils.coalesce(), Is(None))


class TestRetries(TestCase):

    def assertRetry(
            self, clock, observed, expected_elapsed, expected_remaining,
            expected_wait):
        """Assert that the retry tuple matches the given expectations.

        Retry tuples are those returned by `retries`.
        """
        self.assertThat(observed, MatchesListwise([
            Equals(expected_elapsed),  # elapsed
            Equals(expected_remaining),  # remaining
            Equals(expected_wait),  # wait
        ]))

    def test_yields_elapsed_remaining_and_wait(self):
        # Take control of time.
        clock = Clock()

        gen_retries = utils.retries(5, 2, time=clock.seconds)
        # No time has passed, 5 seconds remain, and it suggests sleeping
        # for 2 seconds.
        self.assertRetry(clock, next(gen_retries), 0, 5, 2)
        # Mimic sleeping for the suggested sleep time.
        clock.advance(2)
        # Now 2 seconds have passed, 3 seconds remain, and it suggests
        # sleeping for 2 more seconds.
        self.assertRetry(clock, next(gen_retries), 2, 3, 2)
        # Mimic sleeping for the suggested sleep time.
        clock.advance(2)
        # Now 4 seconds have passed, 1 second remains, and it suggests
        # sleeping for just 1 more second.
        self.assertRetry(clock, next(gen_retries), 4, 1, 1)
        # Mimic sleeping for the suggested sleep time.
        clock.advance(1)
        # There's always a final chance to try something.
        self.assertRetry(clock, next(gen_retries), 5, 0, 0)
        # All done.
        self.assertRaises(StopIteration, next, gen_retries)

    def test_calculates_times_with_reference_to_current_time(self):
        # Take control of time.
        clock = Clock()

        gen_retries = utils.retries(5, 2, time=clock.seconds)
        # No time has passed, 5 seconds remain, and it suggests sleeping
        # for 2 seconds.
        self.assertRetry(clock, next(gen_retries), 0, 5, 2)
        # Mimic sleeping for 4 seconds, more than the suggested.
        clock.advance(4)
        # Now 4 seconds have passed, 1 second remains, and it suggests
        # sleeping for just 1 more second.
        self.assertRetry(clock, next(gen_retries), 4, 1, 1)
        # Don't sleep, ask again immediately, and the same answer is given.
        self.assertRetry(clock, next(gen_retries), 4, 1, 1)
        # Mimic sleeping for 100 seconds, much more than the suggested.
        clock.advance(100)
        # There's always a final chance to try something, but the elapsed and
        # remaining figures are still calculated with reference to the current
        # time. The wait time never goes below zero.
        self.assertRetry(clock, next(gen_retries), 104, -99, 0)
        # All done.
        self.assertRaises(StopIteration, next, gen_retries)

    def test_captures_start_time_when_called(self):
        # Take control of time.
        clock = Clock()

        gen_retries = utils.retries(5, 2, time=clock.seconds)
        clock.advance(4)
        # 4 seconds have passed, so 1 second remains, and it suggests sleeping
        # for 1 second.
        self.assertRetry(clock, next(gen_retries), 4, 1, 1)

    def test_intervals_can_be_an_iterable(self):
        # Take control of time.
        clock = Clock()
        # Use intervals of 1s, 2s, 3, and then back to 1s.
        intervals = cycle((1.0, 2.0, 3.0))

        gen_retries = utils.retries(5, intervals, time=clock.seconds)
        # No time has passed, 5 seconds remain, and it suggests sleeping
        # for 1 second, then 2, then 3, then 1 again.
        self.assertRetry(clock, next(gen_retries), 0, 5, 1)
        self.assertRetry(clock, next(gen_retries), 0, 5, 2)
        self.assertRetry(clock, next(gen_retries), 0, 5, 3)
        self.assertRetry(clock, next(gen_retries), 0, 5, 1)
        # Mimic sleeping for 3.5 seconds, more than the suggested.
        clock.advance(3.5)
        # Now 3.5 seconds have passed, 1.5 seconds remain, and it suggests
        # sleeping for 1.5 seconds, 0.5 less than the next expected interval
        # of 2.0 seconds.
        self.assertRetry(clock, next(gen_retries), 3.5, 1.5, 1.5)
        # Don't sleep, ask again immediately, and the same answer is given.
        self.assertRetry(clock, next(gen_retries), 3.5, 1.5, 1.5)
        # Don't sleep, ask again immediately, and 1.0 seconds is given,
        # because we're back to the 1.0 second interval.
        self.assertRetry(clock, next(gen_retries), 3.5, 1.5, 1.0)
        # Mimic sleeping for 100 seconds, much more than the suggested.
        clock.advance(100)
        # There's always a final chance to try something, but the elapsed and
        # remaining figures are still calculated with reference to the current
        # time. The wait time never goes below zero.
        self.assertRetry(clock, next(gen_retries), 103.5, -98.5, 0.0)
        # All done.
        self.assertRaises(StopIteration, next, gen_retries)
