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
from datetime import datetime
from functools import wraps
from importlib import import_module
from itertools import (
    chain,
    starmap,
)
from types import MethodType

import pytz

from .. import bones
from ..errors import ObjectNotLoaded
from ..utils import (
    get_all_subclasses,
    vars_class,
)
from ..utils.async import Asynchronous


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
            name = owner.__name__.split('.')[0]
            return getattr(owner._origin, name.rstrip("s"))
        else:
            return getattr(owner._origin, self.name)

    def __set__(self, instance, value):
        raise AttributeError()


class ObjectType(Asynchronous, metaclass=Asynchronous):

    def __dir__(cls):
        return dir_class(cls)

    def __new__(cls, name, bases, attrs):
        attrs.setdefault("__slots__", ())
        return super(ObjectType, cls).__new__(cls, name, bases, attrs)

    def bind(cls, origin, handler, *, name=None):
        """Bind this object to the given origin and handler.

        :param origin: An instance of `Origin`.
        :param handler: An instance of `bones.HandlerAPI`.
        :return: A subclass of this class.
        """
        name = cls.__name__ if name is None else name
        attrs = {
            "_origin": origin, "_handler": handler,
            "__module__": "origin",  # Could do better?
        }
        return type(name, (cls,), attrs)


class ObjectBasics:

    __slots__ = ()

    def __dir__(self):
        return dir_instance(self)

    def __str__(self):
        return self.__class__.__qualname__


def is_pk_descriptor(descriptor):
    """Return true if `descriptor` is a primary key."""
    return descriptor.pk is True or type(descriptor.pk) is int


def get_pk_descriptors(cls):
    """Return tuple of tuples with attribute name and descriptor on the
    `cls` that is defined as the primary keys."""
    pk_fields = {
        name: descriptor
        for name, descriptor in vars_class(cls).items()
        if isinstance(descriptor, ObjectField) and is_pk_descriptor(descriptor)
    }
    if len(pk_fields) == 1:
        return (pk_fields.popitem(),)
    elif len(pk_fields) > 1:
        unique_pk_fields = {
            name: descriptor
            for name, descriptor in pk_fields.items()
            if descriptor.pk is True
        }
        if unique_pk_fields:
            raise AttributeError(
                "more than one field is marked as unique primary key: %s" % (
                    ', '.join(sorted(pk_fields))))
        else:
            return tuple(sorted((
                (name, descriptor)
                for name, descriptor in pk_fields.items()
            ), key=lambda item: item[1].pk))
    else:
        return tuple()


