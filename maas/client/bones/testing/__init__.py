"""Testing helpers for the Bones API."""

__all__ = [
    "api_descriptions",
    "DescriptionServer",
    "list_api_descriptions",
]

from collections import defaultdict
import http
import http.server
import json
from operator import attrgetter
from pathlib import Path
import re
import threading

import aiohttp.web
import fixtures
from pkg_resources import (
    resource_filename,
    resource_listdir,
)

from . import desc


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


class Application:

    def __init__(self, description):
        super(Application, self).__init__()
        self._description = desc.Description(description)
        self._application = aiohttp.web.Application()

    def resolve(self, action):
        match = re.match(r"^(anon|auth):(\w+[.]\w+)$", action)
        if match is None:
            raise ValueError(
                "Action should be (anon|auth):Resource.action, got: %s"
                % (action,))
        else:
            anon_auth, resource_name = match.groups()
            resources = getattr(self._description, anon_auth)
            try:
                action = attrgetter(resource_name)(resources)
            except AttributeError:
                raise ValueError("%s not found." % resource_name)
            else:
                return action

    def handle(self, action_name, handler):
        action = self.resolve(action_name)
        self._application.router.add_route(
            action.method, action.path, handler, name=action_name)

    def describe(self):
        actions = [
            self.resolve(route.name)
            for route in self._application.router.routes()
            if route.name is not None
        ]

        by_resource = defaultdict(list)
        for action in actions:
            by_resource[action.resource].append(action)

        by_resource_name = defaultdict(dict)
        for resource, actions in by_resource.items():
            res_name = resource["name"]
            res_name_raw = resource["raw-name"]
            res_desc = by_resource_name[res_name]

            if "names" in res_desc:
                res_desc["names"].add(res_name_raw)
            else:
                res_desc["names"] = {res_name_raw}

            assert res_desc.setdefault("name", res_name) == res_name
            anon_auth = "anon" if resource["is_anonymous"] else "auth"
            assert anon_auth not in res_desc
            res_desc[anon_auth] = {
                "actions": [
                    {
                        "doc": action.doc.title,  # Just the title.
                        "method": action.method,
                        "name": action.name,
                        "op": action.op,
                        "restful": action.is_restful,
                    }
                    for action in actions
                ],
                "doc": resource["doc"].title,
                "name": resource["raw-name"],
                "params": resource["params"],
                "path": resource["path"],
                "uri": resource["uri"],
            }

        for res_desc in by_resource_name.values():
            res_names = res_desc.pop("names")
            res_desc["name"] = min(res_names, key=len)

        return {
            "doc": self._description.doc.title,
            "hash": "// not calculated //",
            "resources": list(by_resource_name.values()),
        }


api20 = api_descriptions[0][1]
app = Application(api20)
app.handle("auth:Machines.allocate", print)
app.handle("auth:Machines.accept", print)
app.handle("anon:Machines.accept", print)
app.handle("anon:Version.read", print)

# print(json.dumps(app.describe(), sort_keys=True, indent="  "))


{
    'anon': None,
    'auth': {
        'actions': [
            {
                'doc': "...",
                'method': 'GET',
                'name': 'read',
                'op': None,
                'restful': True,
            },
            {
                'doc': "...",
                'method': 'POST',
                'name': 'create',
                'op': None,
                'restful': True,
            },
        ],
        'doc': 'Manage block devices on a node.',
        'name': 'BlockDevicesHandler',
        'params': ['system_id'],
        'path': '/MAAS/api/2.0/nodes/{system_id}/blockdevices/',
        'uri': 'http://srv:5240/MAAS/api/2.0/nodes/{system_id}/blockdevices/',
    },
    'name': 'BlockDevicesHandler',
}
