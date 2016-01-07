# Copyright 2015 Alburnum Ltd. This software is licensed under
# the GNU Affero General Public License version 3 (see LICENSE).

"""Interact with a remote MAAS (https://maas.ubuntu.com/).

These are highish-level bindings that provide user-oriented objects to
interact with. They're intended for developers, for folk comfortable working
with Python. They're not a front-end. Hence the name "viscera"; the classes
and functions here are the meat and organs around the "bones", but not the
"flesh".

"""

__all__ = [
    "Object",
    "ObjectField",
    "ObjectMethod",
    "Origin",
    "OriginBase",
]

from types import MethodType


class Object:
    """An object in a MAAS installation.

    * Objects have data attributes. If the handler supports it, these can be
      updated.

    * Objects may have operations.

    """

    def __init__(self, data):
        super(Object, self).__init__()
        assert isinstance(data, dict)
        self._data = data

    def __str__(self):
        return self.__class__.__qualname__

    def __repr__(self):
        data = sorted(self._data.items())
        desc = " ".join("%s=%r" % (name, value) for name, value in data)
        if len(desc) == 0:
            return "<%s>" % (self.__class__.__name__, )
        else:
            return "<%s %s>" % (self.__class__.__name__, desc)


class ObjectField:

    unset = object()

    def __init__(self, name, *, default=unset):
        super(ObjectField, self).__init__()
        self.name = name
        self.default = default

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            if self.name in instance._data:
                return instance._data[self.name]
            elif self.default is self.unset:
                raise AttributeError(
                    "%s has no attribute '%s'" % (instance, self.name))
            else:
                return self.default

    def __set__(self, instance, value):
        instance._data[self.name] = value

    def __delete__(self, instance):
        if self.name in instance._data:
            if self.default is self.unset:
                del instance._data[self.name]
            else:
                instance._data[self.name] = self.default
        else:
            if self.default is self.unset:
                pass  # Nothing to do.
            else:
                instance._data[self.name] = self.default


class ObjectMethod:

    def __init__(self, for_class=None, for_instance=None):
        super(ObjectMethod, self).__init__()
        self.for_class = for_class
        self.for_instance = for_instance

    def __get__(self, instance, owner):
        if instance is None:
            if self.for_class is None:
                raise AttributeError(
                    "%s has no matching class attribute" % (instance, ))
            else:
                return MethodType(self.for_class, owner)
        else:
            if self.for_instance is None:
                raise AttributeError(
                    "%s has no matching instance attribute" % (instance, ))
            else:
                return MethodType(self.for_instance, instance)


class OriginBase:
    """Represents an originating remote MAAS installation."""

    def __init__(self, session, *, objects=None):
        """
        :param session: A `bones.SessionAPI` instance.
        """
        super(OriginBase, self).__init__()
        self.__session = session
        self.__objects = {} if objects is None else objects
        self.__populate()

    def __populate(self):
        for name, handler in self.__session.handlers:
            base = self.__objects.get(name, Object)
            assert issubclass(base, Object)
            # Make default methods for actions that are not handled.
            attrs = {
                name: self.__method(action)
                for name, action in handler.actions
                if not hasattr(base, name)
            }
            # Put the _origin and _handler in the class's attributes.
            attrs["_origin"] = self
            attrs["_handler"] = handler
            # Set the module to something informative.
            attrs["__module__"] = "origin"
            # Construct a new class derived from base, in effect "binding" it
            # to this origin.
            obj = type(name, (base,), attrs)
            # Those objects without a custom class are "hidden" by prefixing
            # their name with an underscore.
            objname = "_%s" % name if base is Object else name
            setattr(self, objname, obj)

    def __method(self, action):
        """Construct a method for a given action.

        :param action: An instance of `ActionAPI`.
        """
        def pretty(func):
            func.__module__ = action.handler.uri
            func.__name__ = action.name
            func.__qualname__ = action.name
            func.__doc__ = action.__doc__
            return func

        if action.name in ("create", "read"):

            def for_class(cls, **params):
                data = action(**params)
                return cls(data)

            method = ObjectMethod(pretty(for_class), None)

        elif action.name == "update":

            def for_instance(self):
                self._data = action(**self._data)

            method = ObjectMethod(None, pretty(for_instance))

        elif action.name == "delete":

            def for_class(cls, **params):
                action(**params)
                return None

            def for_instance(self):
                action(**{
                    name: self._data[name]
                    for name in action.handler.params
                })
                return None

            method = ObjectMethod(
                pretty(for_class), pretty(for_instance))

        else:

            def for_class(cls, **params):
                data = action(**params)
                return data

            def for_instance(self):
                data = action(**{
                    name: self._data[name]
                    for name in action.handler.params
                })
                return data

            method = ObjectMethod(
                pretty(for_class), pretty(for_instance))

        return method


class Tags(Object):
    """The set of tags."""

    @classmethod
    def list(cls):
        return [cls._origin.Tag(data) for data in cls._handler.list()]


class Tag(Object):
    """A tag."""

    name = ObjectField("name")
    comment = ObjectField("comment", default="")
    definition = ObjectField("definition", default="")
    kernel_opts = ObjectField("kernel_opts", default=None)


class FilesType(type):

    def __iter__(cls):
        for data in cls._handler.list():
            yield cls._origin.File(data)


class Files(Object, metaclass=FilesType):
    """The set of files stored in MAAS."""

    @classmethod
    def list(cls):
        return [cls._origin.File(data) for data in cls._handler.list()]


class File(Object):
    """A file stored in MAAS."""


objects = {
    "File": File,
    "Files": Files,
    "Tag": Tag,
    "Tags": Tags,
}


class Origin(OriginBase):
    """Represents an originating remote MAAS installation."""

    def __init__(self, session):
        """
        :param session: A `bones.SessionAPI` instance.
        """
        super(Origin, self).__init__(session, objects=objects)
