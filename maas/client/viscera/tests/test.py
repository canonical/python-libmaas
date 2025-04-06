"""Tests for `maas.client.viscera`."""

from random import randrange, randint
from unittest.mock import call, Mock, sentinel

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
    check,
    dir_class,
    dir_instance,
    Disabled,
    Object,
    ObjectBasics,
    ObjectField,
    ObjectFieldRelated,
    ObjectFieldRelatedSet,
    ObjectMethod,
    ObjectSet,
    ObjectType,
    OriginBase,
)
from ... import bones, viscera
from ...errors import ObjectNotLoaded
from ...testing import AsyncCallableMock, make_name, make_name_without_spaces, TestCase
from ...utils.tests.test_profiles import make_profile


class TestDirClass(TestCase):
    """Tests for `dir_class`."""

    def test__includes_ObjectMethod_descriptors_with_class_methods(self):
        class Example:
            attribute = ObjectMethod(sentinel.function)

        self.assertThat(list(dir_class(Example)), Contains("attribute"))

    def test__excludes_ObjectMethod_descriptors_without_class_methods(self):
        class Example:
            attribute = ObjectMethod()

        self.assertThat(list(dir_class(Example)), Not(Contains("attribute")))

    def test__excludes_Disabled_class_descriptors(self):
        class Example:
            attribute = Disabled("foobar")

        self.assertThat(list(dir_class(Example)), Not(Contains("attribute")))

    def test__includes_other_class_attributes(self):
        class Example:
            alice = "is the first"
            bob = lambda self: "just bob"
            carol = classmethod(lambda cls: "carol")
            dave = property(lambda self: "dave or david")
            erin = staticmethod(lambda: "or eve?")

        self.assertThat(
            list(dir_class(Example)),
            ContainsAll(["alice", "bob", "carol", "dave", "erin"]),
        )

    def test__excludes_mro_metaclass_method(self):
        class Example:
            """Example class."""

        self.assertThat(list(dir_class(Example)), Not(Contains("mro")))

    def test__excludes_Disabled_metaclass_descriptors(self):
        class ExampleType(type):
            attribute = Disabled("foobar")

        class Example(metaclass=ExampleType):
            """Example class with metaclass."""

        self.assertThat(list(dir_class(Example)), Not(Contains("attribute")))

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
            ContainsAll(["alice", "bob", "carol", "dave", "erin"]),
        )


