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

    def __repr__(self):
        title, body = self.doc
        return "<%s %r %s>" % (
            self.__class__.__name__,
            title.rstrip("."), self.hash,
        )


class Resources:
    """Pincushion of API resources."""

    def __init__(self, anonymous, resources):
        super(Resources, self).__init__()
        for resource in resources:
            name = derive_resource_name(resource["name"])
            resource = Resource(name, anonymous, resource)
            attrname = "%s_" % name if iskeyword(name) else name
            setattr(self, attrname, resource)


class Resource:
    """An API resource, like `Machines`."""

    def __init__(self, name, anonymous, data):
        super(Resource, self).__init__()
        self._name = name
        self._anonymous = anonymous
        self._data = data
        self._populate()

    def _populate(self):
        for action in self._data["actions"]:
            name = action["name"]
            name = "%s_" % name if iskeyword(name) else name
            setattr(self, name, Action(self, action))

    def __repr__(self):
        doc = self._data["doc"]
        title, body = parse_docstring(doc)
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
    def is_anonymous(self):
        return self._resource._anonymous

    @property
    def params(self):
        return frozenset(self._resource._data["params"])

    @property
    def path(self):
        return self._resource._data["path"]

    @property
    def uri(self):
        return self._resource._data["uri"]

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

    # Other.

    def __repr__(self):
        title, body = self.doc
        return "<%s:%s.%s %r %s %s%s>" % (
            self.__class__.__name__, self._resource._name,
            self.name, title.rstrip("."), self.method, self.path,
            ("" if self.op is None else "?op=" + self.op)
        )
