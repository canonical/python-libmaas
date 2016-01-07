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
    "ObjectType",
    "ObjectTypedField",
    "Origin",
    "OriginBase",
]

from types import MethodType

from alburnum.maas.utils import (
    get_all_subclasses,
    vars_class,
)


undefined = object()


def dir_class(cls):
    """Return a list of names available on `cls`.

    Eliminates names that bind to an `ObjectMethod` without a corresponding
    class method; see `ObjectMethod`.
    """
    # Class attributes (including methods).
    for name, value in vars_class(cls).items():
        if isinstance(value, ObjectMethod):
            if value.has_classmethod:
                yield name
        else:
            yield name


def dir_instance(inst):
    """Return a list of names available on `inst`.

    Eliminates names that bind to an `ObjectMethod` without a corresponding
    instance method; see `ObjectMethod`.
    """
    # Instance attributes.
    yield from vars(inst)
    # Class attributes (including methods).
    for name, value in vars_class(type(inst)).items():
        if isinstance(value, ObjectMethod):
            if value.has_instancemethod:
                yield name
        else:
            yield name


class ObjectType(type):

    def __dir__(cls):
        return list(dir_class(cls))


class Object(metaclass=ObjectType):
    """An object in a MAAS installation."""

    def __init__(self, data):
        super(Object, self).__init__()
        assert isinstance(data, dict)
        self._data = data

    def __dir__(self):
        return list(dir_instance(self))

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

    def __init__(self, name, *, default=undefined):
        super(ObjectField, self).__init__()
        self.name = name
        self.default = default

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            if self.name in instance._data:
                return instance._data[self.name]
            elif self.default is undefined:
                raise AttributeError()
            else:
                return self.default

    def __set__(self, instance, value):
        instance._data[self.name] = value

    def __delete__(self, instance):
        if self.name in instance._data:
            del instance._data[self.name]


class ObjectTypedField(ObjectField):

    def __init__(self, name, d2v=None, v2d=None, *, default=undefined):
        super(ObjectTypedField, self).__init__(name, default=default)
        self.d2v = (lambda value: value) if d2v is None else d2v
        self.v2d = (lambda value: value) if v2d is None else v2d
        if default is not undefined:
            if self.d2v(self.v2d(default)) != default:
                raise TypeError(
                    "The default of %r cannot be round-tripped through the "
                    "conversion/validation functions given." % (default, ))

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            if self.name in instance._data:
                datum = instance._data[self.name]
                return self.d2v(datum)
            elif self.default is undefined:
                raise AttributeError()
            else:
                return self.default

    def __set__(self, instance, value):
        datum = self.v2d(value)
        instance._data[self.name] = datum


class ReadOnlyField:

    def __init__(self, descriptor):
        super(ReadOnlyField, self).__init__()
        self.descriptor = descriptor

    def __get__(self, instance, owner):
        return self.descriptor.__get__(instance, owner)

    def __set__(self, instance, value):
        raise AttributeError()

    def __delete__(self, instance):
        raise AttributeError()


class ObjectMethod:

    def __init__(self, _classmethod=None, _instancemethod=None):
        super(ObjectMethod, self).__init__()
        self.__classmethod = _classmethod
        self.__instancemethod = _instancemethod

    def __get__(self, instance, owner):
        if instance is None:
            if self.__classmethod is None:
                raise AttributeError(
                    "%s has no matching class attribute" % (instance, ))
            else:
                return MethodType(self.__classmethod, owner)
        else:
            if self.__instancemethod is None:
                raise AttributeError(
                    "%s has no matching instance attribute" % (instance, ))
            else:
                return MethodType(self.__instancemethod, instance)

    def __set__(self, instance, value):
        # Non-data descriptors (those without __set__) can be shadowed by
        # instance attributes, so prevent that by making this a read-only data
        # descriptor.
        raise AttributeError(
            "%s has no matching instance attribute" % (instance, ))

    def classmethod(self, func):
        """Set/modify the class method."""
        self.__classmethod = func
        return self

    @property
    def has_classmethod(self):
        """Has a class method been set?"""
        return self.__classmethod is not None

    def instancemethod(self, func):
        """Set/modify the instance method."""
        self.__instancemethod = func
        return self

    @property
    def has_instancemethod(self):
        """Has an instance method been set?"""
        return self.__instancemethod is not None


class OriginBase:
    """Represents a remote MAAS installation."""

    def __init__(self, session, *, objects=None):
        """
        :param session: A `bones.SessionAPI` instance.
        """
        super(OriginBase, self).__init__()
        self.__session = session
        self.__objects = {} if objects is None else objects
        self.__populate()

    def __populate(self):
        # Some objects will not have handlers in the underlying session, but
        # we want to bind them anyway, hence we iterate through all names.
        handlers = dict(self.__session.handlers)
        names = set().union(handlers, self.__objects)
        for name in names:
            handler = handlers.get(name, None)
            base = self.__objects.get(name, Object)
            assert issubclass(base, Object)
            # Put the _origin and _handler in the class's attributes, and set
            # the module to something informative.
            attrs = {"_origin": self, "_handler": handler}
            attrs["__module__"] = "origin"  # Could do better?
            # Make default methods for actions that are not handled.
            if handler is not None:
                methods = {
                    name: self.__method(action)
                    for name, action in handler.actions
                    if not hasattr(base, name)
                }
                attrs.update(methods)
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


#
# Conversion/validation functions for use with ObjectTypedField.
#


def check_string(value):
    if isinstance(value, str):
        return value
    else:
        raise TypeError("%r is not of type str" % (value,))


def check_string_or_none(value):
    if value is None:
        return value
    else:
        return check_string(value)


#
# Specialised objects.
#


class Tags(Object):
    """The set of tags."""

    @classmethod
    def list(cls):
        return [cls._origin.Tag(data) for data in cls._handler.list()]


class Tag(Object):
    """A tag."""

    name = ReadOnlyField(ObjectTypedField(
        "name", check_string, check_string))
    comment = ObjectTypedField(
        "comment", check_string, check_string, default="")
    definition = ObjectTypedField(
        "definition", check_string, check_string, default="")
    kernel_opts = ObjectTypedField(
        "kernel_opts", check_string_or_none, check_string_or_none,
        default=None)


class FilesType(ObjectType):
    """Metaclass for `Files`."""

    def __iter__(cls):
        return map(cls._origin.File, cls._handler.list())

    def list(self):
        raise NotImplementedError("list has been disabled; use read instead")


class Files(Object, metaclass=FilesType):
    """The set of files stored in MAAS."""

    @classmethod
    def read(cls):
        return list(cls)


class File(Object):
    """A file stored in MAAS."""

    filename = ReadOnlyField(ObjectTypedField(
        "filename", check_string, check_string))


class UsersType(ObjectType):
    """Metaclass for `Users`."""

    def __iter__(cls):
        return map(cls._origin.User, cls._handler.read())


class Users(Object, metaclass=UsersType):
    """The set of users."""

    @classmethod
    def read(cls):
        return list(cls)


class User(Object):
    """A user."""


#
# Now it's possible to define the default Origin, which uses the specialised
# objects created in this module. Most people should use this.
#


# Specialised objects defined in this module.
objects = {
    subclass.__name__: subclass
    for subclass in get_all_subclasses(Object)
    if subclass.__module__ == __name__
}


class Origin(OriginBase):
    """Represents a remote MAAS installation.

    Uses specialised objects defined in its originating module. This is
    probably the best choice for most people.
    """

    def __init__(self, session):
        """
        :param session: A `bones.SessionAPI` instance.
        """
        super(Origin, self).__init__(session, objects=objects)
