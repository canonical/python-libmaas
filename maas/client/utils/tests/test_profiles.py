"""Tests for `maas.client.utils.profiles`."""

import contextlib
from pathlib import Path
import sqlite3

from testtools.matchers import (
    Equals,
    Is,
    Not,
)
from twisted.python.filepath import FilePath

from .. import profiles
from ...testing import (
    make_name_without_spaces,
    TestCase,
)
from ..profiles import (
    Profile,
    ProfileNotFound,
    ProfileStore,
)
from ..testing import make_Credentials


def make_profile():
    return Profile(
        name=make_name_without_spaces("name"), url="http://example.com:5240/",
        credentials=make_Credentials(), description={"resources": []},
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


class TestProfileStore(TestCase):
    """Tests for `ProfileStore`."""

    def test_init(self):
        database = sqlite3.connect(":memory:")
        config = ProfileStore(database)
        # The profiles table has been created.
        self.assertEqual(
            config.database.execute(
                "SELECT COUNT(*) FROM sqlite_master"
                " WHERE type = 'table'"
                "   AND name = 'profiles'").fetchone(),
            (1,))

    def test_profiles_pristine(self):
        # A pristine configuration has no profiles.
        database = sqlite3.connect(":memory:")
        config = ProfileStore(database)
        self.assertSetEqual(set(), set(config))

    def test_saving_and_loading_profile(self):
        database = sqlite3.connect(":memory:")
        config = ProfileStore(database)
        profile = make_profile()
        config.save(profile)
        self.assertEqual({profile.name}, set(config))
        self.assertEqual(profile, config.load(profile.name))

    def test_saving_failure_does_not_corrupt_database(self):
        database = sqlite3.connect(":memory:")
        config = ProfileStore(database)
        profile_good = make_profile()
        config.save(profile_good)
        profile_bad = profile_good.replace(foo=object())
        self.assertRaises(TypeError, config.save, profile_bad)
        self.assertEqual({profile_good.name}, set(config))
        self.assertEqual(profile_good, config.load(profile_good.name))

    def test_replacing_profile(self):
        database = sqlite3.connect(":memory:")
        config = ProfileStore(database)
        profile1 = make_profile().replace(name="alice")
        profile2 = make_profile().replace(name="alice")
        self.assertNotEqual(profile1, profile2)
        config.save(profile1)
        config.save(profile2)
        self.assertEqual({"alice"}, set(config))
        self.assertEqual(profile2, config.load("alice"))

    def test_loading_non_existent_profile(self):
        database = sqlite3.connect(":memory:")
        config = ProfileStore(database)
        self.assertRaises(ProfileNotFound, config.load, "alice")

    def test_removing_profile(self):
        database = sqlite3.connect(":memory:")
        config = ProfileStore(database)
        profile = make_profile()
        config.save(profile)
        config.delete(profile.name)
        self.assertEqual(set(), set(config))

    def test_open_and_close(self):
        # ProfileStore.open() returns a context manager that closes the
        # database on exit.
        config_file = self.makeDir().joinpath("config")
        config = ProfileStore.open(config_file)
        self.assertIsInstance(config, contextlib._GeneratorContextManager)
        with config as config:
            self.assertIsInstance(config, ProfileStore)
            self.assertEqual(
                (1,), config.database.execute("SELECT 1").fetchone())
        self.assertRaises(
            sqlite3.ProgrammingError, config.database.execute,
            "SELECT 1")

    def test_open_permissions_new_database(self):
        # ProfileStore.open() applies restrictive file permissions to newly
        # created configuration databases.
        config_file = self.makeDir().joinpath("config")
        with ProfileStore.open(config_file):
            perms = FilePath(str(config_file)).getPermissions()
            self.assertEqual("rw-------", perms.shorthand())

    def test_open_permissions_existing_database(self):
        # ProfileStore.open() leaves the file permissions of existing
        # configuration databases.
        config_file = self.makeDir().joinpath("config")
        config_file.touch()
        config_file.chmod(0o644)  # u=rw,go=r
        with ProfileStore.open(config_file):
            perms = FilePath(str(config_file)).getPermissions()
            self.assertEqual("rw-r--r--", perms.shorthand())

    def test_open_does_one_time_migration(self):
        home = self.makeDir()
        dbpath_old = home.joinpath(".maascli.db")
        dbpath_new = home.joinpath(".maas.db")

        # Path.expanduser() is used by ProfileStore.open(). We expect the
        # paths to be expanded to be one of those below.
        def expanduser(path):
            if path == Path("~/.maas.db"):
                return dbpath_new
            if path == Path("~/.maascli.db"):
                return dbpath_old
            raise ValueError(path)

        self.patch(profiles.Path, "expanduser", expanduser)

        # A profile that will be migrated.
        profile = make_profile()

        # Populate the old database with a profile. We're using the new
        # ProfileStore but that's okay; the schemas are compatible.
        with ProfileStore.open(dbpath_old) as config_old:
            config_old.save(profile)

        # Immediately as we open the new database, profiles from the old
        # database are migrated.
        with ProfileStore.open(dbpath_new) as config_new:
            self.assertEqual({profile.name}, set(config_new))
            profile_migrated = config_new.load(profile.name)
            self.assertEqual(profile, profile_migrated)
            # Before closing, delete the migrated profile.
            config_new.delete(profile.name)

        # After reopening the new database we see the migrated profile that we
        # deleted has stayed deleted; it has not been migrated a second time.
        with ProfileStore.open(dbpath_new) as config_new:
            self.assertRaises(ProfileNotFound, config_new.load, profile.name)

        # It is still present and correct in the old database.
        with ProfileStore.open(dbpath_old) as config_old:
            self.assertEqual(profile, config_old.load(profile.name))


class TestProfileStoreDefault(TestCase):
    """Tests for `ProfileStore` default profile."""

    def test_getting_and_setting_default_profile(self):
        database = sqlite3.connect(":memory:")
        config = ProfileStore(database)
        self.assertIsNone(config.default)
        profile = make_profile()
        config.default = profile
        self.assertEqual(profile, config.default)
        # A side-effect is that the profile is saved.
        self.assertEqual({profile.name}, set(config))

    def test_default_profile_is_persisted(self):
        database = sqlite3.connect(":memory:")
        config1 = ProfileStore(database)
        config2 = ProfileStore(database)
        profile = make_profile()
        config1.default = profile
        self.assertEqual(profile, config2.default)

    def test_default_profile_remains_default_after_subsequent_save(self):
        database = sqlite3.connect(":memory:")
        profile = make_profile()
        config = ProfileStore(database)
        config.default = profile
        profile = profile.replace(foo="bar")
        config.save(profile)
        self.assertEqual(profile, config.default)

    def test_default_profile_remains_default_after_failed_save(self):
        database = sqlite3.connect(":memory:")
        profile_good = make_profile()
        config = ProfileStore(database)
        config.default = profile_good
        profile_bad = profile_good.replace(foo=object())
        self.assertRaises(TypeError, config.save, profile_bad)
        self.assertEqual(profile_good, config.default)

    def test_clearing_default_profile(self):
        database = sqlite3.connect(":memory:")
        config = ProfileStore(database)
        profile = make_profile()
        config.default = profile
        del config.default
        self.assertIsNone(config.default)
        # The profile itself is not removed.
        self.assertEqual({profile.name}, set(config))

    def test_getting_default_profile_when_profile_has_been_deleted(self):
        database = sqlite3.connect(":memory:")
        config = ProfileStore(database)
        config.default = make_profile()
        config.delete(config.default.name)
        self.assertIsNone(config.default)
        # The profile itself is gone.
        self.assertEqual(set(), set(config))
