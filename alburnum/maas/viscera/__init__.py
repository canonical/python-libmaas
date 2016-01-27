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
    "Origin",
    "OriginBase",
]

from collections import (
    Iterable,
    Mapping,
    Sequence,
)
from copy import copy
from functools import wraps
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

from .. import bones


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
        elif isinstance(value, (classmethod, staticmethod)):
            pass  # Hide this; not interesting here.
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
        return dir_class(cls)

    def __new__(cls, name, bases, attrs):
        attrs.setdefault("__slots__", ())
        return super(ObjectType, cls).__new__(cls, name, bases, attrs)


class ObjectBasics:

    __slots__ = ()

    def __dir__(self):
        return dir_instance(self)

    def __str__(self):
        return self.__class__.__qualname__


class Object(ObjectBasics, metaclass=ObjectType):
    """An object in a MAAS installation."""

    __slots__ = "__weakref__", "_data"

    def __init__(self, data):
        super(Object, self).__init__()
        if isinstance(data, Mapping):
            self._data = data
        else:
            raise TypeError(
                "data must be a mapping, not %s"
                % type(data).__name__)

    def __repr__(self, *, fields=None):
        if fields is None:
            fields = sorted(
                name for name, value in vars_class(type(self)).items()
                if isinstance(value, ObjectField))
        else:
            fields = sorted(fields)
        values = (getattr(self, name) for name in fields)
        pairs = starmap("{0}={1!r}".format, zip(fields, values))
        desc = " ".join(pairs)
        if len(desc) == 0:
            return "<%s>" % (self.__class__.__name__, )
        else:
            return "<%s %s>" % (self.__class__.__name__, desc)


class ObjectSet(ObjectBasics, metaclass=ObjectType):
    """A set of objects in a MAAS installation."""

    __slots__ = "__weakref__", "_items"

    _object = OriginObjectRef()

    def __init__(self, items):
        super(ObjectSet, self).__init__()
        if isinstance(items, (Mapping, str, bytes)):
            raise TypeError(
                "data must be sequence-like, not %s"
                % type(items).__name__)
        elif isinstance(items, Sequence):
            self._items = items
        elif isinstance(items, Iterable):
            self._items = list(items)
        else:
            raise TypeError(
                "data must be sequence-like, not %s"
                % type(items).__name__)

    def __len__(self):
        """Return the count of items contained herein."""
        return len(self._items)

    def __getitem__(self, spec):
        """Get a contained item or slice of contained items.

        Fetching a slice returns a new instance of this class containing the
        subset of items defined by the slice.
        """
        if isinstance(spec, slice):
            self = copy(self)
            self._items = self._items[spec]
            return self
        else:
            return self._items[spec]

    def __iter__(self):
        """Return an iterator for the contained items."""
        return iter(self._items)

    def __reversed__(self):
        """Efficiently provide the contained items in reversed order.

        This is more efficient than relying on the default behaviour of
        ``reversed``, which is to use ``__len__`` and ``__getitem__``.
        """
        return reversed(self._items)

    def __contains__(self, item):
        """Efficiently test if a given item is among the contained items.

        This is more efficient than relying on the default behaviour of
        ``in``, which is to use ``__iter__`` then the old sequence iteration
        protocol using ``__len__`` and ``__getitem__``.
        """
        return item in self._items

    def __repr__(self):
        return "<%s length=%d items=%r>" % (
            self.__class__.__name__, len(self._items), self._items)