class TestDirInstance(TestCase):
    """Tests for `dir_instance`."""

    def test__includes_ObjectMethod_descriptors_with_instance_methods(self):
        class Example:
            attribute = ObjectMethod()
            attribute.instancemethod(sentinel.function)

        example = Example()

        self.assertThat(list(dir_instance(example)), Contains("attribute"))

    def test__excludes_ObjectMethod_descriptors_without_instance_methods(self):
        class Example:
            attribute = ObjectMethod()
            attribute.classmethod(sentinel.function)

        example = Example()

        self.assertThat(list(dir_instance(example)), Not(Contains("attribute")))

    def test__excludes_Disabled_class_descriptors(self):
        class Example:
            attribute = Disabled("foobar")

        example = Example()

        self.assertThat(list(dir_instance(example)), Not(Contains("attribute")))

    def test__excludes_class_methods(self):
        class Example:
            carol = classmethod(lambda cls: "carol")

        example = Example()

        self.assertThat(list(dir_instance(example)), Not(Contains("carol")))

    def test__excludes_static_methods(self):
        class Example:
            steve = staticmethod(lambda: "or eve?")

        example = Example()

        self.assertThat(list(dir_instance(example)), Not(Contains("steve")))

    def test__includes_other_class_attributes(self):
        class Example:
            alice = "is the first"
            bob = lambda self: "just bob"
            dave = property(lambda self: "or david")

        example = Example()

        self.assertThat(
            list(dir_instance(example)), ContainsAll(["alice", "bob", "dave"])
        )

    def test__excludes_instance_attributes(self):
        # In a bit of a departure, dir_instance(foo) will NOT return instance
        # attributes of foo. This is because object attributes in viscera
        # should be defined using descriptors (which are class attributes).

        class Example:
            """Example class."""

        example = Example()
        example.alice = 123

        self.assertThat(list(dir_instance(example)), Not(Contains(["alice"])))


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
            Equals(("__weakref__", "_data", "_orig_data", "_changed_data", "_loaded")),
        )

    def test__inherits_ObjectBasics(self):
        self.assertThat(Object.__mro__, Contains(ObjectBasics))

    def test__init_sets__data_and_loaded(self):
        data = {"alice": make_name_without_spaces("alice")}
        self.assertThat(Object(data)._data, Equals(data))
        self.assertTrue(Object(data)._loaded)

    def test__init_insists_on_mapping_when_no_pk(self):
        error = self.assertRaises(TypeError, Object, ["some", "items"])
        self.assertThat(str(error), Equals("data must be a mapping, not list"))

    def test__init_insists_on_complete_data(self):
        data = {"alice": make_name_without_spaces("alice"), "__incomplete__": True}
        error = self.assertRaises(ValueError, Object, data)
        self.assertThat(
            str(error),
            Equals("data cannot be incomplete without any primary keys defined"),
        )

    def test__init_takes_pk_when_defined(self):
        object_type = type("PKObject", (Object,), {"pk": ObjectField("pk_d", pk=True)})
        object_pk = randint(0, 20)
        object_a = object_type(object_pk)
        self.assertThat(object_a._data, Equals({"pk_d": object_pk}))
        self.assertThat(object_a.pk, Equals(object_pk))
        self.assertFalse(object_a._loaded)

    def test__init_takes_pk_in_mapping_when_defined(self):
        object_type = type("PKObject", (Object,), {"pk": ObjectField("pk_d", pk=True)})
        object_pk = randint(0, 20)
        object_a = object_type({"pk_d": object_pk, "__incomplete__": True})
        self.assertThat(object_a._data, Equals({"pk_d": object_pk}))
        self.assertThat(object_a.pk, Equals(object_pk))
        self.assertFalse(object_a._loaded)

    def test__init_takes_alt_pk_in_mapping_when_defined(self):
        object_type = type(
            "PKObject",
            (Object,),
            {
                "pk": ObjectField("pk_d", pk=True),
                "alt_pk": ObjectField("alt_pk_d", alt_pk=True),
            },
        )
        object_alt_pk = randint(0, 20)
        object_a = object_type({"alt_pk_d": object_alt_pk, "__incomplete__": True})
        self.assertThat(object_a._data, Equals({"alt_pk_d": object_alt_pk}))
        self.assertThat(object_a.alt_pk, Equals(object_alt_pk))
        self.assertFalse(object_a._loaded)

    def test__init_validates_pk_when_defined(self):
        object_type = type(
            "PKObject",
            (Object,),
            {"pk": ObjectField.Checked("pk_d", check(int), pk=True)},
        )
        error = self.assertRaises(TypeError, object_type, "not int")
        self.assertThat(str(error), Equals("'not int' is not of type %r" % int))

    def test__init_validates_pk_in_mapping_when_defined(self):
        object_type = type(
            "PKObject",
            (Object,),
            {"pk": ObjectField.Checked("pk_d", check(int), pk=True)},
        )
        error = self.assertRaises(
            TypeError, object_type, {"pk_d": "not int", "__incomplete__": True}
        )
        self.assertThat(str(error), Equals("'not int' is not of type %r" % int))

    def test__init_validates_alt_pk_in_mapping_when_defined(self):
        object_type = type(
            "PKObject",
            (Object,),
            {
                "pk": ObjectField.Checked("pk_d", check(int), pk=True),
                "alt_pk": ObjectField.Checked("alt_pk_d", check(int), alt_pk=True),
            },
        )
        error = self.assertRaises(
            TypeError, object_type, {"alt_pk_d": "not int", "__incomplete__": True}
        )
        self.assertThat(str(error), Equals("'not int' is not of type %r" % int))

    def test__init_doesnt_allow_multiple_pk_True(self):
        object_type = type(
            "PKObject",
            (Object,),
            {
                "pk1": ObjectField.Checked("pk_1", check(int), pk=True),
                "pk2": ObjectField.Checked("pk_2", check(int), pk=True),
            },
        )
        error = self.assertRaises(AttributeError, object_type, [0, 1])
        self.assertThat(
            str(error),
            Equals("more than one field is marked as unique " "primary key: pk1, pk2"),
        )

    def test__init_allows_mapping_when_multiple_pks(self):
        object_type = type(
            "PKObject",
            (Object,),
            {
                "pk1": ObjectField.Checked("pk_1", check(int), pk=0),
                "pk2": ObjectField.Checked("pk_2", check(int), pk=1),
            },
        )
        object_pk_1 = randint(0, 20)
        object_pk_2 = randint(0, 20)
        object_a = object_type(
            {"pk_1": object_pk_1, "pk_2": object_pk_2, "__incomplete__": True}
        )
        self.assertThat(
            object_a._data, Equals({"pk_1": object_pk_1, "pk_2": object_pk_2})
        )
        self.assertThat(object_a.pk1, Equals(object_pk_1))
        self.assertThat(object_a.pk2, Equals(object_pk_2))
        self.assertFalse(object_a._loaded)

    def test__init_allows_mapping_when_multiple_alt_pks(self):
        object_type = type(
            "PKObject",
            (Object,),
            {
                "pk1": ObjectField.Checked("pk_1", check(int), pk=0),
                "pk2": ObjectField.Checked("pk_2", check(int), pk=1),
                "alt_pk1": ObjectField.Checked("alt_pk_1", check(int), alt_pk=0),
                "alt_pk2": ObjectField.Checked("alt_pk_2", check(int), alt_pk=1),
            },
        )
        object_alt_pk_1 = randint(0, 20)
        object_alt_pk_2 = randint(0, 20)
        object_a = object_type(
            {
                "alt_pk_1": object_alt_pk_1,
                "alt_pk_2": object_alt_pk_2,
                "__incomplete__": True,
            }
        )
        self.assertThat(
            object_a._data,
            Equals({"alt_pk_1": object_alt_pk_1, "alt_pk_2": object_alt_pk_2}),
        )
        self.assertThat(object_a.alt_pk1, Equals(object_alt_pk_1))
        self.assertThat(object_a.alt_pk2, Equals(object_alt_pk_2))
        self.assertFalse(object_a._loaded)

    def test__init_allows_sequence_when_multiple_pks(self):
        object_type = type(
            "PKObject",
            (Object,),
            {
                "pk1": ObjectField.Checked("pk_1", check(int), pk=0),
                "pk2": ObjectField.Checked("pk_2", check(int), pk=1),
            },
        )
        object_pk_1 = randint(0, 20)
        object_pk_2 = randint(0, 20)
        object_a = object_type([object_pk_1, object_pk_2])
        self.assertThat(
            object_a._data, Equals({"pk_1": object_pk_1, "pk_2": object_pk_2})
        )
        self.assertThat(object_a.pk1, Equals(object_pk_1))
        self.assertThat(object_a.pk2, Equals(object_pk_2))
        self.assertFalse(object_a._loaded)

    def test__init_requires_mapping_or_sequence_when_multiple_pks(self):
        object_type = type(
            "PKObject",
            (Object,),
            {
                "pk1": ObjectField.Checked("pk_1", check(int), pk=0),
                "pk2": ObjectField.Checked("pk_2", check(int), pk=1),
            },
        )
        error = self.assertRaises(TypeError, object_type, 0)
        self.assertThat(
            str(error), Equals("data must be a mapping or a sequence, not int")
        )

    def test__init_validates_property_when_multiple_pks_mapping(self):
        object_type = type(
            "PKObject",
            (Object,),
            {
                "pk1": ObjectField.Checked("pk_1", check(int), pk=0),
                "pk2": ObjectField.Checked("pk_2", check(int), pk=1),
            },
        )
        error = self.assertRaises(
            TypeError, object_type, {"pk_1": 0, "pk_2": "bad", "__incomplete__": True}
        )
        self.assertThat(str(error), Equals("'bad' is not of type %r" % int))

    def test__init_validates_property_when_multiple_alt_pks_mapping(self):
        object_type = type(
            "PKObject",
            (Object,),
            {
                "pk1": ObjectField.Checked("pk_1", check(int), pk=0),
                "pk2": ObjectField.Checked("pk_2", check(int), pk=1),
                "alt_pk1": ObjectField.Checked("alt_pk_1", check(int), alt_pk=0),
                "alt_pk2": ObjectField.Checked("alt_pk_2", check(int), alt_pk=1),
            },
        )
        error = self.assertRaises(
            TypeError,
            object_type,
            {"alt_pk_1": 0, "alt_pk_2": "bad", "__incomplete__": True},
        )
        self.assertThat(str(error), Equals("'bad' is not of type %r" % int))

    def test__init_validates_property_when_multiple_pks_sequence(self):
        object_type = type(
            "PKObject",
            (Object,),
            {
                "pk1": ObjectField.Checked("pk_1", check(int), pk=0),
                "pk2": ObjectField.Checked("pk_2", check(int), pk=1),
            },
        )
        error = self.assertRaises(TypeError, object_type, [0, "bad"])
        self.assertThat(str(error), Equals("'bad' is not of type %r" % int))

    def test__loaded(self):
        object_a = Object({})
        self.assertTrue(object_a.loaded)
        object_a._loaded = False
        self.assertFalse(object_a.loaded)

    def test__cannot_access_attributes_when_unloaded(self):
        object_type = type(
            "PKObject",
            (Object,),
            {"pk": ObjectField("pk_d", pk=True), "name": ObjectField("name")},
        )
        object_pk = randint(0, 20)
        object_a = object_type(object_pk)
        object_a._data["name"] = make_name("name")
        self.assertFalse(object_a.loaded)
        error = self.assertRaises(ObjectNotLoaded, getattr, object_a, "name")
        self.assertThat(
            str(error), Equals("cannot access attribute 'name' of object 'PKObject'")
        )

    def test__can_access_pk_attributes_when_unloaded(self):
        object_type = type(
            "PKObject",
            (Object,),
            {"pk": ObjectField("pk_d", pk=True), "name": ObjectField("name")},
        )
        object_pk = randint(0, 20)
        object_a = object_type(object_pk)
        self.assertFalse(object_a.loaded)
        self.assertEquals(object_pk, object_a.pk)

    def test__can_access_alt_pk_attributes_when_unloaded(self):
        object_type = type(
            "PKObject",
            (Object,),
            {
                "pk": ObjectField("pk_d", pk=True),
                "alt_pk": ObjectField("alt_pk_d", alt_pk=True),
                "name": ObjectField("name"),
            },
        )
        object_alt_pk = randint(0, 20)
        object_a = object_type({"alt_pk_d": object_alt_pk, "__incomplete__": True})
        self.assertFalse(object_a.loaded)
        self.assertEquals(object_alt_pk, object_a.alt_pk)

    def test__can_access_attributes_when_loaded(self):
        object_type = type(
            "PKObject",
            (Object,),
            {"pk": ObjectField("pk_d", pk=True), "name": ObjectField("name")},
        )
        object_pk = randint(0, 20)
        object_name = make_name("name")
        object_a = object_type({"pk_d": object_pk, "name": object_name})
        self.assertTrue(object_a.loaded)
        self.assertEquals(object_name, object_a.name)

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

        example = Example(
            {
                "alice": make_name_without_spaces("alice"),
                "bob": make_name_without_spaces("bob"),
            }
        )

        self.assertThat(
            repr(example),
            Equals("<Example alice=%(alice)r bob=%(bob)r>" % example._data),
        )

    def test__string_representation_can_be_limited_to_selected_fields(self):
        class Example(Object):
            alice = ObjectField("alice")
            bob = ObjectField("bob")

        example = Example(
            {
                "alice": make_name_without_spaces("alice"),
                "bob": make_name_without_spaces("bob"),
            }
        )

        # A string repr can be prepared using only the "alice" field.
        self.assertThat(
            example.__repr__(fields={"alice"}),
            Equals("<Example alice=%(alice)r>" % example._data),
        )

        # Fields are always displayed in a stable order though.
        self.assertThat(
            example.__repr__(fields=["bob", "alice"]),
            Equals("<Example alice=%(alice)r bob=%(bob)r>" % example._data),
        )

    def test_refresh_raises_AttributeError_when_no_read_defined(self):
        object_a = Object({})
        error = self.assertRaises(AttributeError, object_a.refresh)
        self.assertThat(str(error), Equals("'Object' object doesn't support refresh."))

    def test_refresh_with_one_pk(self):
        object_type = type("PKObject", (Object,), {"pk": ObjectField("pk_d", pk=True)})
        object_pk = randint(0, 20)
        new_data = {"pk_d": object_pk, "other": randint(0, 20)}
        mock_read = AsyncCallableMock(return_value=object_type(new_data))
        self.patch(object_type, "read", mock_read)
        object_a = object_type(object_pk)
        self.assertFalse(object_a.loaded)
        object_a.refresh()
        self.assertTrue(object_a.loaded)
        self.assertThat(object_a._data, Equals(new_data))
        self.assertThat(object_a._orig_data, Equals(new_data))
        self.assertThat(object_a._orig_data, Not(Is(object_a._data)))
        self.assertThat(object_a._changed_data, Equals({}))
        self.assertThat(mock_read.call_args_list, Equals([call(object_pk)]))

    def test_refresh_with_one_alt_pk(self):
        object_type = type(
            "PKObject",
            (Object,),
            {
                "pk": ObjectField("pk_d", pk=True),
                "alt_pk": ObjectField("alt_pk_d", alt_pk=True),
            },
        )
        object_pk = randint(0, 20)
        object_alt_pk = randint(0, 20)
        new_data = {
            "pk_d": object_pk,
            "alt_pk_d": object_alt_pk,
            "other": randint(0, 20),
        }
        mock_read = AsyncCallableMock(return_value=object_type(new_data))
        self.patch(object_type, "read", mock_read)
        object_a = object_type({"alt_pk_d": object_alt_pk, "__incomplete__": True})
        self.assertFalse(object_a.loaded)
        object_a.refresh()
        self.assertTrue(object_a.loaded)
        self.assertThat(object_a._data, Equals(new_data))
        self.assertThat(object_a._orig_data, Equals(new_data))
        self.assertThat(object_a._orig_data, Not(Is(object_a._data)))
        self.assertThat(object_a._changed_data, Equals({}))
        self.assertThat(mock_read.call_args_list, Equals([call(object_alt_pk)]))

    def test_refresh_with_multiple_pk(self):
        object_type = type(
            "PKObject",
            (Object,),
            {"pk1": ObjectField("pk_1", pk=0), "pk2": ObjectField("pk_2", pk=1)},
        )
        object_pk_1 = randint(0, 20)
        object_pk_2 = randint(0, 20)
        new_data = {"pk_1": object_pk_1, "pk_2": object_pk_2, "other": randint(0, 20)}
        mock_read = AsyncCallableMock(return_value=object_type(new_data))
        self.patch(object_type, "read", mock_read)
        object_a = object_type([object_pk_1, object_pk_2])
        self.assertFalse(object_a.loaded)
        object_a.refresh()
        self.assertTrue(object_a.loaded)
        self.assertThat(object_a._data, Equals(new_data))
        self.assertThat(object_a._orig_data, Equals(new_data))
        self.assertThat(object_a._orig_data, Not(Is(new_data)))
        self.assertThat(object_a._changed_data, Equals({}))
        self.assertThat(
            mock_read.call_args_list, Equals([call(object_pk_1, object_pk_2)])
        )

    def test_refresh_with_multiple_alt_pk(self):
        object_type = type(
            "PKObject",
            (Object,),
            {
                "pk1": ObjectField("pk_1", pk=0),
                "pk2": ObjectField("pk_2", pk=1),
                "alt_pk1": ObjectField("alt_pk_1", alt_pk=0),
                "alt_pk2": ObjectField("alt_pk_2", alt_pk=1),
            },
        )
        object_pk_1 = randint(0, 20)
        object_pk_2 = randint(0, 20)
        object_alt_pk_1 = randint(0, 20)
        object_alt_pk_2 = randint(0, 20)
        new_data = {
            "pk_1": object_pk_1,
            "pk_2": object_pk_2,
            "alt_pk_1": object_alt_pk_1,
            "alt_pk_2": object_alt_pk_2,
            "other": randint(0, 20),
        }
        mock_read = AsyncCallableMock(return_value=object_type(new_data))
        self.patch(object_type, "read", mock_read)
        object_a = object_type(
            {
                "alt_pk_1": object_alt_pk_1,
                "alt_pk_2": object_alt_pk_2,
                "__incomplete__": True,
            }
        )
        self.assertFalse(object_a.loaded)
        object_a.refresh()
        self.assertTrue(object_a.loaded)
        self.assertThat(object_a._data, Equals(new_data))
        self.assertThat(object_a._orig_data, Equals(new_data))
        self.assertThat(object_a._orig_data, Not(Is(new_data)))
        self.assertThat(object_a._changed_data, Equals({}))
        self.assertThat(
            mock_read.call_args_list, Equals([call(object_alt_pk_1, object_alt_pk_2)])
        )

    def test_refresh_raises_AttributeError_when_no_pk_fields(self):
        object_type = type("PKObject", (Object,), {})
        mock_read = AsyncCallableMock(return_value=object_type({}))
        self.patch(object_type, "read", mock_read)
        object_a = object_type({})
        error = self.assertRaises(AttributeError, object_a.refresh)
        self.assertThat(
            str(error),
            Equals("unable to perform 'refresh' no primary key fields defined."),
        )

    def test_refresh_raises_TypeError_on_mismatch(self):
        object_type = type("PKObject", (Object,), {"pk": ObjectField("pk_d", pk=True)})
        mock_read = AsyncCallableMock(return_value=Object({}))
        self.patch(object_type, "read", mock_read)
        object_a = object_type({"pk_d": 0})
        error = self.assertRaises(TypeError, object_a.refresh)
        self.assertThat(
            str(error),
            Equals("result of 'PKObject.read' must be 'PKObject', not 'Object'"),
        )

    def test_save_raises_AttributeError_when_handler_has_no_update(self):
        object_type = type("NotSaveableObject", (Object,), {"_handler": object()})
        error = self.assertRaises(AttributeError, object_type({}).save)
        self.assertThat(
            str(error), Equals("'NotSaveableObject' object doesn't support save.")
        )

    def test_save_does_nothing_when_nothing_changed(self):
        handler = Mock()
        handler.update = AsyncCallableMock(return_value={})
        object_type = type(
            "SaveableObject",
            (Object,),
            {"_handler": handler, "name": ObjectField("name")},
        )
        object_a = object_type({})
        object_a.save()
        self.assertThat(handler.update.call_count, Equals(0))

    def test_save_calls_update_on_handler_with_params(self):
        object_id = randint(0, 10)
        saved_name = make_name("name")
        updated_data = {"id": object_id, "name": saved_name}
        handler = Mock()
        handler.params = ["id"]
        handler.update = AsyncCallableMock(return_value=updated_data)
        object_type = type(
            "SaveableObject",
            (Object,),
            {"_handler": handler, "name": ObjectField("name")},
        )
        object_a = object_type({"id": object_id})
        new_name = make_name("new")
        object_a.name = new_name
        object_a.save()
        self.assertThat(
            handler.update.call_args_list, Equals([call(id=object_id, name=new_name)])
        )
        self.assertThat(object_a._data, Equals(updated_data))
        self.assertThat(object_a._orig_data, Equals(updated_data))
        self.assertThat(object_a._orig_data, Not(Is(object_a._data)))
        self.assertThat(object_a._changed_data, Equals({}))