class Object(ObjectBasics, metaclass=ObjectType):
    """An object in a MAAS installation."""

    __slots__ = (
        "__weakref__", "_data", "_orig_data", "_changed_data", "_loaded")

    def __init__(self, data, local_data=None):
        super(Object, self).__init__()
        self._changed_data = {}
        self._loaded = False
        if isinstance(data, Mapping):
            self._data = data
            self._loaded = True
        else:
            descriptors = get_pk_descriptors(type(self))
            if len(descriptors) == 1:
                self._data = {
                    descriptors[0][1].name: data
                }
                # Validate that the primary key is correct and
                # can be converted to the python value.
                getattr(self, descriptors[0][0])
            elif len(descriptors) > 1:
                if isinstance(data, Sequence):
                    self._data = {}
                    for idx, (name, descriptor) in enumerate(descriptors):
                        self._data[descriptor.name] = data[idx]
                        # Validate that the primary key is correct and
                        # can be converted to the python value.
                        getattr(self, name)
                else:
                    raise TypeError(
                        "data must be a sequence, not %s" % (
                            type(data).__name__))
            else:
                raise TypeError(
                    "data must be a mapping, not %s"
                    % type(data).__name__)
        self._orig_data = dict(self._data)
        if local_data is not None:
            if isinstance(local_data, Mapping):
                self._data.update(local_data)
            else:
                raise TypeError(
                    "local_data must be a mapping, not %s"
                    % type(data).__name__)

    def __getattribute__(self, name):
        """Prevent access to fields that are not defined as primary keys on
        the object when its not loaded."""
        fields = {
            name: descriptor
            for name, descriptor in vars_class(type(self)).items()
            if isinstance(descriptor, ObjectField)
        }
        if name in fields:
            if self.loaded:
                return super(Object, self).__getattribute__(name)
            elif is_pk_descriptor(fields[name]):
                return super(Object, self).__getattribute__(name)
            else:
                raise ObjectNotLoaded(
                    "cannot access attribute '%s' of object '%s'" % (
                        name, type(self).__name__))
        else:
            return super(Object, self).__getattribute__(name)

    def __eq__(self, other):
        """Strict equality check.

        The type of `other` must exactly match the type of `self`. All data
        must also match.
        """
        return type(self) is type(other) and self._data == other._data

    def __repr__(self, *, name=None, fields=None):
        if name is None:
            name = self.__class__.__name__
        unloaded = ""
        if not self.loaded:
            unloaded = " (unloaded)"
            descriptors = get_pk_descriptors(type(self))
            if descriptors:
                fields = [name for name, _ in descriptors]
            else:
                fields = []
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
            return "<%s%s>" % (name, unloaded)
        else:
            return "<%s %s%s>" % (name, desc, unloaded)

    def __hash__(self):
        name = str(self.__class__.__name__)
        if hasattr(self, 'id'):
            return hash((name, self.id))
        if hasattr(self, 'system_id'):
            return hash((name, self.system_id))
        return None

    @property
    def loaded(self):
        """True when the object is loaded.

        Accessing any attribute (expected for the primary keys) of an unloaded
        object will raise an `ObjectNotLoaded` exception.
        """
        return self._loaded

    async def refresh(self):
        """Refresh the object from MAAS."""
        cls = type(self)
        if hasattr(cls, 'read'):
            descriptors = get_pk_descriptors(cls)
            if len(descriptors) == 1:
                obj = await cls.read(getattr(self, descriptors[0][0]))
            elif len(descriptors) > 1:
                args = (
                    getattr(self, name)
                    for name, _ in descriptors
                )
                obj = await cls.read(*args)
            else:
                raise AttributeError(
                    "unable to perform 'refresh' no primary key "
                    "fields defined.")
            if type(obj) is cls:
                self._data = obj._data
                self._orig_data = dict(obj._data)
                self._changed_data = {}
                self._loaded = True
            else:
                raise TypeError(
                    "result of '%s.read' must be '%s', not '%s'" % (
                        cls.__name__, cls.__name__, type(obj).__name__))
        else:
            raise AttributeError(
                "'%s' object doesn't support refresh." % cls.__name__)

    async def save(self):
        """Save the object in MAAS."""
        if hasattr(self._handler, "update"):
            if self._changed_data:
                update_data = dict(self._changed_data)
                update_data.update({
                    key: self._orig_data[key]
                    for key in self._handler.params
                })
                self._data = await self._handler.update(**update_data)
                self._orig_data = dict(self._data)
                self._changed_data = {}
        else:
            raise AttributeError(
                "'%s' object doesn't support save." % type(self).__name__)


def ManagedCreate(super_cls):
    """Dynamically creates a `create` method for a `ObjectSet.Managed` class
    that calls the `super_cls.create`.

    The first positional argument that is passed to the `super_cls.create` is
    the `_manager` that was set using `ObjectSet.Managed`. The created object
    is added to the `ObjectSet.Managed` also placed in the correct
    `_data[field]` and `_orig_data[field]` for the `_manager` object.
    """

    @wraps(super_cls.create)
    async def _create(self, *args, **kwargs):
        cls = type(self)
        manager = getattr(cls, '_manager', None)
        manager_field = getattr(cls, '_manager_field', None)
        if manager is not None and manager_field is not None:
            args = (manager,) + args
            new_obj = await super_cls.create(*args, **kwargs)
            self._items = self._items + [new_obj]
            manager._data[manager_field.name] = (
                manager._data[manager_field.name] +
                [new_obj._data])
            manager._orig_data[manager_field.name] = (
                manager._orig_data[manager_field.name] +
                [new_obj._data])
            return new_obj
        else:
            raise AttributeError(
                'create is not supported; %s is not a managed set' % (
                    super_cls.__name__))
    return _create


