"""Tests for `maas.client.viscera`."""

from random import randrange
from unittest.mock import sentinel

from testtools.matchers import (
    Contains,
    ContainsAll,
    Equals,
    HasLength,
    Is,
    IsInstance,
    MatchesStructure,
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
    OriginBase,
)
from ... import (
    bones,
    viscera,
)
from ...testing import (
    make_name,
    make_name_without_spaces,
    TestCase,
)
from ...utils.tests.test_profiles import make_profile


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

    def test__init_insists_on_mapping(self):
        error = self.assertRaises(TypeError, Object, ["some", "items"])
        self.assertThat(str(error), Equals("data must be a mapping, not list"))

    def test__equal_when_data_matches(self):
        data = {"key": make_name("value")}
        object_a = Object(data)
        object_b = Object(data)
        self.assertThat(object_a, Equals(object_b))
        self.assertThat(object_b, Equals(object_a))

    def test__not_equal_when_types_different(self):
        # Even if one is a subclass of the other.
        data = {"key": make_name("value")}
        object_a = Object(data)
        object_b = type("Object", (Object,), {})(data)
        self.assertThat(object_a, Not(Equals(object_b)))
        self.assertThat(object_b, Not(Equals(object_a)))

    def test__string_representation_includes_field_values(self):

        class Example(Object):
            alice = ObjectField("alice")
            bob = ObjectField("bob")

        example = Example({
            "alice": make_name_without_spaces("alice"),
            "bob": make_name_without_spaces("bob"),
        })

        self.assertThat(repr(example), Equals(
            "<Example alice=%(alice)r bob=%(bob)r>" % example._data))

    def test__string_representation_can_be_limited_to_selected_fields(self):

        class Example(Object):
            alice = ObjectField("alice")
            bob = ObjectField("bob")

        example = Example({
            "alice": make_name_without_spaces("alice"),
            "bob": make_name_without_spaces("bob"),
        })

        # A string repr can be prepared using only the "alice" field.
        self.assertThat(
            example.__repr__(fields={"alice"}), Equals(
                "<Example alice=%(alice)r>" % example._data))

        # Fields are always displayed in a stable order though.
        self.assertThat(
            example.__repr__(fields=["bob", "alice"]), Equals(
                "<Example alice=%(alice)r bob=%(bob)r>" % example._data))


