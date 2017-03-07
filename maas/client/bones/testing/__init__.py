"""Testing helpers for the Bones API."""

__all__ = [
    "api_descriptions",
    "DescriptionServer",
    "list_api_descriptions",
]

import http
import http.server
import json
from pathlib import Path
import re
import threading

import fixtures
from pkg_resources import (
    resource_filename,
    resource_listdir,
)


def list_api_descriptions():
    """List API description documents.

    They're searched for in the same directory as this file, and their name
    must match "apiXX.json" where "XX" denotes the major and minor version
    number of the API.
    """
    for filename in resource_listdir(__name__, "."):
        match = re.match("api(\d)(\d)[.]json", filename)
        if match is not None:
            version = tuple(map(int, match.groups()))
            path = resource_filename(__name__, filename)
            name = "%d.%d" % version
            yield name, version, Path(path)


def load_api_descriptions():
    """Load the API description documents found by `list_api_descriptions`."""
    for name, version, path in list_api_descriptions():
        description = path.read_text("utf-8")
        yield name, version, json.loads(description)


api_descriptions = list(load_api_descriptions())
assert len(api_descriptions) != 0


class DescriptionHandler(http.server.BaseHTTPRequestHandler):
    """An HTTP request handler that serves only API descriptions.

    The `desc` attribute ought to be specified, for example by subclassing, or
    by using the `make` class-method.

    The `content_type` attribute can be overridden to simulate a different
    Content-Type header for the description.
    """

    # Override these in subclasses.
    description = b'{"resources": []}'
    content_type = "application/json"

    @classmethod
    def make(cls, description=description):
        return type(
            "DescriptionHandler", (cls, ),
            {"description": description},
        )

    def setup(self):
        super(DescriptionHandler, self).setup()
        self.logs = []

    def log_message(self, *args):
        """By default logs go to stdout/stderr. Instead, capture them."""
        self.logs.append(args)

    def do_GET(self):
        version_match = re.match(r"/MAAS/api/([0-9.]+)/describe/$", self.path)
        if version_match is None:
            self.send_error(http.HTTPStatus.NOT_FOUND)
        else:
            self.send_response(http.HTTPStatus.OK)
            self.send_header("Content-Type", self.content_type)
            self.send_header("Content-Length", str(len(self.description)))
            self.end_headers()
            self.wfile.write(self.description)


class DescriptionServer(fixtures.Fixture):
    """Fixture to start up an HTTP server for API descriptions only.

    :ivar handler: A `DescriptionHandler` subclass.
    :ivar server: An `http.server.HTTPServer` instance.
    :ivar url: A URL that points to the API that `server` is mocking.
    """

    def __init__(self, description=DescriptionHandler.description):
        super(DescriptionServer, self).__init__()
        self.description = description

    def _setUp(self):
        self.handler = DescriptionHandler.make(self.description)
        self.server = http.server.HTTPServer(("", 0), self.handler)
        self.url = "http://%s:%d/MAAS/api/2.0/" % self.server.server_address
        threading.Thread(target=self.server.serve_forever).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
