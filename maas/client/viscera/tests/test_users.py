"""Test for `maas.client.viscera.users`."""

from testtools.matchers import (
    Equals,
    MatchesStructure,
)

from .. import users
from ...testing import (
    make_name_without_spaces,
    pick_bool,
    TestCase,
)
from ..testing import bind


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

    def test__create_without_email(self):
        username = make_name_without_spaces("username")
        password = make_name_without_spaces("password")
        email = "%s@null.maas.io" % username
        is_admin = pick_bool()

        Users = make_origin().Users
        Users._handler.create.return_value = {
            "username": username, "email": email, "is_superuser": is_admin}

        Users.create(username, password, is_admin=is_admin)
        Users._handler.create.assert_called_once_with(
            username=username, password=password, email=email,
            is_superuser='1' if is_admin else '0')

    def test__create_with_email(self):
        username = make_name_without_spaces("username")
        password = make_name_without_spaces("password")
        domain = "%s.com" % make_name_without_spaces("domain")
        email = "%s@%s" % (username, domain)
        is_admin = pick_bool()

        Users = make_origin().Users
        Users._handler.create.return_value = {
            "username": username, "email": email, "is_superuser": is_admin}

        Users.create(username, password, email=email, is_admin=is_admin)
        Users._handler.create.assert_called_once_with(
            username=username, password=password, email=email,
            is_superuser='1' if is_admin else '0')
