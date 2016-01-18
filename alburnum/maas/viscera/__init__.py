"""Interact with a remote MAAS (https://maas.ubuntu.com/).

These are highish-level bindings that provide user-oriented objects to
interact with. They're intended for developers, for folk comfortable working
with Python. They're not a front-end. Hence the name "viscera"; the classes
and functions here are the meat and organs around the "bones", but not the
"flesh".

"""

__all__ = [
    "check",
    "check_optional",
    "Object",
    "ObjectField",
    "ObjectMethod",
    "ObjectType",
    "ObjectTypedField",
    "Origin",
    "OriginBase",
]

from importlib import import_module
from itertools import (
    chain,
    starmap,
)
from types import MethodType
from typing import Optional

from alburnum.maas.utils import (
    get_all_subclasses,
    vars_class,
)


undefined = object()


class Disabled:
    """A disabled method."""

    def __init__(self, name, alternative=None):
        super(Disabled, self).__init__()
        self.name, self.alternative = name, alternative

    def __call__(self, *args, **kwargs):
        if self.alternative is None:
            raise RuntimeError("%s has been disabled" % (self.name,))
        else:
            raise RuntimeError(
                "%s has been disabled; use %s instead" % (
                    self.name, self.alternative))


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
        elif isinstance(value, Disabled):
            pass  # Hide this; disabled.
        else:
            yield name
    # Metaclass attributes.
    for name, value in vars_class(type(cls)).items():
        if name == "mro":
            pass  # Hide this; not interesting.
        elif isinstance(value, Disabled):
            pass  # Hide this; disabled.
        else:
            yield name


def dir_instance(inst):
    """Return a list of names available on `inst`.

    Eliminates names that bind to an `ObjectMethod` without a corresponding
    instance method; see `ObjectMethod`.
    """
    # Skip instance attributes; __slots__ is automatically defined, and
    # descriptors are used to define attributes. Instead, go straight to class
    # attributes (including methods).
    for name, value in vars_class(type(inst)).items():
        if isinstance(value, ObjectMethod):
            if value.has_instancemethod:
                yield name
        elif isinstance(value, Disabled):
            pass  # Hide this; disabled.
        else:
            yield name


class OriginObjectRef:
    """A reference to an object in the origin.

    Use this on an `Object` to reference a related object type via a bound
    origin (see `OriginBase`). By default this guesses that the name of the
    referenced object is the singular of the owner's name. For example,
    given::

      class Things(Object):
          _object = OriginObjectRef()

    `Things._object` would look for `Things._origin.Thing`. When referencing
    something that has non-trivial singular/plural naming, specify the name to
    the `OriginObjectRef` constructor.
    """

    def __init__(self, name=None):
        super(OriginObjectRef, self).__init__()
        self.name = name

    def __get__(self, instance, owner):
        if self.name is None:
            return getattr(owner._origin, owner.__name__.rstrip("s"))
        else:
            return getattr(owner._origin, self.name)

    def __set__(self, instance, value):
        raise AttributeError()


class ObjectType(type):

    def __dir__(cls):
        return list(dir_class(cls))

    def __new__(cls, name, bases, attrs):
        attrs.setdefault("__slots__", ())
        return super(ObjectType, cls).__new__(cls, name, bases, attrs)


class ObjectBasics:

    __slots__ = ()

    def __dir__(self):
        return list(dir_instance(self))

    def __str__(self):
        return self.__class__.__qualname__

    def __repr__(self):
        fields = sorted(
            name for name, value in vars_class(type(self)).items()
            if isinstance(value, ObjectField))
        values = (getattr(self, name) for name in fields)
        pairs = starmap("{0}={1!r}".format, zip(fields, values))
        desc = " ".join(pairs)
        if len(desc) == 0:
            return "<%s>" % (self.__class__.__name__, )
        else:
            return "<%s %s>" % (self.__class__.__name__, desc)


class Object(ObjectBasics, metaclass=ObjectType):
    """An object in a MAAS installation."""

    __slots__ = "__weakref__", "_data"

    def __init__(self, data):
        super(Object, self).__init__()
        assert isinstance(data, dict)
        self._data = data


class ObjectSet(ObjectBasics, list, metaclass=ObjectType):
    """A set of objects in a MAAS installation."""

    __slots__ = "__weakref__",

    _object = OriginObjectRef()

    def __init__(self, items):
        super(ObjectSet, self).__init__(items)


class ObjectField:

    def __init__(self, name, *, default=undefined, readonly=False):
        super(ObjectField, self).__init__()
        self.name = name
        self.default = default
        self.readonly = readonly

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
        if self.readonly:
            raise AttributeError("%s is read-only" % self.name)
        else:
            instance._data[self.name] = value

    def __delete__(self, instance):
        if self.readonly:
            raise AttributeError("%s is read-only" % self.name)
        elif self.name in instance._data:
            del instance._data[self.name]
        else:
            pass  # Nothing to do.


