"""Interact with a remote MAAS (https://maas.ubuntu.com/).

These are low-level bindings that closely mirror the shape of MAAS's Web API,
hence the name "bones".
"""

__all__ = [
    "CallError",
    "SessionAPI",
]

from collections import (
    Iterable,
    namedtuple,
)
import json
import re

import aiohttp
import aiohttp.errors

from . import helpers
from .. import utils
from ..utils import profiles


class SessionError(Exception):
    """Miscellaneous session-related error."""


class SessionAPI:
    """Represents an API session with a remote MAAS installation."""

    @classmethod
    async def fromURL(
            cls, url, *, credentials=None, insecure=False):
        """Return a `SessionAPI` for a given MAAS instance."""
        try:
            description = await helpers.fetch_api_description(
                url, credentials=credentials, insecure=insecure)
        except helpers.RemoteError as error:
            # For now just re-raise as SessionError.
            raise SessionError(str(error))
        else:
            session = cls(description, credentials)
            session.insecure = insecure
            return session

    @classmethod
    def fromProfile(cls, profile):
        """Return a `SessionAPI` from a given configuration profile.

        :see: `ProfileStore`.
        """
        return cls(profile.description, profile.credentials)

    @classmethod
    def fromProfileName(cls, name):
        """Return a `SessionAPI` from a given configuration profile name.

        :see: `ProfileStore`.
        """
        with profiles.ProfileStore.open() as config:
            return cls.fromProfile(config.load(name))

    @classmethod
    async def login(
            cls, url, *, username=None, password=None, insecure=False):
        """Make a `SessionAPI` by logging-in with a username and password.

        :return: A tuple of ``profile`` and ``session``, where the former is
            an unsaved `Profile` instance, and the latter is a `SessionAPI`
            instance made using the profile.
        """
        profile = await helpers.login(
            url=url, username=username, password=password, insecure=insecure)
        session = cls(profile.description, profile.credentials)
        session.insecure = insecure
        return profile, session

    @classmethod
    async def connect(
            cls, url, *, apikey=None, insecure=False):
        """Make a `SessionAPI` by connecting with an apikey.

        :return: A tuple of ``profile`` and ``session``, where the former is
            an unsaved `Profile` instance, and the latter is a `SessionAPI`
            instance made using the profile.
        """
        profile = await helpers.connect(
            url=url, apikey=apikey, insecure=insecure)
        session = cls(profile.description, profile.credentials)
        session.insecure = insecure
        return profile, session

    # Set these on instances.
    insecure = False
    debug = False

    def __init__(self, description, credentials=None):
        """Construct a `SessionAPI`.

        :param description: The description of the remote API. See `fromURL`.
        :param credentials: Credentials for the remote system. Optional.
        """
        super(SessionAPI, self).__init__()
        self.__description = description
        self.__credentials = credentials
        self.__populate()

    def __populate(self):
        resources = self.__description["resources"]
        if self.__credentials is None:
            for resource in resources:
                if resource["anon"] is not None:
                    handler = HandlerAPI(resource["anon"], resource, self)
                    setattr(self, handler.name, handler)
        else:
            for resource in resources:
                if resource["auth"] is not None:
                    handler = HandlerAPI(resource["auth"], resource, self)
                    setattr(self, handler.name, handler)
                elif resource["anon"] is not None:
                    handler = HandlerAPI(resource["anon"], resource, self)
                    setattr(self, handler.name, handler)

    @property
    def is_anonymous(self):
        return self.__credentials is None

    @property
    def credentials(self):
        return self.__credentials

    @property
    def description(self):
        return self.__description

    @property
    def handlers(self):
        for name, value in vars(self).items():
            if not name.startswith("_") and isinstance(value, HandlerAPI):
                yield name, value


