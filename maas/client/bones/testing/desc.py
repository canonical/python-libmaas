"""Abstractions around API description documents."""

__all__ = [
    "Description",
    "Action",
]

from keyword import iskeyword
from operator import itemgetter

from maas.client.bones.helpers import derive_resource_name
from maas.client.utils import parse_docstring


class Description:
    """Object-oriented interface to a MAAS API description document."""

    def __init__(self, description):
        super(Description, self).__init__()
        self._description = description
        self._populate()

    def _populate(self):
        self.anon = Resources(True, self._resources("anon"))
        self.auth = Resources(False, self._resources("auth"))

    def _resources(self, classification):
        resources = self._description["resources"]
        resources = map(itemgetter(classification), resources)
        return (rs for rs in resources if rs is not None)

    @property
    def doc(self):
        doc = self._description["doc"]
        return parse_docstring(doc)

    @property
    def hash(self):
        return self._description["hash"]

    @property
    def raw(self):
        return self._description

    def __iter__(self):
        """Iterate all resources, anonymous first."""
        yield from self.anon
        yield from self.auth

    def __repr__(self):
        title, body = self.doc
        return "<%s %r %s>" % (
            self.__class__.__name__,
            title.rstrip("."), self.hash,
        )


class Resources:
    """Pincushion of API resources."""

    def __init__(self, is_anonymous, resources):
        super(Resources, self).__init__()
        for resource in resources:
            name = derive_resource_name(resource["name"])
            resource = Resource(name, is_anonymous, resource)
            attrname = "%s_" % name if iskeyword(name) else name
            setattr(self, attrname, resource)

    def __iter__(self):
        """Iterate all resources."""
        for value in vars(self).values():
            if isinstance(value, Resource):
                yield value


class Resource:
    """An API resource, like `Machines`."""

    def __init__(self, name, is_anonymous, data):
        super(Resource, self).__init__()
        self._is_anonymous = is_anonymous
        self._name = name
        self._data = data
        self._populate()

    def _populate(self):
        for action in self._data["actions"]:
            name = action["name"]
            name = "%s_" % name if iskeyword(name) else name
            setattr(self, name, Action(self, action))
        self._properties = {
            "doc": parse_docstring(self._data["doc"]),
            "is_anonymous": self._is_anonymous,
            "name": self._name,
            "name/raw": self._data["name"],
            "params": tuple(self._data["params"]),
            "path": self._data["path"],
            "uri": self._data["uri"],
        }

    def __getitem__(self, name):
        return self._properties[name]

    def __iter__(self):
        """Iterate all actions."""
        for value in vars(self).values():
            if isinstance(value, Action):
                yield value

    def __repr__(self):
        title, body = self["doc"]
        return "<%s:%s %r>" % (
            self.__class__.__name__,
            self._name, title.rstrip("."),
        )


class Action:
    """An API action on a resource, like `Machines.allocate`."""

    def __init__(self, resource, data):
        super(Action, self).__init__()
        self._resource = resource
        self._data = data

    # Resource-specific properties.

    @property
    def resource(self):
        return self._resource

    @property
    def is_anonymous(self):
        return self._resource["is_anonymous"]

    @property
    def params(self):
        return self._resource["params"]

    @property
    def path(self):
        return self._resource["path"]

    @property
    def uri(self):
        return self._resource["uri"]

    # Action-specific properties.

    @property
    def doc(self):
        doc = self._data["doc"]
        return parse_docstring(doc)

    @property
    def method(self):
        return self._data["method"]

    @property
    def name(self):
        return self._data["name"]

    @property
    def op(self):
        return self._data["op"]

    @property
    def is_restful(self):
        return self._data["restful"]

    @property
    def action_name(self):
        anon_auth = "anon" if self.is_anonymous else "auth"
        return "%s:%s.%s" % (anon_auth, self.resource["name"], self.name)

    # Other.

    def __repr__(self):
        title, body = self.doc
        return "<%s:%s.%s %r %s %s%s>" % (
            self.__class__.__name__, self._resource._name,
            self.name, title.rstrip("."), self.method, self.path,
            ("" if self.op is None else "?op=" + self.op)
        )
