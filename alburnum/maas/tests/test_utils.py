# Copyright 2015 Alburnum Ltd. This software is licensed under
# the GNU Affero General Public License version 3 (see LICENSE).

"""Tests for `alburnum.maas.utils`."""

__all__ = []

import base64
import contextlib
from functools import partial
import os
import os.path
import sqlite3
from unittest.mock import sentinel

from alburnum.maas import utils
from alburnum.maas.testing import (
    make_name_without_spaces,
    make_string,
    TestCase,
)
from alburnum.maas.utils import (
    OAuthSigner,
    prepare_payload,
    ProfileConfig,
)
from testtools.matchers import (
    Equals,
    MatchesListwise,
)
from twisted.python.filepath import FilePath


class TestMAASOAuth(TestCase):

    def test_OAuthSigner_sign_request_adds_header(self):
        token_key = make_name_without_spaces("token-key")
        token_secret = make_name_without_spaces("token-secret")
        consumer_key = make_name_without_spaces("consumer-key")
        consumer_secret = make_name_without_spaces("consumer-secret")
        realm = make_name_without_spaces("realm")

        headers = {}
        auth = OAuthSigner(
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


class TestProfileConfig(TestCase):
    """Tests for `ProfileConfig`."""

    def test_init(self):
        database = sqlite3.connect(":memory:")
        config = ProfileConfig(database)
        with config.cursor() as cursor:
            # The profiles table has been created.
            self.assertEqual(
                cursor.execute(
                    "SELECT COUNT(*) FROM sqlite_master"
                    " WHERE type = 'table'"
                    "   AND name = 'profiles'").fetchone(),
                (1,))

    def test_profiles_pristine(self):
        # A pristine configuration has no profiles.
        database = sqlite3.connect(":memory:")
        config = ProfileConfig(database)
        self.assertSetEqual(set(), set(config))

    def test_adding_profile(self):
        database = sqlite3.connect(":memory:")
        config = ProfileConfig(database)
        config["alice"] = {"abc": 123}
        self.assertEqual({"alice"}, set(config))
        self.assertEqual({"abc": 123}, config["alice"])

    def test_replacing_profile(self):
        database = sqlite3.connect(":memory:")
        config = ProfileConfig(database)
        config["alice"] = {"abc": 123}
        config["alice"] = {"def": 456}
        self.assertEqual({"alice"}, set(config))
        self.assertEqual({"def": 456}, config["alice"])

    def test_getting_profile(self):
        database = sqlite3.connect(":memory:")
        config = ProfileConfig(database)
        config["alice"] = {"abc": 123}
        self.assertEqual({"abc": 123}, config["alice"])

    def test_getting_non_existent_profile(self):
        database = sqlite3.connect(":memory:")
        config = ProfileConfig(database)
        self.assertRaises(KeyError, lambda: config["alice"])

    def test_removing_profile(self):
        database = sqlite3.connect(":memory:")
        config = ProfileConfig(database)
        config["alice"] = {"abc": 123}
        del config["alice"]
        self.assertEqual(set(), set(config))

    def test_open_and_close(self):
        # ProfileConfig.open() returns a context manager that closes the
        # database on exit.
        config_file = os.path.join(self.make_dir(), "config")
        config = ProfileConfig.open(config_file)
        self.assertIsInstance(config, contextlib._GeneratorContextManager)
        with config as config:
            self.assertIsInstance(config, ProfileConfig)
            with config.cursor() as cursor:
                self.assertEqual(
                    (1,), cursor.execute("SELECT 1").fetchone())
        self.assertRaises(sqlite3.ProgrammingError, config.cursor)

    def test_open_permissions_new_database(self):
        # ProfileConfig.open() applies restrictive file permissions to newly
        # created configuration databases.
        config_file = os.path.join(self.make_dir(), "config")
        with ProfileConfig.open(config_file):
            perms = FilePath(config_file).getPermissions()
            self.assertEqual("rw-------", perms.shorthand())

    def test_open_permissions_existing_database(self):
        # ProfileConfig.open() leaves the file permissions of existing
        # configuration databases.
        config_file = os.path.join(self.make_dir(), "config")
        open(config_file, "wb").close()  # touch.
        os.chmod(config_file, 0o644)  # u=rw,go=r
        with ProfileConfig.open(config_file):
            perms = FilePath(config_file).getPermissions()
            self.assertEqual("rw-r--r--", perms.shorthand())


class TestPayloadPreparation(TestCase):
    """Tests for `prepare_payload`."""

    uri_base = "http://example.com/MAAS/api/1.0/"

    # Scenarios for ReSTful operations; i.e. without an "op" parameter.
    scenarios_without_op = (
        # Without data, all requests have an empty request body and no extra
        # headers.
        ("create",
         {"method": "POST", "data": [],
          "expected_uri": uri_base,
          "expected_body": None,
          "expected_headers": []}),
        ("read",
         {"method": "GET", "data": [],
          "expected_uri": uri_base,
          "expected_body": None,
          "expected_headers": []}),
        ("update",
         {"method": "PUT", "data": [],
          "expected_uri": uri_base,
          "expected_body": None,
          "expected_headers": []}),
        ("delete",
         {"method": "DELETE", "data": [],
          "expected_uri": uri_base,
          "expected_body": None,
          "expected_headers": []}),
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
          "expected_body": None,
          "expected_headers": []}),
        ("read",
         {"method": "GET", "data": [],
          "expected_uri": uri_base + "?op=something",
          "expected_body": None,
          "expected_headers": []}),
        ("update",
         {"method": "PUT", "data": [],
          "expected_uri": uri_base + "?op=something",
          "expected_body": None,
          "expected_headers": []}),
        ("delete",
         {"method": "DELETE", "data": [],
          "expected_uri": uri_base + "?op=something",
          "expected_body": None,
          "expected_headers": []}),
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
        # The payload returned is a 3-tuple of (uri, body, headers).
        payload = prepare_payload(
            op=self.op, method=self.method,
            uri=self.uri_base, data=self.data)
        expected = (
            Equals(self.expected_uri),
            Equals(self.expected_body),
            Equals(self.expected_headers),
            )
        self.assertThat(payload, MatchesListwise(expected))
        # encode_multipart_message, when called, is passed the data
        # unadulterated.
        if self.expected_body is sentinel.body:
            build_multipart.assert_called_once_with(self.data)
            encode_multipart.assert_called_once_with(sentinel.message)