class ObjectField:
    """A field on an `Object`.

    By default, no conversion and/or validation is performed; the value
    retrieved from MAAS's Web API (tranmitted as JSON) is returned when
    accessing this field, and is set or deleted when setting or deleting this
    field.

    It is possible to declare this field as read-only and to specify a default
    value when the corresponding datum is not found.

    A word on the "value" and "datum" nomenclature used here:

    * A "value" is a Python-side value, i.e. the one you'll work with in a
      program that uses this API.

    * A "datum" is an item of data obtained from MAAS's Web API, or ready to
      be sent back to MAAS's Web API. It is almost always something that can
      be dumped as JSON.

    A value passed into a field must be converted to a datum and vice-versa.
    To support this, two methods can be customised in `ObjectField`
    subclasses: ``value_to_datum`` and ``datum_to_value``.

    These methods serve to both convert and validate, but the default
    implementions do nothing.

    Alternatively, simple conversion functions can be passed to the `Checked`
    constructor.

    """

    @classmethod
    def Checked(cls, name, datum_to_value=None, value_to_datum=None, **other):
        """Create a custom `ObjectField` that validates values and datums.

        :param name: The name of the field. This is the name that's used to
            store the datum in the MAAS-side data dictionary.
        :param datum_to_value: A callable taking a single ``datum`` argument,
            passed positionally. This callable should convert the datum to a
            Python-side value, and/or raise an exception for invalid datums.
        :param value_to_datum: A callable taking a single ``value`` argument,
            passed positionally. This callable should convert the value to a
            MAAS-side datum, and/or raise an exception for invalid values.
        :param other: Additional arguments to pass to the default
            `ObjectField` constructor.
        """
        attrs = {}
        if datum_to_value is not None:
            @wraps(datum_to_value)
            def datum_to_value_method(instance, datum):
                return datum_to_value(datum)
            attrs["datum_to_value"] = staticmethod(datum_to_value_method)
        if value_to_datum is not None:
            @wraps(value_to_datum)
            def value_to_datum_method(instance, value):
                return value_to_datum(value)
            attrs["value_to_datum"] = staticmethod(value_to_datum_method)
        cls = type("%s.Checked#%s" % (cls.__name__, name), (cls,), attrs)
        return cls(name, **other)

    def __init__(self, name, *, default=undefined, readonly=False):
        """Create a `ObjectField` with an optional default.

        :param name: The name of the field. This is the name that's used to
            store the datum in the MAAS-side data dictionary.
        :param default: A default value to return when `name` is not found in
            the MAAS-side data dictionary.
        :param readonly: If true, prevent setting or deleting of this field.
        """
        super(ObjectField, self).__init__()
        self.name = name
        self.default = default
        self.readonly = readonly

    def datum_to_value(self, instance, datum):
        """Convert a given MAAS-side datum to a Python-side value.

        :param instance: The `Object` instance on which this field is
            currently operating. This method should treat it as read-only, for
            example to perform validation with regards to other fields.
        :param datum: The MAAS-side datum to validate and convert into a
            Python-side value.
        :return: A value derived from the given datum.
        """
        return datum

    def value_to_datum(self, instance, value):
        """Convert a given Python-side value to a MAAS-side datum.

        :param instance: The `Object` instance on which this field is
            currently operating. This method should treat it as read-only, for
            example to perform validation with regards to other fields.
        :param datum: The Python-side value to validate and convert into a
            MAAS-side datum.
        :return: A datum derived from the given value.
        """
        return value

    def __get__(self, instance, owner):
        """Standard Python descriptor method."""
        if instance is None:
            return self
        else:
            if self.name in instance._data:
                datum = instance._data[self.name]
                return self.datum_to_value(instance, datum)
            elif self.default is undefined:
                raise AttributeError(self.name)
            else:
                return self.default

    def __set__(self, instance, value):
        """Standard Python descriptor method."""
        if self.readonly:
            raise AttributeError("%s is read-only" % self.name)
        else:
            datum = self.value_to_datum(instance, value)
            instance._data[self.name] = datum

    def __delete__(self, instance):
        """Standard Python descriptor method."""
        if self.readonly:
            raise AttributeError("%s is read-only" % self.name)
        elif self.name in instance._data:
            del instance._data[self.name]
        else:
            pass  # Nothing to do.


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
# Now it's possible to define the default Origin, which uses a predefined set
# of specialised objects. Most people should use this.
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


class OriginType(type):
    """Metaclass for `Origin`."""

    def fromURL(cls, url, *, credentials=None, insecure=False):
        """Return an `Origin` for a given MAAS instance."""
        session = bones.SessionAPI.fromURL(
            url, credentials=credentials, insecure=insecure)
        return cls(session)

    def fromProfile(cls, profile):
        """Return an `Origin` from a given configuration profile.

        :see: `ProfileStore`.
        """
        session = bones.SessionAPI.fromProfile(profile)
        return cls(session)

    def fromProfileName(cls, name):
        """Return an `Origin` from a given configuration profile name.

        :see: `ProfileStore`.
        """
        session = bones.SessionAPI.fromProfileName(name)
        return cls(session)

    def login(cls, url, *, username=None, password=None, insecure=False):
        """Make an `Origin` by logging-in with a username and password.

        :return: A tuple of ``profile`` and ``origin``, where the former is an
            unsaved `Profile` instance, and the latter is an `Origin` instance
            made using the profile.
        """
        profile, session = bones.SessionAPI.login(
            url=url, username=username, password=password,
            insecure=insecure)
        return profile, cls(session)

    def __dir__(cls):
        return dir_class(cls)


class Origin(OriginBase, metaclass=OriginType):
    """Represents a remote MAAS installation.

    Uses specialised objects defined in its originating module and specific
    submodules. This is probably the best choice for most people.
    """

    def __init__(self, session):
        """
        :param session: A `bones.SessionAPI` instance.

        """
        modules = {
            ".", ".events", ".files", ".nodes", ".tags", ".users", ".version",
        }
        super(Origin, self).__init__(
            session, objects=find_objects({
                import_module(name, __name__).__name__
                for name in modules
            }),
        )
