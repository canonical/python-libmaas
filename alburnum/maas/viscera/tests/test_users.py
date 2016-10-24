"""Test for `alburnum.maas.viscera.users`."""

__all__ = []

from alburnum.maas.testing import (
    make_name_without_spaces,
    pick_bool,
    TestCase,
)
from alburnum.maas.viscera.testing import bind
from testtools.matchers import (
    Equals,
    MatchesStructure,
)

from .. import users


def make_origin():
    # Create a new origin with Users and User. The former refers to the
    # latter via the origin, hence why it must be bound.
    return bind(users.Users, users.User)


class TestUser(TestCase):

    def test__string_representation_includes_username_only(self):
        user = users.User({
            "username": make_name_without_spaces("username"),
            "email": make_name_without_spaces("user@"),
            "is_superuser": False,
        })
        self.assertThat(repr(user), Equals(
            "<User username=%(username)r>" % user._data))

    def test__string_representation_includes_username_only_for_admin(self):
        user = users.User({
            "username": make_name_without_spaces("username"),
            "email": make_name_without_spaces("user@"),
            "is_superuser": True,
        })
        self.assertThat(repr(user), Equals(
            "<Admin username=%(username)r>" % user._data))


class TestUsers(TestCase):

    def test__whoami(self):
        username = make_name_without_spaces("username")
        email = make_name_without_spaces("user@")
        is_admin = pick_bool()

        Users = make_origin().Users
        Users._handler.whoami.return_value = {
            "username": username, "email": email, "is_superuser": is_admin}

        user = Users.whoami()
        self.assertThat(user, MatchesStructure.byEquality(
            username=username, email=email, is_admin=is_admin))