class TestPayloadPreparationWithFiles(TestCase):
    """Tests for `maascli.prepare_payload` involving files."""

    def test_files_are_included(self):
        parameter = make_string()
        contents = os.urandom(5)
        filename = self.make_file(contents=contents)
        # Writing the parameter as "parameter@=filename" on the
        # command-line causes name_value_pair() to return a `name,
        # opener` tuple, where `opener` is a callable that returns an
        # open file handle.
        data = [(parameter, partial(open, filename, "rb"))]
        uri, body, headers = prepare_payload(
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

    def test_basic(self):
        self.assertEqual(
            ("Title", "Body"),
            utils.parse_docstring("Title\n\nBody"))
        self.assertEqual(
            ("A longer title", "A longer body"),
            utils.parse_docstring(
                "A longer title\n\nA longer body"))

    def test_no_body(self):
        # parse_docstring returns an empty string when there's no body.
        self.assertEqual(
            ("Title", ""),
            utils.parse_docstring("Title\n\n"))
        self.assertEqual(
            ("Title", ""),
            utils.parse_docstring("Title"))

    def test_unwrapping(self):
        # parse_docstring unwraps the title paragraph, and dedents the body
        # paragraphs.
        self.assertEqual(
            ("Title over two lines",
             "Paragraph over\ntwo lines\n\n"
             "Another paragraph\nover two lines"),
            utils.parse_docstring("""
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
            utils.parse_docstring(example))

    def test_normalises_whitespace(self):
        # parse_docstring can parse CRLF/CR/LF text, but always emits LF (\n,
        # new-line) separated text.
        self.assertEqual(
            ("long title", ""),
            utils.parse_docstring("long\r\ntitle"))
        self.assertEqual(
            ("title", "body1\n\nbody2"),
            utils.parse_docstring("title\n\nbody1\r\rbody2"))