class TestObjectSet(TestCase):
    """Tests for `ObjectSet`."""

    def test__defines_slots(self):
        self.assertThat(
            ObjectSet.__slots__,
            Equals(("__weakref__", "_items")))

    def test__inherits_ObjectBasics(self):
        self.assertThat(ObjectSet.__mro__, Contains(ObjectBasics))

    def test__init_sets__items_from_sequence(self):
        items = [{"alice": make_name_without_spaces("alice")}]
        self.assertThat(ObjectSet(items)._items, Equals(items))

    def test__init_sets__items_from_iterable(self):
        items = [{"alice": make_name_without_spaces("alice")}]
        self.assertThat(ObjectSet(iter(items))._items, Equals(items))

    def test__init_rejects_mapping(self):
        error = self.assertRaises(TypeError, ObjectSet, {})
        self.assertThat(str(error), Equals(
            "data must be sequence-like, not dict"))

    def test__init_rejects_str(self):
        error = self.assertRaises(TypeError, ObjectSet, "")
        self.assertThat(str(error), Equals(
            "data must be sequence-like, not str"))

    def test__init_rejects_bytes(self):
        error = self.assertRaises(TypeError, ObjectSet, b"")
        self.assertThat(str(error), Equals(
            "data must be sequence-like, not bytes"))

    def test__init_rejects_non_iterable(self):
        error = self.assertRaises(TypeError, ObjectSet, 123)
        self.assertThat(str(error), Equals(
            "data must be sequence-like, not int"))

    def test__length_is_number_of_items(self):
        items = [0] * randrange(0, 100)
        objectset = ObjectSet(items)
        self.assertThat(objectset, HasLength(len(items)))

    def test__can_be_indexed(self):
        items = [make_name_without_spaces(str(index)) for index in range(5)]
        objectset = ObjectSet(items)
        for index, item in enumerate(items):
            self.assertThat(objectset[index], Equals(item))

    def test__can_be_sliced(self):
        items = [make_name_without_spaces(str(index)) for index in range(5)]
        objectset1 = ObjectSet(items)
        objectset2 = objectset1[1:3]
        self.assertThat(objectset2, IsInstance(ObjectSet))
        self.assertThat(list(objectset2), Equals(items[1:3]))

    def test__iteration_yield_items(self):
        items = [make_name_without_spaces(str(index)) for index in range(5)]
        objectset = ObjectSet(items)
        self.assertThat(list(objectset), Equals(items))

    def test__reversed_yields_items_in_reverse(self):
        items = [make_name_without_spaces(str(index)) for index in range(5)]
        objectset = ObjectSet(items)
        self.assertThat(list(reversed(objectset)), Equals(items[::-1]))

    def test__membership_can_be_tested(self):
        item1 = make_name_without_spaces("item")
        item2 = make_name_without_spaces("item")
        objectset = ObjectSet([item1])
        self.assertThat(objectset, Contains(item1))
        self.assertThat(objectset, Not(Contains(item2)))

    def test__equal_when_items_match(self):
        items = [{"key": make_name("value")}]
        objectset_a = ObjectSet(items)
        objectset_b = ObjectSet(items)
        self.assertThat(objectset_a, Equals(objectset_b))
        self.assertThat(objectset_b, Equals(objectset_a))

    def test__not_equal_when_types_different(self):
        # Even if one is a subclass of the other.
        items = [{"key": make_name("value")}]
        objectset_a = ObjectSet(items)
        objectset_b = type("ObjectSet", (ObjectSet,), {})(items)
        self.assertThat(objectset_a, Not(Equals(objectset_b)))
        self.assertThat(objectset_b, Not(Equals(objectset_a)))

    def test__string_representation_includes_length_and_items(self):

        class Example(Object):
            alice = ObjectField("alice")

        class ExampleSet(ObjectSet):
            pass

        example = ExampleSet([
            Example({"alice": "wonderland"}),
            Example({"alice": "cooper"}),
        ])

        self.assertThat(repr(example), Equals(
            "<ExampleSet length=2 items=["
            "<Example alice='wonderland'>, <Example alice='cooper'>"
            "]>"))


