"""Tests for `alburnum.maas.utils.profiles`."""

__all__ = []

import contextlib
import os
import os.path
import sqlite3

from alburnum.maas.testing import (
    make_name_without_spaces,
    TestCase,
)
from alburnum.maas.utils.profiles import (
    Profile,
    ProfileConfig,
)
from testtools.matchers import (
    Equals,
    Is,
    Not,
)
from twisted.python.filepath import FilePath

from .test_auth import make_credentials


def make_profile():
    return Profile(
        name=make_name_without_spaces("name"), url="http://example.com:5240/",
        credentials=make_credentials(), description={"resources": []},
        something=make_name_without_spaces("something"))


class TestProfile(TestCase):

    def test__instances_are_immutable(self):
        profile = make_profile()
        self.assertRaises(AttributeError, setattr, profile, "name", "foo")
        self.assertRaises(AttributeError, setattr, profile, "uri", "foo")
        self.assertRaises(AttributeError, setattr, profile, "bar", "foo")

    def test__replace_returns_a_new_profile(self):
        profile1 = make_profile()
        profile2 = profile1.replace()
        self.assertThat(profile2, Not(Is(profile1)))
        self.assertThat(profile2.name, Equals(profile1.name))
        self.assertThat(profile2.url, Equals(profile1.url))
        self.assertThat(profile2.credentials, Equals(profile1.credentials))
        self.assertThat(profile2.description, Equals(profile1.description))
        self.assertThat(profile2.other, Equals(profile1.other))

    def test__replace_returns_a_new_profile_with_modifications(self):
        profile1 = make_profile()
        profile2 = profile1.replace(
            name=profile1.name + "basil", hello="world")
        self.assertThat(profile2.name, Equals(profile1.name + "basil"))
        self.assertThat(profile2.other, Equals(
            dict(profile1.other, hello="world")))

    def test__dump_returns_dict_with_all_state(self):
        profile = make_profile()
        self.assertThat(profile.dump(), Equals({
            "name": profile.name,
            "url": profile.url,
            "credentials": profile.credentials,
            "description": profile.description,
            "something": profile.other["something"],
        }))

    def test__representation(self):
        profile = make_profile()
        self.assertThat(repr(profile), Equals(
            "<Profile {0.name} {0.url}>".format(profile)))

    def test__representation_of_anonymous_profile(self):
        profile = make_profile().replace(credentials=None)
        self.assertThat(repr(profile), Equals(
            "<Profile {0.name} (anonymous) {0.url}>".format(profile)))


class TestProfileConfig(TestCase):
    """Tests for `ProfileConfig`."""

    def test_init(self):
        database = sqlite3.connect(":memory:")
        config = ProfileConfig(database)
        with config.cursor() as cursor:
            # The profiles table has been created.
            self.assertEqual(
                cursor.execute(
                    "SELECT COUNT(*) FROM sqlite_master"
                    " WHERE type = 'table'"
                    "   AND name = 'profiles'").fetchone(),
                (1,))

    def test_profiles_pristine(self):
        # A pristine configuration has no profiles.
        database = sqlite3.connect(":memory:")
        config = ProfileConfig(database)
        self.assertSetEqual(set(), set(config))

    def test_saving_and_loading_profile(self):
        database = sqlite3.connect(":memory:")
        config = ProfileConfig(database)
        profile = make_profile()
        config.save(profile)
        self.assertEqual({profile.name}, set(config))
        self.assertEqual(profile, config.load(profile.name))

    def test_replacing_profile(self):
        database = sqlite3.connect(":memory:")
        config = ProfileConfig(database)
        profile1 = make_profile().replace(name="alice")
        profile2 = make_profile().replace(name="alice")
        self.assertNotEqual(profile1, profile2)
        config.save(profile1)
        config.save(profile2)
        self.assertEqual({"alice"}, set(config))
        self.assertEqual(profile2, config.load("alice"))

    def test_loading_non_existent_profile(self):
        database = sqlite3.connect(":memory:")
        config = ProfileConfig(database)
        self.assertRaises(KeyError, config.load, "alice")

    def test_removing_profile(self):
        database = sqlite3.connect(":memory:")
        config = ProfileConfig(database)
        profile = make_profile()
        config.save(profile)
        config.delete(profile.name)
        self.assertEqual(set(), set(config))

    def test_open_and_close(self):
        # ProfileConfig.open() returns a context manager that closes the
        # database on exit.
        config_file = os.path.join(self.make_dir(), "config")
        config = ProfileConfig.open(config_file)
        self.assertIsInstance(config, contextlib._GeneratorContextManager)
        with config as config:
            self.assertIsInstance(config, ProfileConfig)
            with config.cursor() as cursor:
                self.assertEqual(
                    (1,), cursor.execute("SELECT 1").fetchone())
        self.assertRaises(sqlite3.ProgrammingError, config.cursor)

    def test_open_permissions_new_database(self):
        # ProfileConfig.open() applies restrictive file permissions to newly
        # created configuration databases.
        config_file = os.path.join(self.make_dir(), "config")
        with ProfileConfig.open(config_file):
            perms = FilePath(config_file).getPermissions()
            self.assertEqual("rw-------", perms.shorthand())

    def test_open_permissions_existing_database(self):
        # ProfileConfig.open() leaves the file permissions of existing
        # configuration databases.
        config_file = os.path.join(self.make_dir(), "config")
        open(config_file, "wb").close()  # touch.
        os.chmod(config_file, 0o644)  # u=rw,go=r
        with ProfileConfig.open(config_file):
            perms = FilePath(config_file).getPermissions()
            self.assertEqual("rw-r--r--", perms.shorthand())
