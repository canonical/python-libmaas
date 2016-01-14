"""Profile configuration."""

__all__ = [
    "Profile",
    "ProfileManager",
    "ProfileNotFound",
]

from contextlib import (
    closing,
    contextmanager,
)
from copy import deepcopy
import json
import os
from os.path import expanduser
import sqlite3
from typing import Optional

from . import api_url
from .creds import Credentials
from .typecheck import typed
from .types import JSONObject


class Profile(tuple):
    """A profile is all that's required to talk to a remote MAAS."""

    __slots__ = ()

    @typed
    def __new__(
            cls, name: str, url: str, *, credentials: Optional[Credentials],
            description: dict, **other: JSONObject):
        return super(Profile, cls).__new__(
            cls, (name, api_url(url), credentials, description, other))

    @property
    def name(self) -> str:
        """The name of this profile."""
        return self[0]

    @property
    def url(self) -> str:
        """The URL for this profile."""
        return self[1]

    @property
    def credentials(self) -> Optional[Credentials]:
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


class ProfileNotFound(KeyError):
    """The named profile was not found."""

    def __init__(self, name):
        super(ProfileNotFound, self).__init__(
            "Profile '%s' not found." % (name,))


class ProfileManager:
    """Store profile configurations in an sqlite3 database."""

    def __init__(self, database):
        self.database = database
        with self.cursor() as cursor:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS profiles "
                "(id INTEGER PRIMARY KEY,"
                " name TEXT NOT NULL UNIQUE,"
                " data BLOB)")

    def cursor(self):
        return closing(self.database.cursor())

    def __iter__(self):
        with self.cursor() as cursor:
            results = cursor.execute(
                "SELECT name FROM profiles").fetchall()
        return (name for (name,) in results)

    @typed
    def load(self, name: str) -> Profile:
        with self.cursor() as cursor:
            data = cursor.execute(
                "SELECT data FROM profiles"
                " WHERE name = ?", (name,)).fetchone()
        if data is None:
            raise ProfileNotFound(name)
        else:
            state = json.loads(data[0])
            creds = state.pop("credentials", None)
            return Profile(credentials=Credentials.parse(creds), **state)

    @typed
    def save(self, profile: Profile):
        state = profile.dump()
        data = json.dumps(state)
        with self.cursor() as cursor:
            cursor.execute(
                "INSERT OR REPLACE INTO profiles (name, data) "
                "VALUES (?, ?)", (profile.name, data))

    @typed
    def delete(self, name: str):
        with self.cursor() as cursor:
            cursor.execute(
                "DELETE FROM profiles"
                " WHERE name = ?", (name,))

    @classmethod
    @contextmanager
    def open(cls, dbpath=expanduser("~/.maascli.db")):
        """Load a profiles database.

        Called without arguments this will open (and create) a database in the
        user's home directory.

        **Note** that this returns a context manager which will close the
        database on exit, saving if the exit is clean.
        """
        # Initialise filename with restrictive permissions...
        os.close(os.open(dbpath, os.O_CREAT | os.O_APPEND, 0o600))
        # before opening it with sqlite.
        database = sqlite3.connect(dbpath)
        try:
            yield cls(database)
        except:
            raise
        else:
            database.commit()
        finally:
            database.close()
