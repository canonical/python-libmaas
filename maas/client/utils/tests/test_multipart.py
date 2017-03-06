"""Test multipart MIME helpers."""

from io import BytesIO
from os import urandom

from django.conf import settings
from django.core.files.uploadhandler import MemoryFileUploadHandler
from django.http.multipartparser import MultiPartParser
from django.utils.datastructures import MultiValueDict
from testtools.matchers import (
    EndsWith,
    StartsWith,
)

from ...testing import (
    make_string,
    TestCase,
)
from ..multipart import (
    encode_multipart_data,
    get_content_type,
)

# Django, sigh, needs this.
settings.configure()


ahem_django_ahem = (
    "If the mismatch appears to be because the parsed values "
    "are base64 encoded, then check you're using a >=1.4 release "
    "of Django.")


def parse_headers_and_body_with_django(headers, body):
    """Parse `headers` and `body` with Django's :class:`MultiPartParser`.

    `MultiPartParser` is a curiously ugly and RFC non-compliant concoction.

    Amongst other things, it coerces all field names, field data, and
    filenames into Unicode strings using the "replace" error strategy, so be
    warned that your data may be silently mangled.

    It also, in 1.3.1 at least, does not recognise any transfer encodings at
    *all* because its header parsing code was broken.

    I'm also fairly sure that it'll fall over on headers than span more than
    one line.

    In short, it's a piece of code that inspires little confidence, yet we
    must work with it, hence we need to round-trip test multipart handling
    with it.
    """
    handler = MemoryFileUploadHandler()
    meta = {
        "CONTENT_TYPE": headers["Content-Type"],
        "CONTENT_LENGTH": headers["Content-Length"],
    }
    parser = MultiPartParser(
        META=meta, input_data=BytesIO(body),
        upload_handlers=[handler])
    return parser.parse()


class TestMultiPart(TestCase):

    def test_get_content_type_guesses_type(self):
        guess = get_content_type('text.txt')
        self.assertEqual('text/plain', guess)
        self.assertIsInstance(guess, str)

    def test_encode_multipart_data_produces_bytes(self):
        data = {make_string(): make_string().encode('ascii')}
        files = {make_string(): BytesIO(make_string().encode('ascii'))}
        body, headers = encode_multipart_data(data, files)
        self.assertIsInstance(body, bytes)

    def test_encode_multipart_data_closes_with_closing_boundary_line(self):
        data = {'foo': make_string().encode('ascii')}
        files = {'bar': BytesIO(make_string().encode('ascii'))}
        body, headers = encode_multipart_data(data, files)
        self.assertThat(body, EndsWith(b'--'))

    def test_encode_multipart_data(self):
        # The encode_multipart_data() function should take a list of
        # parameters and files and encode them into a MIME
        # multipart/form-data suitable for posting to the MAAS server.
        params = {"op": "add", "foo": "bar\u1234"}
        random_data = urandom(32)
        files = {"baz": BytesIO(random_data)}
        body, headers = encode_multipart_data(params, files)
        self.assertEqual("%s" % len(body), headers["Content-Length"])
        self.assertThat(
            headers["Content-Type"],
            StartsWith("multipart/form-data; boundary="))
        # Round-trip through Django's multipart code.
        post, files = parse_headers_and_body_with_django(headers, body)
        self.assertEqual(
            {name: [value] for name, value in params.items()}, post,
            ahem_django_ahem)
        self.assertSetEqual({"baz"}, set(files))
        self.assertEqual(
            random_data, files["baz"].read(),
            ahem_django_ahem)

    def test_encode_multipart_data_multiple_params(self):
        # Sequences of parameters and files passed to
        # encode_multipart_data() permit use of the same name for
        # multiple parameters and/or files. See `make_payloads` to
        # understand how it processes different types of parameter
        # values.
        params_in = [
            ("one", "ABC"),
            ("one", "XYZ"),
            ("two", ["DEF", "UVW"]),
        ]
        files = [
            BytesIO(b"f1"),
            self.makeFile(contents=b"f2").open("rb"),
            self.makeFile(contents=b"f3").open("rb"),
        ]
        for fd in files:
            self.addCleanup(fd.close)
        files_in = [
            ("f-one", files[0]),
            ("f-two", files[1]),
            ("f-three", lambda: files[2]),
        ]
        body, headers = encode_multipart_data(params_in, files_in)
        self.assertEqual("%s" % len(body), headers["Content-Length"])
        self.assertThat(
            headers["Content-Type"],
            StartsWith("multipart/form-data; boundary="))
        # Round-trip through Django's multipart code.
        params_out, files_out = (
            parse_headers_and_body_with_django(headers, body))
        params_out_expected = MultiValueDict()
        params_out_expected.appendlist("one", "ABC")
        params_out_expected.appendlist("one", "XYZ")
        params_out_expected.appendlist("two", "DEF")
        params_out_expected.appendlist("two", "UVW")
        self.assertEqual(
            params_out_expected, params_out,
            ahem_django_ahem)
        files_expected = {"f-one": b"f1", "f-two": b"f2", "f-three": b"f3"}
        files_observed = {name: buf.read() for name, buf in files_out.items()}
        self.assertEqual(
            files_expected, files_observed,
            ahem_django_ahem)

    def test_encode_multipart_data_list_params(self):
        params_in = [
            ("one", ["ABC", "XYZ"]),
            ("one", "UVW"),
            ]
        body, headers = encode_multipart_data(params_in, [])
        params_out, files_out = (
            parse_headers_and_body_with_django(headers, body))
        self.assertEqual({'one': ['ABC', 'XYZ', 'UVW']}, params_out)
        self.assertSetEqual(set(), set(files_out))