class ObjectTypedField(ObjectField):

    def __init__(
            self, name, datum_to_value=None, value_to_datum=None, *,
            default=undefined, readonly=False):
        super(ObjectTypedField, self).__init__(
            name, default=default, readonly=readonly)
        self.datum_to_value = (
            (lambda d: d) if datum_to_value is None else datum_to_value)
        self.value_to_datum = (
            (lambda v: v) if value_to_datum is None else value_to_datum)
        if default is not undefined:
            if self.datum_to_value(self.value_to_datum(default)) != default:
                raise TypeError(
                    "The default of %r cannot be round-tripped through the "
                    "conversion/validation functions given." % (default, ))

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            datum = super(ObjectTypedField, self).__get__(instance, owner)
            if datum is self.default:
                return datum
            else:
                return self.datum_to_value(datum)

    def __set__(self, instance, value):
        datum = self.value_to_datum(value)
        super(ObjectTypedField, self).__set__(instance, datum)


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
            assert issubclass(type(base), ObjectType)
            # Put the _origin and _handler in the class's attributes, and set
            # the module to something informative.
            attrs = {"_origin": self, "_handler": handler}
            attrs["__module__"] = "origin"  # Could do better?
            # Make default methods for actions that are not handled.
            if handler is not None:
                if issubclass(base, Object):
                    methods = {
                        "_%s" % name: self.__method(action)
                        for name, action in handler.actions
                        if not hasattr(base, name)
                    }
                    attrs.update(methods)
                elif issubclass(base, ObjectSet):
                    pass  # TODO?
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
                return cls._object(data)

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


def check(expected):
    def checker(value):
        if issubclass(type(value), expected):
            return value
        else:
            raise TypeError(
                "%r is not of type %s" % (value, expected))
    return checker


def check_optional(expected):
    return check(Optional[expected])


#
# Specialised objects.
#


class TagsType(ObjectType):
    """Metaclass for `Tags`."""

    def __iter__(cls):
        return map(cls._object, cls._handler.list())

    def create(cls, name, *, comment="", definition="", kernel_opts=""):
        data = cls._handler.new(
            name=name, comment=comment, definition=definition,
            kernel_opts=kernel_opts)
        return cls._object(data)

    new = Disabled("new", "create")  # API is malformed in MAAS server.

    def read(cls):
        return cls(cls)

    list = Disabled("list", "read")  # API is malformed in MAAS server.


class Tags(ObjectSet, metaclass=TagsType):
    """The set of tags."""


class Tag(Object):
    """A tag."""

    name = ObjectTypedField(
        "name", check(str), readonly=True)
    comment = ObjectTypedField(
        "comment", check(str), check(str), default="")
    definition = ObjectTypedField(
        "definition", check(str), check(str), default="")
    kernel_opts = ObjectTypedField(
        "kernel_opts", check_optional(str), check_optional(str),
        default=None)


class FilesType(ObjectType):
    """Metaclass for `Files`."""

    def __iter__(cls):
        return map(cls._object, cls._handler.list())

    def read(cls):
        return list(cls)

    list = Disabled("list", "read")  # API is malformed in MAAS server.


class Files(ObjectSet, metaclass=FilesType):
    """The set of files stored in MAAS."""


class File(Object):
    """A file stored in MAAS."""

    filename = ObjectTypedField(
        "filename", check(str), readonly=True)


class UsersType(ObjectType):
    """Metaclass for `Users`."""

    def __iter__(cls):
        return map(cls._object, cls._handler.read())


class Users(ObjectSet, metaclass=UsersType):
    """The set of users."""

    @classmethod
    def read(cls):
        return list(cls)


class User(Object):
    """A user."""

    username = ObjectTypedField(
        "username", check(str), check(str))
    email = ObjectTypedField(
        "email", check(str), check(str))
    is_admin = ObjectTypedField(
        "is_superuser", check(bool), check(bool))


#
# Now it's possible to define the default Origin, which uses the specialised
# objects created in this module. Most people should use this.
#


def find_objects(modules):
    """Find subclasses of `Object` and `ObjectSet` in the given modules.

    :param modules: The full *names* of modules to include. These modules MUST
        have been imported in advance.
    """
    return {
        subclass.__name__: subclass
        for subclass in chain(
            get_all_subclasses(Object),
            get_all_subclasses(ObjectSet),
        )
        if subclass.__module__ in modules
    }


class Origin(OriginBase):
    """Represents a remote MAAS installation.

    Uses specialised objects defined in its originating module and specific
    submodules. This is probably the best choice for most people.
    """

    def __init__(self, session):
        """
        :param session: A `bones.SessionAPI` instance.

        """
        super(Origin, self).__init__(
            session, objects=find_objects({
                import_module(name, __name__).__name__
                for name in {".", ".nodes"}
            }),
        )