class ObjectSet(ObjectBasics, metaclass=ObjectType):
    """A set of objects in a MAAS installation."""

    __slots__ = "__weakref__", "_items"

    _object = OriginObjectRef()

    @classmethod
    def Managed(cls, manager, field, items):
        """Create a custom `ObjectSet` that is managed by a related `Object.`

        :param manager: The manager of the `ObjectSet`. This is the `Object`
            that manages this set of objects.
        :param field: The field on the `manager` that created this managed
            `ObjectSet`.
        :param items: The items in the `ObjectSet`.
        """
        attrs = {
            "_manager": manager,
            "_manager_field": field,
        }
        if hasattr(cls, "create"):
            attrs['create'] = ManagedCreate(cls)
        cls = type(
            "%s.Managed#%s" % (
                cls.__name__, manager.__class__.__name__), (cls,), attrs)
        return cls(items)

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

    def __eq__(self, other):
        """Strict equality check.

        The type of `other` must exactly match the type of `self`. All items
        must also match.
        """
        return type(self) is type(other) and self._items == other._items

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

    def __init__(self, name, *, default=undefined, readonly=False, pk=False):
        """Create a `ObjectField` with an optional default.

        :param name: The name of the field. This is the name that's used to
            store the datum in the MAAS-side data dictionary.
        :param default: A default value to return when `name` is not found in
            the MAAS-side data dictionary.
        :param readonly: If true, prevent setting or deleting of this field.
        :param pk: If true marks the field as the unique primary key for the
            object it is defined on. If an integer then it define its place
            in the tuple of values that makes the object uniquely identified.
        """
        super(ObjectField, self).__init__()
        self.name = name
        self.default = default
        if not isinstance(readonly, bool):
            raise ValueError(
                'readonly must be a bool, not %s' % type(readonly).__name__)
        else:
            self.readonly = readonly
        if not isinstance(pk, (bool, int)):
            raise ValueError(
                'pk must be a bool or an int, not %s' % type(pk).__name__)
        else:
            self.pk = pk

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
            if self.name in instance._orig_data:
                orig_datum = instance._orig_data[self.name]
                if self.name in instance._changed_data:
                    if orig_datum == datum:
                        # Value set back to original value.
                        del instance._changed_data[self.name]
                    else:
                        # Value changed still update to new value.
                        instance._changed_data[self.name] = datum
                elif orig_datum != datum:
                    # New value changed.
                    instance._changed_data[self.name] = datum
            else:
                instance._changed_data[self.name] = datum

    def __delete__(self, instance):
        """Standard Python descriptor method."""
        if self.readonly:
            raise AttributeError("%s is read-only" % self.name)
        elif self.name in instance._data:
            del instance._data[self.name]
            # Mark the field as deleted.
            instance._changed_data[self.name] = None
        else:
            pass  # Nothing to do.


class ObjectFieldRelated(ObjectField):

    def __init__(
            self, name, cls, *,
            default=undefined, readonly=False, pk=False, reverse=undefined):
        """Create a `ObjectFieldRelated` with `cls`.

        :param name: The name of the field. This is the name that's used to
            store the datum in the MAAS-side data dictionary.
        :param cls: The name of the object class to convert into.
        :param default: A default value to return when `name` is not found in
            the MAAS-side data dictionary.
        :param readonly: If true, prevent setting or deleting of this field.
        :param pk: If true marks the field as the unique primary key for the
            object it is defined on. If an integer then it define its place
            in the tuple of values that makes the object uniquely identified.
        :param reverse: The name of the field on the returned instances of
            `cls` to place this objects instance.
        """
        super(ObjectFieldRelated, self).__init__(
            name, default=default, readonly=readonly, pk=pk)
        self.reverse = reverse
        if not isinstance(cls, str):
            if not issubclass(cls, Object):
                raise TypeError(
                    "%s is not a subclass of Object" % cls)
            else:
                self.cls = cls.__name__
        else:
            self.cls = cls

    def datum_to_value(self, instance, datum):
        """Convert a given MAAS-side datum to a Python-side value.

        :param instance: The `Object` instance on which this field is
            currently operating. This method should treat it as read-only, for
            example to perform validation with regards to other fields.
        :param datum: The MAAS-side datum to validate and convert into a
            Python-side value.
        :return: A set of `cls` from the given datum.
        """
        if datum is None:
            return None
        local_data = None
        if self.reverse is not None:
            local_data = {}
            if self.reverse is undefined:
                local_data[instance.__class__.__name__.lower()] = instance
            else:
                local_data[self.reverse] = instance
        # Get the class from the bound origin.
        bound = getattr(instance._origin, self.cls)
        return bound(datum, local_data=local_data)

    def value_to_datum(self, instance, value):
        """Convert a given Python-side value to a MAAS-side datum.

        :param instance: The `Object` instance on which this field is
            currently operating. This method should treat it as read-only, for
            example to perform validation with regards to other fields.
        :param datum: The Python-side value to validate and convert into a
            MAAS-side datum.
        :return: A datum derived from the given value.
        """
        if value is None:
            return None
        bound = getattr(instance._origin, self.cls)
        if type(value) is bound:
            # Use the primary keys to set the value.
            descriptors = get_pk_descriptors(bound)
            if len(descriptors) == 1:
                return getattr(value, descriptors[0][0])
            elif len(descriptors) > 1:
                return tuple(
                    getattr(value, name)
                    for name, _ in descriptors
                )
            else:
                raise AttributeError(
                    "unable to perform set object no primary key "
                    "fields defined for %s" % self.cls)
        else:
            raise TypeError(
                "must be %s, not %s" % (self.cls, type(value).__name__))


