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

    async def whoami(cls):
        """Get the logged-in user."""
        data = await cls._handler.whoami()
        return cls._object(data)

    async def create(cls, username, password, *, email=None, is_admin=False):
        if email is None:
            email = "%s@null.maas.io" % username
        data = await cls._handler.create(
            username=username, email=email, password=password,
            is_superuser='1' if is_admin else '0')
        return cls._object(data)

    async def read(cls):
        data = await cls._handler.read()
        return cls(map(cls._object, data))


class Users(ObjectSet, metaclass=UsersType):
    """The set of users."""


class User(Object):
    """A user."""

    username = ObjectField.Checked(
        "username", check(str), check(str))
    email = ObjectField.Checked(
        "email", check(str), check(str))
    is_admin = ObjectField.Checked(
        "is_superuser", check(bool), check(bool))

    def __repr__(self):
        if self.is_admin:
            return super(User, self).__repr__(
                name="Admin", fields={"username"})
        else:
            return super(User, self).__repr__(
                name="User", fields={"username"})