class TestObjectField(TestCase):
    """Tests for `ObjectField`."""

    def test__gets_sets_and_deletes_the_given_name_from_object(self):

        class Example(Object):
            alice = ObjectField("alice")

        example = Example({})

        # At first, referencing "alice" yields an exception.
        self.assertRaises(AttributeError, getattr, example, "alice")
        self.assertThat(example._data, Equals({}))

        # Setting "alice" stores the value in the object's _data dict.
        example.alice = sentinel.alice
        self.assertThat(example.alice, Is(sentinel.alice))
        self.assertThat(example._data, Equals({"alice": sentinel.alice}))

        # Deleting "alice" removes the value from the object's _data dict, and
        # referencing "alice" yields an exception.
        del example.alice
        self.assertRaises(AttributeError, getattr, example, "alice")
        self.assertThat(example._data, Equals({}))

    def test__default_is_returned_when_value_not_found_in_object(self):

        class Example(Object):
            alice = ObjectField("alice", default=sentinel.alice_default)

        example = Example({})

        # At first, referencing "alice" yields the default value.
        self.assertThat(example.alice, Is(sentinel.alice_default))
        self.assertThat(example._data, Equals({}))

        # Setting "alice" stores the value in the object's _data dict.
        example.alice = sentinel.alice
        self.assertThat(example, MatchesStructure(alice=Is(sentinel.alice)))
        self.assertThat(example._data, Equals({"alice": sentinel.alice}))

        # Deleting "alice" removes the value from the object's _data dict, and
        # referencing "alice" again yields the default value.
        del example.alice
        self.assertThat(example.alice, Is(sentinel.alice_default))
        self.assertThat(example._data, Equals({}))

    def test__readonly_prevents_setting_or_deleting(self):

        class Example(Object):
            alice = ObjectField("alice", readonly=True)

        example = Example({"alice": sentinel.in_wonderland})

        self.assertThat(example.alice, Is(sentinel.in_wonderland))
        self.assertRaises(AttributeError, setattr, example, "alice", 123)
        self.assertThat(example.alice, Is(sentinel.in_wonderland))
        self.assertRaises(AttributeError, delattr, example, "alice")
        self.assertThat(example.alice, Is(sentinel.in_wonderland))

    def test__conversion_and_validation_happens(self):

        class AliceField(ObjectField):
            """A most peculiar field."""

            def datum_to_value(self, instance, datum):
                return datum + instance.datum_to_value_delta

            def value_to_datum(self, instance, value):
                return value + instance.value_to_datum_delta

        class Example(Object):
            alice = AliceField("alice")
            # Deltas to apply to datums and values.
            datum_to_value_delta = 2
            value_to_datum_delta = 3

        example = Example({})
        example.alice = 0

        # value_to_datum_delta was added to the value we specified before
        # being stored in the object's _data dict.
        self.assertThat(example._data, Equals({"alice": 3}))

        # datum_to_value_delta is added to the datum in the object's _data
        # dict before being returned to us.
        self.assertThat(example.alice, Equals(5))

    def test__default_is_not_subject_to_conversion_or_validation(self):

        class AliceField(ObjectField):
            """Another most peculiar field."""

        class Example(Object):
            alice = AliceField("alice", default=sentinel.alice_default)

        example = Example({})

        # The default given is treated as a Python-side value rather than a
        # MAAS-side datum, so is not passed through datum_to_value (or
        # value_to_datum for that matter).
        self.assertThat(example.alice, Is(sentinel.alice_default))


class TestObjectFieldChecked(TestCase):
    """Tests for `ObjectField.Checked`."""

    def test__creates_subclass(self):
        field = ObjectField.Checked("alice")
        self.assertThat(type(field).__mro__, Contains(ObjectField))
        self.assertThat(type(field), Not(Is(ObjectField)))
        self.assertThat(
            type(field).__name__,
            Equals("ObjectField.Checked#alice"))

    def test__overrides_datum_to_value(self):
        add_one = lambda value: value + 1
        field = ObjectField.Checked("alice", datum_to_value=add_one)
        self.assertThat(field.datum_to_value(None, 1), Equals(2))

    def test__overrides_value_to_daturm(self):
        add_one = lambda value: value + 1
        field = ObjectField.Checked("alice", value_to_datum=add_one)
        self.assertThat(field.value_to_datum(None, 1), Equals(2))

    def test__works_in_place(self):

        # Deltas to apply to datums and values.
        datum_to_value_delta = 2
        value_to_datum_delta = 3

        class Example(Object):
            alice = ObjectField.Checked(
                "alice", (lambda datum: datum + datum_to_value_delta),
                (lambda value: value + value_to_datum_delta))

        example = Example({})
        example.alice = 0

        # value_to_datum_delta was added to the value we specified before
        # being stored in the object's _data dict.
        self.assertThat(example._data, Equals({"alice": 3}))

        # datum_to_value_delta is added to the datum in the object's _data
        # dict before being returned to us.
        self.assertThat(example.alice, Equals(5))


class TestOriginBase(TestCase):
    """Tests for `OriginBase`."""

    def test__session_is_underlying_session(self):
        profile = make_profile()
        session = bones.SessionAPI.fromProfile(profile)
        origin = OriginBase(session)
        self.assertThat(origin.session, Is(session))

    def test__session_is_read_only(self):
        profile = make_profile()
        session = bones.SessionAPI.fromProfile(profile)
        origin = OriginBase(session)
        self.assertRaises(AttributeError, setattr, origin, "session", None)