class HandlerAPI:
    """Represents remote objects and operations, and collections thereof.

    For example, this may represent the set of all nodes and the
    operations/actions available for that set, or a single node and relevant
    operations.
    """

    def __init__(self, handler, resource, session):
        """Construct a `HandlerAPI`.

        :param handler: The handler description from the overall API
            description document. See `SessionAPI`.
        :param resource: The parent of `handler` in the API description
            document. XXX: This does not appear to be needed.
        :param session: The `SessionAPI`.
        """
        super(HandlerAPI, self).__init__()
        self.__handler = handler
        self.__resource = resource
        self.__session = session
        self.__populate()

    def __populate(self):
        self.__doc__ = self.__handler["doc"]
        actions = self.__handler["actions"]
        for action in actions:
            setattr(self, action["name"], ActionAPI(action, self))

    @property
    def name(self):
        """A stable, human-readable name and identifier for this handler."""
        name = self.__handler["name"]
        if name.startswith("Anon"):
            name = name[4:]
        if name.endswith("Handler"):
            name = name[:-7]
        return re.sub('maas', 'MAAS', name, flags=re.IGNORECASE)

    @property
    def uri(self):
        """The URI for this handler.

        This will typically contain replacement patterns; these are
        interpolated in `CallAPI`.
        """
        return self.__handler["uri"]

    @property
    def params(self):
        """The set of parameters that this handler requires.

        These are the names required for interpolation into the URI.
        """
        return frozenset(self.__handler["params"])

    @property
    def path(self):
        """The path component of the URI."""
        return self.__handler["path"]

    @property
    def session(self):
        """The parent `SessionAPI`."""
        return self.__session

    @property
    def actions(self):
        return [
            (name, value) for name, value in vars(self).items()
            if not name.startswith("_") and isinstance(value, ActionAPI)
        ]

    def __repr__(self):
        return "<Handler %s %s>" % (self.name, self.uri)


class ActionAPI:
    """Represents a single action.

    This roughly corresponds to an HTTP verb plus a URI. Here you can bind
    parameters into the URI, as well as get information about the nature of
    the action.
    """

    def __init__(self, action, handler):
        """Construct a `ActionAPI`.

        :param action: The action description from the overall API description
            document. See `SessionAPI`.
        :param handler: The `HandlerAPI`.
        """
        super(ActionAPI, self).__init__()
        self.__action = action
        self.__handler = handler
        self.__doc__ = self.__action["doc"]

    @property
    def name(self):
        """The name of this action."""
        return self.__action["name"]

    @property
    def fullname(self):
        """The qualified name of this action, including the handler's name."""
        return "%s.%s" % (self.__handler.name, self.name)

    @property
    def op(self):
        """The name of the underlying operation, if set."""
        return self.__action["op"]

    @property
    def is_restful(self):
        """Indicates if this action is ReSTful.

        In other words, this is a CRUD operation: create, read, update, or
        delete.
        """
        return self.__action["restful"]

    @property
    def method(self):
        """The HTTP method."""
        return self.__action["method"]

    @property
    def handler(self):
        """The `HandlerAPI`."""
        return self.__handler

    def bind(self, **params):
        """Bind URI parameters.

        :return: A `CallAPI` instance.
        """
        return CallAPI(params, self)

    async def __call__(self, **data):
        """Convenience method to do ``this.bind(**params).call(**data).data``.

        The ``params`` are extracted from the given keyword arguments.
        Whatever remains is assumed to be data to be passed to ``call()`` as
        keyword arguments.

        :raise KeyError: If not all required arguments are provided.

        See `CallAPI.call()` for return information and exceptions.
        """
        params = {name: data.pop(name) for name in self.handler.params}
        response = await self.bind(**params).call(**data)
        return response.data

    def __repr__(self):
        if self.op is None:
            return "<Action %s %s %s>" % (
                self.fullname, self.method, self.handler.uri)
        else:
            return "<Action %s %s %s op=%s>" % (
                self.fullname, self.method, self.handler.uri, self.op)


CallResult = namedtuple("CallResult", ("response", "content", "data"))


class CallError(Exception):

    def __init__(self, request, response, content, call):
        desc_for_request = "%(method)s %(uri)s" % request
        desc_for_response = "HTTP %s %s" % (response.status, response.reason)
        desc_for_content = content.decode("utf-8", "replace")
        desc = "%s -> %s (%s)" % (
            desc_for_request, desc_for_response,
            desc_for_content if len(desc_for_content) <= 50 else (
                desc_for_content[:49] + "…"))
        super(CallError, self).__init__(desc)
        self.request = request
        self.response = response
        self.content = content
        self.call = call

    @property
    def status(self):
        return self.response.status