class TestObjectSet(TestCase):
    """Tests for `ObjectSet`."""

    def test__defines_slots(self):
        self.assertThat(ObjectSet.__slots__, Equals(("__weakref__", "_items")))

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
        self.assertThat(str(error), Equals("data must be sequence-like, not dict"))

    def test__init_rejects_str(self):
        error = self.assertRaises(TypeError, ObjectSet, "")
        self.assertThat(str(error), Equals("data must be sequence-like, not str"))

    def test__init_rejects_bytes(self):
        error = self.assertRaises(TypeError, ObjectSet, b"")
        self.assertThat(str(error), Equals("data must be sequence-like, not bytes"))

    def test__init_rejects_non_iterable(self):
        error = self.assertRaises(TypeError, ObjectSet, 123)
        self.assertThat(str(error), Equals("data must be sequence-like, not int"))

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

        example = ExampleSet(
            [Example({"alice": "wonderland"}), Example({"alice": "cooper"})]
        )

        self.assertThat(
            repr(example),
            Equals(
                "<ExampleSet length=2 items=["
                "<Example alice='wonderland'>, <Example alice='cooper'>"
                "]>"
            ),
        )


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

    def test__set_new_value_is_set_in_changed(self):
        class AliceField(ObjectField):
            """Another most peculiar field."""

        class Example(Object):
            alice = AliceField("alice")

        example = Example({})

        example.alice = sentinel.alice
        self.assertThat(example._changed_data, Equals({"alice": sentinel.alice}))

    def test__set_update_value_is_set_in_changed(self):
        class AliceField(ObjectField):
            """Another most peculiar field."""

        class Example(Object):
            alice = AliceField("alice")

        example = Example({"alice": sentinel.alice})

        example.alice = sentinel.new_alice
        self.assertThat(example._changed_data, Equals({"alice": sentinel.new_alice}))

    def test__set_update_value_replaces_changed(self):
        class AliceField(ObjectField):
            """Another most peculiar field."""

        class Example(Object):
            alice = AliceField("alice")

        example = Example({"alice": sentinel.alice})

        example.alice = sentinel.new_alice
        self.assertThat(example._changed_data, Equals({"alice": sentinel.new_alice}))
        example.alice = sentinel.newer_alice
        self.assertThat(example._changed_data, Equals({"alice": sentinel.newer_alice}))

    def test__set_update_value_to_orig_removes_from_changed(self):
        class AliceField(ObjectField):
            """Another most peculiar field."""

        class Example(Object):
            alice = AliceField("alice")

        alice = make_name_without_spaces("alice")
        new_alice = make_name_without_spaces("alice")
        example = Example({"alice": alice})

        example.alice = new_alice
        self.assertThat(example._changed_data, Equals({"alice": new_alice}))
        example.alice = alice
        self.assertThat(example._changed_data, Equals({}))

    def test__delete_marks_field_deleted(self):
        class AliceField(ObjectField):
            """Another most peculiar field."""

        class Example(Object):
            alice = AliceField("alice")

        example = Example({"alice": sentinel.alice})

        del example.alice
        self.assertThat(example._changed_data, Equals({"alice": None}))

    def test__set_deleted_field_sets_changed(self):
        class AliceField(ObjectField):
            """Another most peculiar field."""

        class Example(Object):
            alice = AliceField("alice")

        alice = make_name_without_spaces("alice")
        new_alice = make_name_without_spaces("alice")
        example = Example({"alice": alice})

        del example.alice
        example.alice = new_alice
        self.assertThat(example._changed_data, Equals({"alice": new_alice}))
        example.alice = alice
        self.assertThat(example._changed_data, Equals({}))