class ObjectFieldRelatedSet(ObjectField):

    def __init__(self, name, cls, *, reverse=undefined, default=undefined):
        """Create a `ObjectFieldRelatedSet` with `cls`.

        :param name: The name of the field. This is the name that's used to
            store the datum in the MAAS-side data dictionary.
        :param cls: The name of the object class to convert the sequence of
            data into.
        :param reverse: The name of the field on the returned instances of
            `cls` to place this objects instance.
        :param default: A default value to return when `name` is not found in
            the MAAS-side data dictionary.
        """
        if default is undefined:
            default = []
        super(ObjectFieldRelatedSet, self).__init__(
            name, default=default, readonly=True)
        self.reverse = reverse
        if not isinstance(cls, str):
            if not issubclass(cls, ObjectSet):
                raise TypeError(
                    "%s is not a subclass of ObjectSet" % cls)
            else:
                self.cls = cls.__name__
        else:
            self.cls = cls

    def datum_to_value(self, instance, datum):
        """Convert a given MAAS-side datum to a Python-side value.

        :param instance: The `Object` instance on which this field is
            currently operating. This method should treat it as read-only, for
            example to perform validation with regards to other fields.
        :param datum: The MAAS-side datum to validate and convert into a
            Python-side value.
        :return: A set of `cls` from the given datum.
        """
        if datum is None:
            return []
        if not isinstance(datum, Sequence):
            raise TypeError(
                "datum must be a sequence, not %s" % type(datum).__name__)
        local_data = None
        if self.reverse is not None:
            local_data = {}
            if self.reverse is undefined:
                local_data[instance.__class__.__name__.lower()] = instance
            else:
                local_data[self.reverse] = instance
        # Get the class from the bound origin.
        bound = getattr(instance._origin, self.cls)
        return bound.Managed(
            instance, self,
            (
                bound._object(item, local_data=local_data)
                for item in datum
            ))


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

    @property
    def session(self):
        """The underlying `bones` session."""
        return self.__session

    def __populate(self):
        # Some objects will not have handlers in the underlying session, but
        # we want to bind them anyway, hence we iterate through all names.
        handlers = dict(self.__session.handlers)
        names = set().union(handlers, self.__objects)
        for name in names:
            handler = handlers.get(name, None)
            base = self.__objects.get(name, Object)
            assert issubclass(type(base), ObjectType)
            obj = base.bind(self, handler, name=name)
            # Those objects without a custom class are "hidden" by prefixing
            # their name with an underscore.
            objname = "_%s" % name if base is Object else name
            setattr(self, objname, obj)


#
# Conversion/validation functions for use with ObjectTypedField.
#


def to(cls):
    def to_cls(value):
        return cls(value)
    return to_cls


def check(expected):
    def checker(value):
        if issubclass(type(value), expected):
            return value
        else:
            raise TypeError(
                "%r is not of type %s" % (value, expected))
    return checker


def check_optional(expected):
    return check((expected, type(None)))


def parse_timestamp(created):
    created = datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%f")
    return created.replace(tzinfo=pytz.UTC)


def mapping_of(cls):
    """Expects a mapping from some key to data for `cls` instances."""
    def mapper(data):
        if not isinstance(data, Mapping):
            raise TypeError(
                "data must be a mapping, not %s"
                % type(data).__name__)
        return {
            key: cls(value)
            for key, value in data.items()
        }
    return mapper


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


class OriginType(Asynchronous):
    """Metaclass for `Origin`."""

    async def fromURL(cls, url, *, credentials=None, insecure=False):
        """Return an `Origin` for a given MAAS instance."""
        session = await bones.SessionAPI.fromURL(
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

    async def login(
            cls, url, *, username=None, password=None, insecure=False):
        """Make an `Origin` by logging-in with a username and password.

        :return: A tuple of ``profile`` and ``origin``, where the former is an
            unsaved `Profile` instance, and the latter is an `Origin` instance
            made using the profile.
        """
        profile, session = await bones.SessionAPI.login(
            url=url, username=username, password=password, insecure=insecure)
        return profile, cls(session)

    async def connect(
            cls, url, *, apikey=None, insecure=False):
        """Make an `Origin` by connecting with an apikey.

        :return: A tuple of ``profile`` and ``origin``, where the former is an
            unsaved `Profile` instance, and the latter is an `Origin` instance
            made using the profile.
        """
        profile, session = await bones.SessionAPI.connect(
            url=url, apikey=apikey, insecure=insecure)
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
            ".",
            ".account",
            ".boot_resources",
            ".boot_sources",
            ".boot_source_selections",
            ".controllers",
            ".devices",
            ".events",
            ".subnets",
            ".fabrics",
            ".spaces",
            ".files",
            ".interfaces",
            ".ipranges",
            ".maas",
            ".machines",
            ".spaces",
            ".sshkeys",
            ".static_routes",
            ".subnets",
            ".tags",
            ".users",
            ".version",
            ".vlans",
            ".zones",
        }
        super(Origin, self).__init__(
            session, objects=find_objects({
                import_module(name, __name__).__name__
                for name in modules
            }),
        )
