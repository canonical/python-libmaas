"""Objects for users."""

__all__ = [
    "User",
    "Users",
]

from . import (
    check,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
)


class UsersType(ObjectType):
    """Metaclass for `Users`."""

    def __iter__(cls):
        return map(cls._object, cls._handler.read())


class Users(ObjectSet, metaclass=UsersType):
    """The set of users."""

    @classmethod
    def read(cls):
        return list(cls)


class User(Object):
    """A user."""

    username = ObjectField.Checked(
        "username", check(str), check(str))
    email = ObjectField.Checked(
        "email", check(str), check(str))
    is_admin = ObjectField.Checked(
        "is_superuser", check(bool), check(bool))