class CallAPI:

    def __init__(self, params, action):
        """Create a new `CallAPI`.

        :param params: Parameters to be interpolated into the action's URI.
        :param action: The `ActionAPI`.
        """
        super(CallAPI, self).__init__()
        self.__params = params
        self.__action = action
        self.__validate()

    def __validate(self):
        params_expected = self.action.handler.params
        params_observed = frozenset(self.__params)
        if params_observed != params_expected:
            if len(params_expected) == 0:
                raise TypeError("%s takes no arguments" % self.action.fullname)
            else:
                params_expected_desc = ", ".join(sorted(params_expected))
                raise TypeError("%s takes %d arguments: %s" % (
                    self.action.fullname, len(params_expected),
                    params_expected_desc))

    @property
    def action(self):
        """The `ActionAPI`."""
        return self.__action

    @property
    def uri(self):
        """The URI for this handler, with parameters interpolated."""
        # TODO: this is el-cheapo URI Template
        # <http://tools.ietf.org/html/rfc6570> support; use uritemplate-py
        # <https://github.com/uri-templates/uritemplate-py> here?
        return self.action.handler.uri.format(**self.__params)

    def rebind(self, **params):
        """Rebind the parameters into the URI.

        :return: A new `CallAPI` instance with the new parameters.
        """
        new_params = self.__params.copy()
        new_params.update(params)
        return self.__class__(new_params, self.__action)

    def call(self, **data):
        """Issue the call.

        :param data: Data to pass in the *body* of the request.
        """
        uri, body, headers = self.prepare(data)
        return self.dispatch(uri, body, headers)

    def prepare(self, data):
        """Prepare the call payload.

        This is used by `call` and can be overridden to marshal the request in
        a different way.

        :param data: Data to pass in the *body* of the request.
        :type data: dict
        """
        def expand(data):
            for name, value in data.items():
                if isinstance(value, Iterable):
                    for value in value:
                        yield name, value
                else:
                    yield name, value

        # `data` must be an iterable yielding 2-tuples.
        if self.action.method in ("GET", "DELETE"):
            # MAAS does not expect an entity-body for GET or DELETE.
            data = expand(data)
        else:
            # MAAS expects and entity-body for PUT and POST.
            data = data.items()

        # Bundle things up ready to throw over the wire.
        uri, body, headers = utils.prepare_payload(
            self.action.op, self.action.method, self.uri, data)

        # Headers are returned as a list, but they must be a dict for
        # the signing machinery.
        headers = dict(headers)

        # Sign request if credentials have been provided.
        credentials = self.action.handler.session.credentials
        if credentials is not None:
            utils.sign(uri, headers, credentials)

        return uri, body, headers

    async def dispatch(self, uri, body, headers):
        """Dispatch the call via HTTP.

        This is used by `call` and can be overridden to use a different HTTP
        library.
        """
        insecure = self.action.handler.session.insecure
        connector = aiohttp.TCPConnector(verify_ssl=(not insecure))
        session = aiohttp.ClientSession(connector=connector)
        async with session:
            response = await session.request(
                self.action.method, uri, data=body,
                headers=_prefer_json(headers))
            async with response:
                # Fetch the raw body content.
                content = await response.read()

                # Debug output.
                if self.action.handler.session.debug:
                    print(response)

                # 2xx status codes are all okay.
                if response.status // 100 != 2:
                    request = {
                        "body": body,
                        "headers": headers,
                        "method": self.action.method,
                        "uri": uri,
                    }
                    raise CallError(request, response, content, self)

                # Decode from JSON if that's what it's declared as.
                if response.content_type is None:
                    data = await response.read()
                elif response.content_type.endswith('/json'):
                    data = await response.json()
                else:
                    data = await response.read()

                if response.content_type is None:
                    data = content
                elif response.content_type.endswith('/json'):
                    # JSON should always be UTF-8.
                    data = json.loads(content.decode("utf-8"))
                else:
                    data = content

                return CallResult(response, content, data)

    def __repr__(self):
        return "<Call %s @%s>" % (self.action.fullname, self.uri)


def _prefer_json(headers):
    """Prefer JSON in HTTP requests.

    If no `Accept` header has yet been defined in `headers`, this adds one
    that makes `application/json` clearly preferred. See RFC-7159 re. this
    choice of MIME type:

      The MIME media type for JSON text is application/json.

    It also happens to be what Piston understands, which is what MAAS uses.
    """
    if not any(header.lower() == "accept" for header in headers):
        headers["Accept"] = "application/json,*/*;q=0.9"
    return headers
