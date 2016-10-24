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

    def create(cls, username, password, *, email=None, is_superuser=False):
        if email is None:
            email = "%s@null.maas.io" % username
        data = cls._handler.create(
            username=username, email=email, password=password,
            is_superuser='1' if is_superuser else '0')
        return cls._object(data)


class Users(ObjectSet, metaclass=UsersType):
    """The set of users."""

    @classmethod
    def read(cls):
        return cls(cls)


class User(Object):
    """A user."""

    username = ObjectField.Checked(
        "username", check(str), check(str))
    email = ObjectField.Checked(
        "email", check(str), check(str))
    is_superuser = ObjectField.Checked(
        "is_superuser", check(bool), check(bool))
