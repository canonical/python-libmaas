"""Profile configuration."""

__all__ = [
    "Profile",
    "ProfileStore",
    "ProfileNotFound",
]

from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
from textwrap import dedent
import typing

from . import api_url
from .creds import Credentials
from .types import JSONObject


class Profile(tuple):
    """A profile is all that's required to talk to a remote MAAS."""

    __slots__ = ()

    def __new__(
            cls, name: str, url: str, *,
            credentials: typing.Union[Credentials, typing.Sequence, str, None],
            description: dict, **other: JSONObject):
        return super(Profile, cls).__new__(cls, (
            name, api_url(url), Credentials.parse(credentials),
            description, other))

    @property
    def name(self) -> str:
        """The name of this profile."""
        return self[0]

    @property
    def url(self) -> str:
        """The URL for this profile."""
        return self[1]

    @property
    def credentials(self) -> typing.Optional[Credentials]:
        """The credentials for this profile, if set."""
        return self[2]

    @property
    def description(self) -> dict:
        """The description for this profile, detailing remote resources et al.

        A deep copy is made of this before it is returned, so that mutations
        will not alter the originating copy.
        """
        return deepcopy(self[3])

    @property
    def other(self) -> dict:
        """Other fields that have been stored for this profile.

        A deep copy is made of this before it is returned, so that mutations
        will not alter the originating copy.
        """
        return deepcopy(self[-1])

    def replace(self, **updates):
        """Return a new profile with the given updates.

        Unspecified fields will be the same as this instance. See `__new__`
        for details on the arguments.
        """
        state = self.dump()
        state.update(updates)
        return self.__class__(**state)

    def dump(self):
        """Return a dict of fields that can be used to recreate this profile.

        For example::

          >>> profile = Profile(name="foobar", ...)
          >>> profile == Profile(**profile.dump())
          True

        Use this value when persisting a profile.
        """
        return dict(
            self.other, name=self.name, url=self.url,
            credentials=self.credentials, description=self.description,
        )

    def __repr__(self):
        if self.credentials is None:
            return "<%s %s (anonymous) %s>" % (
                self.__class__.__name__, self.name, self.url)
        else:
            return "<%s %s %s>" % (
                self.__class__.__name__, self.name, self.url)


class ProfileNotFound(Exception):
    """The named profile was not found."""

    def __init__(self, name):
        super(ProfileNotFound, self).__init__(
            "Profile '%s' not found." % (name,))


def schema_create(conn):
    """Create the index for storing profiles.

    This is idempotent; it can be called every time a database is opened to
    make sure it's ready to use and up-to-date.

    :param conn: A connection to an SQLite3 database.
    """
    conn.execute(dedent("""\
    CREATE TABLE IF NOT EXISTS profiles
      (id INTEGER PRIMARY KEY,
       name TEXT NOT NULL UNIQUE,
       data BLOB NOT NULL,
       selected BOOLEAN NOT NULL DEFAULT FALSE)
    """))
    # Partial indexes are only available in >=3.8.0 and expressions in indexes
    # are only available in >=3.9.0 (https://www.sqlite.org/partialindex.html
    # & https://www.sqlite.org/expridx.html). Don't bother with any kind of
    # index before that because it would complicate upgrades.
    if sqlite3.sqlite_version_info >= (3, 9, 0):
        # This index is for data integrity -- ensuring that only one profile
        # is the default ("selected") profile -- and speed a distant second.
        conn.execute(dedent("""\
        CREATE UNIQUE INDEX IF NOT EXISTS
          only_one_profile_selected ON profiles
          (selected IS NOT NULL) WHERE selected
        """))


def schema_import(conn, dbpath):
    """Import profiles from another database.

    This does not overwrite existing profiles in the target database. Profiles
    in the source database that share names with those in the target database
    are ignored.

    :param conn: A connection to an SQLite3 database into which to copy
        profiles.
    :param dbpath: The filesystem path to the source SQLite3 database.
    """
    conn.execute(
        "ATTACH DATABASE ? AS source", (str(dbpath),))
    conn.execute(
        "INSERT OR IGNORE INTO profiles (name, data)"
        " SELECT name, data FROM source.profiles"
        " WHERE data IS NOT NULL")
    conn.execute(
        "DETACH DATABASE source")


class ProfileStore:
    """Store profile configurations in an sqlite3 database."""

    def __init__(self, database):
        self.database = database
        schema_create(database)

    def __iter__(self):
        results = self.database.execute("SELECT name FROM profiles").fetchall()
        return (name for (name,) in results)

    def load(self, name: str) -> Profile:
        found = self.database.execute(
            "SELECT data FROM profiles"
            " WHERE name = ?", (name,)).fetchone()
        if found is None:
            raise ProfileNotFound(name)
        else:
            state = json.loads(found[0])
            state["name"] = name  # Belt-n-braces.
            return Profile(**state)

    def save(self, profile: Profile):
        state = profile.dump()
        data = json.dumps(state)
        # On the face of it `INSERT OR REPLACE` would be an obvious way to do
        # this. However, on conflict it will erase the value of the `selected`
        # column to the default (which is false). Hence we do it in two steps,
        # within a transaction.
        with self.database:
            # Ensure there's a row for this profile.
            self.database.execute(
                "INSERT OR IGNORE INTO profiles (name, data) VALUES (?, '')",
                (profile.name,))
            # Update the row's data.
            self.database.execute(
                "UPDATE profiles SET data = ? WHERE name = ?",
                (data, profile.name))

    def delete(self, name: str):
        self.database.execute(
            "DELETE FROM profiles WHERE name = ?", (name,))

    @property
    def default(self) -> typing.Optional[Profile]:
        """The name of the default profile to use, or `None`."""
        found = self.database.execute(
            "SELECT name, data FROM profiles WHERE selected"
            " ORDER BY name LIMIT 1").fetchone()
        if found is None:
            return None
        else:
            state = json.loads(found[1])
            state["name"] = found[0]  # Belt-n-braces.
            return Profile(**state)

    @default.setter
    def default(self, profile: Profile):
        with self.database:
            self.save(profile)
            self.database.execute(
                "UPDATE profiles SET selected = (name = ?)",
                (profile.name,))

    @default.deleter
    def default(self):
        self.database.execute("UPDATE profiles SET selected = 0")

    @classmethod
    @contextmanager
    def open(cls, dbpath=Path("~/.maas.db").expanduser()):
        """Load a profiles database.

        Called without arguments this will open (and create) a database in the
        user's home directory.

        **Note** that this returns a context manager which will close the
        database on exit, saving if the exit is clean.

        :param dbpath: The path to the database file to create and open.
        """
        # Ensure we're working with a Path instance.
        dbpath = Path(dbpath)
        # See if we ought to do a one-time migration.
        migrate_from = Path("~/.maascli.db").expanduser()
        migrate = migrate_from.is_file() and not dbpath.exists()
        # Initialise filename with restrictive permissions...
        dbpath.touch(mode=0o600, exist_ok=True)
        # Final check to see if it's safe to migrate.
        migrate = migrate and not migrate_from.samefile(dbpath)
        # before opening it with sqlite.
        database = sqlite3.connect(str(dbpath))
        try:
            store = cls(database)
            if migrate:
                schema_import(database, migrate_from)
                yield store
            else:
                yield store
        except:
            raise
        else:
            database.commit()
        finally:
            database.close()
