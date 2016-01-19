"""Tests for `alburnum.maas.viscera`."""

__all__ = []

from random import randrange
from unittest.mock import sentinel

from alburnum.maas.testing import (
    make_name_without_spaces,
    TestCase,
)
from testtools.matchers import (
    Contains,
    ContainsAll,
    Equals,
    HasLength,
    Not,
)

from .. import (
    dir_class,
    dir_instance,
    Disabled,
    Object,
    ObjectBasics,
    ObjectField,
    ObjectMethod,
    ObjectSet,
    ObjectType,
)
from ... import viscera


class TestDirClass(TestCase):
    """Tests for `dir_class`."""

    def test__includes_ObjectMethod_descriptors_with_class_methods(self):

        class Example:
            attribute = ObjectMethod(sentinel.function)

        self.assertThat(
            list(dir_class(Example)),
            Contains("attribute"))

    def test__excludes_ObjectMethod_descriptors_without_class_methods(self):

        class Example:
            attribute = ObjectMethod()

        self.assertThat(
            list(dir_class(Example)),
            Not(Contains("attribute")))

    def test__excludes_Disabled_class_descriptors(self):

        class Example:
            attribute = Disabled("foobar")

        self.assertThat(
            list(dir_class(Example)),
            Not(Contains("attribute")))

    def test__includes_other_class_attributes(self):

        class Example:
            alice = "is the first"
            bob = lambda self: "just bob"
            carol = classmethod(lambda cls: "carol")
            dave = property(lambda self: "dave or david")
            erin = staticmethod(lambda: "or eve?")

        self.assertThat(
            list(dir_class(Example)),
            ContainsAll(["alice", "bob", "carol", "dave", "erin"]))

    def test__excludes_mro_metaclass_method(self):

        class Example:
            """Example class."""

        self.assertThat(
            list(dir_class(Example)),
            Not(Contains("mro")))

    def test__excludes_Disabled_metaclass_descriptors(self):

        class ExampleType(type):
            attribute = Disabled("foobar")

        class Example(metaclass=ExampleType):
            "Example class with metaclass."""

        self.assertThat(
            list(dir_class(Example)),
            Not(Contains("attribute")))

    def test__includes_superclass_attributes(self):

        class ExampleBase:
            alice = "is the first"
            bob = lambda self: "just bob"

        class Example(ExampleBase):
            carol = classmethod(lambda cls: "carol")
            dave = property(lambda self: "dave or david")
            erin = staticmethod(lambda: "or eve?")

        self.assertThat(
            list(dir_class(Example)),
            ContainsAll(["alice", "bob", "carol", "dave", "erin"]))


class TestDirInstance(TestCase):
    """Tests for `dir_instance`."""

    def test__includes_ObjectMethod_descriptors_with_instance_methods(self):

        class Example:
            attribute = ObjectMethod()
            attribute.instancemethod(sentinel.function)

        example = Example()

        self.assertThat(
            list(dir_instance(example)),
            Contains("attribute"))

    def test__excludes_ObjectMethod_descriptors_without_instance_methods(self):

        class Example:
            attribute = ObjectMethod()
            attribute.classmethod(sentinel.function)

        example = Example()

        self.assertThat(
            list(dir_instance(example)),
            Not(Contains("attribute")))

    def test__excludes_Disabled_class_descriptors(self):

        class Example:
            attribute = Disabled("foobar")

        example = Example()

        self.assertThat(
            list(dir_instance(example)),
            Not(Contains("attribute")))

    def test__excludes_class_methods(self):

        class Example:
            carol = classmethod(lambda cls: "carol")

        example = Example()

        self.assertThat(
            list(dir_instance(example)),
            Not(Contains("carol")))

    def test__excludes_static_methods(self):

        class Example:
            steve = staticmethod(lambda: "or eve?")

        example = Example()

        self.assertThat(
            list(dir_instance(example)),
            Not(Contains("steve")))

    def test__includes_other_class_attributes(self):

        class Example:
            alice = "is the first"
            bob = lambda self: "just bob"
            dave = property(lambda self: "or david")

        example = Example()

        self.assertThat(
            list(dir_instance(example)),
            ContainsAll(["alice", "bob", "dave"]))

    def test__excludes_instance_attributes(self):
        # In a bit of a departure, dir_instance(foo) will NOT return instance
        # attributes of foo. This is because object attributes in viscera
        # should be defined using descriptors (which are class attributes).

        class Example:
            """Example class."""

        example = Example()
        example.alice = 123

        self.assertThat(
            list(dir_instance(example)),
            Not(Contains(["alice"])))


