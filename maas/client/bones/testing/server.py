"""Testing server."""

__all__ = [
    "ApplicationBuilder",
]

from collections import defaultdict
from functools import partial
import json
from operator import attrgetter
import re
from urllib.parse import urlparse

from aiohttp.multipart import (
    CONTENT_DISPOSITION,
    parse_content_disposition,
)
import aiohttp.web
from multidict import MultiDict

from . import desc


class ApplicationBuilder:

    def __init__(self, description):
        super(ApplicationBuilder, self).__init__()
        self._description = desc.Description(description)
        self._application = aiohttp.web.Application()
        self._basepath, self._version = self._discover_version_and_base_path()
        self._wire_up_description()
        self._actions = {}
        self._views = {}

    def handle(self, action_name, handler=None):
        if handler is None:
            return partial(self.handle, action_name)

        action = self._resolve_action(action_name)
        view_name = self._view_name(action)
        assert view_name not in self._actions
        self._actions[view_name] = action
        handler = self._wrap_handler(handler)
        if view_name in self._views:
            view = self._views[view_name]
            view.set(action, handler)
        else:
            view = self._views[view_name] = ApplicationView()
            self._application.router.add_route("*", action.path, view)
            view.set(action, handler)

    def serve(self):
        return ApplicationRunner(
            self._application, self._basepath)

    @staticmethod
    def _wrap_handler(handler):
        """Wrap `handler` in some conveniences."""

        async def wrapper(request):
            # For convenience, read in all multipart parameters.
            assert not hasattr(request, "params")
            request.params = await _get_multipart_params(request)
            response = await handler(request, **request.match_info)
            # For convenience, assume non-Responses are meant as JSON.
            if not isinstance(response, aiohttp.web.Response):
                response = aiohttp.web.json_response(response)
            return response

        return wrapper

    @staticmethod
    def _view_name(action):
        return "%s.%s" % (action.resource["name"], action.name)

    def _discover_version_and_base_path(self):
        for resource in self._description:
            path = urlparse(resource["uri"]).path
            match = re.match("(.*/api/([0-9.]+))/", path)
            if match is not None:
                base, version = match.groups()
                return base, version
        else:
            raise ValueError(
                "Could not discover version or base path.")

    def _wire_up_description(self):
        path = "%s/describe/" % self._basepath

        def describe(request):
            description = self._render_description(
                request.url.with_path(""))
            description_json = json.dumps(
                description, indent="  ", sort_keys=True)
            return aiohttp.web.Response(
                text=description_json, content_type="application/json")

        self._application.router.add_get(path, describe)

    def _render_description(self, base):
        by_resource = defaultdict(list)
        for action in self._actions.values():
            by_resource[action.resource].append(action)

        def make_resource_skeleton():
            # The "names" set gets popped later and replaced.
            return {"anon": None, "auth": None, "names": set()}

        by_resource_name = defaultdict(make_resource_skeleton)
        for resource, actions in by_resource.items():
            res_name = resource["name"]
            res_name_raw = resource["name/raw"]
            res_desc = by_resource_name[res_name]
            res_desc["names"].add(res_name_raw)
            anon_auth = "anon" if resource["is_anonymous"] else "auth"
            assert res_desc[anon_auth] is None
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
                "name": res_name_raw,
                "params": resource["params"],
                "path": resource["path"],
                "uri": str(base) + resource["path"],
            }

        for res_desc in by_resource_name.values():
            res_names = res_desc.pop("names")
            res_desc["name"] = min(res_names, key=len)

        return {
            "doc": self._description.doc.title,
            "hash": "// not calculated //",
            "resources": list(by_resource_name.values()),
        }

    def _resolve_action(self, action_name):
        match = re.match(r"^(anon|auth):(\w+[.]\w+)$", action_name)
        if match is None:
            raise ValueError(
                "Action should be (anon|auth):Resource.action, got: %s"
                % (action_name,))
        else:
            anon_auth, resource_name = match.groups()
            resources = getattr(self._description, anon_auth)
            try:
                action = attrgetter(resource_name)(resources)
            except AttributeError:
                raise ValueError("%s not found." % resource_name)
            else:
                assert action.action_name == action_name
                return action


class ApplicationView:

    def __init__(self):
        super(ApplicationView, self).__init__()
        self.rest, self.ops = {}, {}

    @property
    def allowed_methods(self):
        allowed_methods = frozenset(self.rest)
        if len(self.ops) == 0:
            return allowed_methods
        else:
            return allowed_methods | {aiohttp.hdrs.METH_POST}

    def set(self, action, handler):
        if action.is_restful:
            self.rest[action.method] = handler
        else:
            self.ops[action.op] = handler

    async def __call__(self, request):
        if request.method == "POST":
            op = request.rel_url.query.get("op")
            if op is None:
                handler = self.rest.get(request.method)
            else:
                handler = self.ops.get(op)
        else:
            handler = self.rest.get(request.method)

        if handler is None:
            raise aiohttp.web.HTTPMethodNotAllowed(
                request.method, self.allowed_methods)
        else:
            return await handler(request)


class ApplicationRunner:

    def __init__(self, application, basepath):
        super(ApplicationRunner, self).__init__()
        self._application = application
        self._loop = application.loop
        self._basepath = basepath

    async def __aenter__(self):
        self._handler = self._application.make_handler()
        self._server = await self._loop.create_server(
            self._handler, host="0.0.0.0", port=0)
        return "http://%s:%d/%s/" % (
            *self._server.sockets[0].getsockname(),
            self._basepath.strip("/"))

    async def __aexit__(self, *exc_info):
        self._server.close()
        await self._server.wait_closed()
        await self._application.shutdown()
        await self._handler.shutdown(10.0)
        await self._application.cleanup()


async def _get_multipart_params(request):
    """Extract a mapping of parts sent in a multipart request.

    :rtype: MultiDict
    """

    def get_part_name(part):
        _, params = parse_content_disposition(
            part.headers.get(CONTENT_DISPOSITION))
        return params.get("name")

    def get_part_data(part):
        if part.filename is None:
            return part.text()
        else:
            return part.read(decode=True)

    params = MultiDict()
    async for part in await request.multipart():
        params.add(get_part_name(part), await get_part_data(part))

    return params