class TestObjectFieldChecked(TestCase):
    """Tests for `ObjectField.Checked`."""

    def test__creates_subclass(self):
        field = ObjectField.Checked("alice")
        self.assertThat(type(field).__mro__, Contains(ObjectField))
        self.assertThat(type(field), Not(Is(ObjectField)))
        self.assertThat(type(field).__name__, Equals("ObjectField.Checked#alice"))

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
                "alice",
                (lambda datum: datum + datum_to_value_delta),
                (lambda value: value + value_to_datum_delta),
            )

        example = Example({})
        example.alice = 0

        # value_to_datum_delta was added to the value we specified before
        # being stored in the object's _data dict.
        self.assertThat(example._data, Equals({"alice": 3}))

        # datum_to_value_delta is added to the datum in the object's _data
        # dict before being returned to us.
        self.assertThat(example.alice, Equals(5))


class TestObjectFieldRelated(TestCase):
    """Tests for `ObjectFieldRelated`."""

    def test__init__requires_str_or_Object_class(self):
        self.assertRaises(TypeError, ObjectFieldRelated, "name", 0)
        self.assertRaises(TypeError, ObjectFieldRelated, "name", object)
        # Doesn't raise error.
        ObjectFieldRelated("name", "class")
        ObjectFieldRelated("name", Object)

    def test_datum_to_value_returns_None_on_None(self):
        self.assertIsNone(
            ObjectFieldRelated("name", "class").datum_to_value(object(), None)
        )

    def test_datum_to_value_converts_to_bound_class(self):
        rel_object_type = type(
            "RelObject", (Object,), {"pk": ObjectField("pk_d", pk=True)}
        )
        origin = Mock()
        origin.RelObject = rel_object_type
        instance = type("InstObject", (Object,), {"_origin": origin})({})
        field = ObjectFieldRelated("related_id", "RelObject")
        rel_id = randint(0, 20)
        rel_object = field.datum_to_value(instance, rel_id)
        self.assertIsInstance(rel_object, rel_object_type)
        self.assertFalse(rel_object.loaded)
        self.assertThat(
            rel_object._data, Equals({"instobject": instance, "pk_d": rel_id})
        )

    def test_datum_to_value_uses_reverse_name(self):
        rel_object_type = type(
            "RelObject", (Object,), {"pk": ObjectField("pk_d", pk=True)}
        )
        origin = Mock()
        origin.RelObject = rel_object_type
        instance = type("Object", (Object,), {"_origin": origin})({})
        field = ObjectFieldRelated("related_id", "RelObject", reverse="reverse")
        rel_id = randint(0, 20)
        rel_object = field.datum_to_value(instance, rel_id)
        self.assertIsInstance(rel_object, rel_object_type)
        self.assertFalse(rel_object.loaded)
        self.assertThat(rel_object._data, Equals({"reverse": instance, "pk_d": rel_id}))

    def test_datum_to_value_doesnt_include_reverse(self):
        rel_object_type = type(
            "RelObject", (Object,), {"pk": ObjectField("pk_d", pk=True)}
        )
        origin = Mock()
        origin.RelObject = rel_object_type
        instance = type("Object", (Object,), {"_origin": origin})({})
        field = ObjectFieldRelated("related_id", "RelObject", reverse=None)
        rel_id = randint(0, 20)
        rel_object = field.datum_to_value(instance, rel_id)
        self.assertIsInstance(rel_object, rel_object_type)
        self.assertFalse(rel_object.loaded)
        self.assertThat(rel_object._data, Equals({"pk_d": rel_id}))

    def test_value_to_datum_returns_None_on_None(self):
        self.assertIsNone(
            ObjectFieldRelated("name", "class").value_to_datum(object(), None)
        )

    def test_value_to_datum_requires_same_class(self):
        rel_object_type = type(
            "RelObject", (Object,), {"pk": ObjectField("pk_d", pk=True)}
        )
        origin = Mock()
        origin.RelObject = rel_object_type
        instance = type("Object", (Object,), {"_origin": origin})({})
        field = ObjectFieldRelated("related_id", "RelObject")
        error = self.assertRaises(TypeError, field.value_to_datum, instance, object())
        self.assertThat(str(error), Equals("must be RelObject, not object"))

    def test_value_to_datum_with_one_primary_key(self):
        rel_object_type = type(
            "RelObject", (Object,), {"pk": ObjectField("pk_d", pk=True)}
        )
        origin = Mock()
        origin.RelObject = rel_object_type
        instance = type("Object", (Object,), {"_origin": origin})({})
        field = ObjectFieldRelated("related_id", "RelObject")
        rel_id = randint(0, 20)
        rel_object = rel_object_type(rel_id)
        self.assertThat(field.value_to_datum(instance, rel_object), Equals(rel_id))

    def test_value_to_datum_with_multiple_primary_keys(self):
        rel_object_type = type(
            "RelObject",
            (Object,),
            {"pk1": ObjectField("pk_1", pk=0), "pk2": ObjectField("pk_2", pk=1)},
        )
        origin = Mock()
        origin.RelObject = rel_object_type
        instance = type("Object", (Object,), {"_origin": origin})({})
        field = ObjectFieldRelated("related", "RelObject")
        rel_1 = randint(0, 20)
        rel_2 = randint(0, 20)
        rel_object = rel_object_type((rel_1, rel_2))
        self.assertThat(
            field.value_to_datum(instance, rel_object), Equals((rel_1, rel_2))
        )

    def test_value_to_datum_raises_error_when_no_primary_keys(self):
        rel_object_type = type("RelObject", (Object,), {"pk": ObjectField("pk_d")})
        origin = Mock()
        origin.RelObject = rel_object_type
        instance = type("Object", (Object,), {"_origin": origin})({})
        field = ObjectFieldRelated("related_id", "RelObject")
        rel_id = randint(0, 20)
        rel_object = rel_object_type({"pk_d": rel_id})
        error = self.assertRaises(
            AttributeError, field.value_to_datum, instance, rel_object
        )
        self.assertThat(
            str(error),
            Equals(
                "unable to perform set object no primary key "
                "fields defined for RelObject"
            ),
        )