class TestObjectType(TestCase):
    """Tests for `ObjectType`."""

    def test__classes_always_have_slots_defined(self):

        class WithoutSlots(metaclass=ObjectType):
            """A class WITHOUT __slots__ defined explicitly."""

        self.assertThat(WithoutSlots.__slots__, Equals(()))
        self.assertRaises(AttributeError, getattr, WithoutSlots(), "__dict__")

        class WithSlots(metaclass=ObjectType):
            """A class WITH __slots__ defined explicitly."""
            __slots__ = "a", "b"

        self.assertThat(WithSlots.__slots__, Equals(("a", "b")))
        self.assertRaises(AttributeError, getattr, WithSlots(), "__dict__")

    def test__uses_dir_class(self):

        class Dummy(metaclass=ObjectType):
            """Does nothing; just a stand-in."""

        dir_class = self.patch(viscera, "dir_class")
        dir_class.return_value = iter([sentinel.name])

        self.assertThat(dir(Dummy), Equals([sentinel.name]))


class TestObjectBasics(TestCase):
    """Tests for `ObjectBasics`."""

    def test__defines_slots(self):
        self.assertThat(ObjectBasics.__slots__, Equals(()))

    def test__uses_dir_instance(self):
        dir_instance = self.patch(viscera, "dir_instance")
        dir_instance.return_value = iter([sentinel.name])

        self.assertThat(dir(ObjectBasics()), Equals([sentinel.name]))

    def test__stringification_returns_qualified_class_name(self):
        self.assertThat(str(ObjectBasics()), Equals(ObjectBasics.__qualname__))

    def test__string_representation_includes_ObjectField_values(self):

        class Example(ObjectBasics):
            alice = ObjectField("alice")
            bob = ObjectField("bob")

        example = Example()
        example._data = {
            "alice": make_name_without_spaces("alice"),
            "bob": make_name_without_spaces("bob"),
        }

        self.assertThat(repr(example), Equals(
            "<Example alice=%(alice)r bob=%(bob)r>" % example._data))


class TestObject(TestCase):
    """Tests for `Object`."""

    def test__defines_slots(self):
        self.assertThat(
            Object.__slots__,
            Equals(("__weakref__", "_data")))

    def test__inherits_ObjectBasics(self):
        self.assertThat(Object.__mro__, Contains(ObjectBasics))

    def test__init_sets__data(self):
        data = {"alice": make_name_without_spaces("alice")}
        self.assertThat(Object(data)._data, Equals(data))


class TestObjectSet(TestCase):
    """Tests for `ObjectSet`."""

    def test__defines_slots(self):
        self.assertThat(
            ObjectSet.__slots__,
            Equals(("__weakref__", "_items")))

    def test__inherits_ObjectBasics(self):
        self.assertThat(ObjectSet.__mro__, Contains(ObjectBasics))

    def test__init_sets__items(self):
        items = [{"alice": make_name_without_spaces("alice")}]
        self.assertThat(ObjectSet(items)._items, Equals(items))

    def test__length_is_number_of_items(self):
        items = [0] * randrange(0, 100)
        objectset = ObjectSet(items)
        self.assertThat(objectset, HasLength(len(items)))

    def test__items_can_be_indexed(self):
        items = [make_name_without_spaces(str(index)) for index in range(5)]
        objectset = ObjectSet(items)
        for index, item in enumerate(items):
            self.assertThat(objectset[index], Equals(item))

    def test__iteration_yield_items(self):
        items = [make_name_without_spaces(str(index)) for index in range(5)]
        objectset = ObjectSet(items)
        self.assertThat(list(objectset), Equals(items))