class TestObjectFieldRelatedSet(TestCase):
    """Tests for `ObjectFieldRelatedSet`."""

    def test__init__requires_str_or_Object_class(self):
        self.assertRaises(TypeError, ObjectFieldRelatedSet, "name", 0)
        self.assertRaises(TypeError, ObjectFieldRelatedSet, "name", object)
        # Doesn't raise error.
        ObjectFieldRelatedSet("name", "class")
        ObjectFieldRelatedSet("name", ObjectSet)

    def test_datum_to_value_returns_empty_list_on_None(self):
        self.assertEquals(
            ObjectFieldRelatedSet("name", "class").datum_to_value(object(), None), []
        )

    def test_datum_must_be_a_sequence(self):
        field = ObjectFieldRelatedSet("name", "class")
        error = self.assertRaises(TypeError, field.datum_to_value, object(), 0)
        self.assertThat(str(error), Equals("datum must be a sequence, not int"))

    def test_datum_to_value_converts_to_set_of_bound_class(self):
        rel_object_type = type(
            "RelObject", (Object,), {"pk": ObjectField("pk_d", pk=True)}
        )
        rel_object_set_type = type(
            "RelObjectSet", (ObjectSet,), {"_object": rel_object_type}
        )
        origin = Mock()
        origin.RelObjectSet = rel_object_set_type
        instance = type("InstObject", (Object,), {"_origin": origin})({})
        field = ObjectFieldRelatedSet("related_ids", "RelObjectSet")
        rel_ids = range(5)
        rel_object_set = field.datum_to_value(instance, rel_ids)
        self.assertEquals(5, len(rel_object_set))
        self.assertIsInstance(rel_object_set[0], rel_object_type)
        self.assertFalse(rel_object_set[0].loaded)
        self.assertThat(
            rel_object_set[0]._data,
            Equals({"instobject": instance, "pk_d": rel_ids[0]}),
        )

    def test_datum_to_value_uses_reverse_name(self):
        rel_object_type = type(
            "RelObject", (Object,), {"pk": ObjectField("pk_d", pk=True)}
        )
        rel_object_set_type = type(
            "RelObjectSet", (ObjectSet,), {"_object": rel_object_type}
        )
        origin = Mock()
        origin.RelObjectSet = rel_object_set_type
        instance = type("InstObject", (Object,), {"_origin": origin})({})
        field = ObjectFieldRelatedSet("related_ids", "RelObjectSet", reverse="reverse")
        rel_ids = range(5)
        rel_object_set = field.datum_to_value(instance, rel_ids)
        self.assertEquals(5, len(rel_object_set))
        self.assertIsInstance(rel_object_set[0], rel_object_type)
        self.assertFalse(rel_object_set[0].loaded)
        self.assertThat(
            rel_object_set[0]._data, Equals({"reverse": instance, "pk_d": rel_ids[0]})
        )

    def test_datum_to_value_doesnt_include_reverse(self):
        rel_object_type = type(
            "RelObject", (Object,), {"pk": ObjectField("pk_d", pk=True)}
        )
        rel_object_set_type = type(
            "RelObjectSet", (ObjectSet,), {"_object": rel_object_type}
        )
        origin = Mock()
        origin.RelObjectSet = rel_object_set_type
        instance = type("InstObject", (Object,), {"_origin": origin})({})
        field = ObjectFieldRelatedSet("related_ids", "RelObjectSet", reverse=None)
        rel_ids = range(5)
        rel_object_set = field.datum_to_value(instance, rel_ids)
        self.assertEquals(5, len(rel_object_set))
        self.assertIsInstance(rel_object_set[0], rel_object_type)
        self.assertFalse(rel_object_set[0].loaded)
        self.assertThat(rel_object_set[0]._data, Equals({"pk_d": rel_ids[0]}))

    def test_datum_to_value_wraps_managed_create(self):
        rel_object_type = type(
            "RelObject", (Object,), {"pk": ObjectField("pk_d", pk=True)}
        )
        create_mock = AsyncCallableMock(return_value=rel_object_type({}))
        rel_object_set_type = type(
            "RelObjectSet",
            (ObjectSet,),
            {"_object": rel_object_type, "create": create_mock},
        )
        origin = Mock()
        origin.RelObjectSet = rel_object_set_type
        instance = type("InstObject", (Object,), {"_origin": origin})(
            {"related_ids": []}
        )
        field = ObjectFieldRelatedSet("related_ids", "RelObjectSet")
        rel_ids = range(5)
        rel_object_set = field.datum_to_value(instance, rel_ids)
        rel_object_set.create()
        self.assertEquals(
            "RelObjectSet.Managed#InstObject", type(rel_object_set).__name__
        )
        self.assertThat(create_mock.call_args_list, Equals([call(instance)]))


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
