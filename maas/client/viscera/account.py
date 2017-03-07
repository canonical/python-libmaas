"""Objects for accounts."""

__all__ = [
    "Account",
]

from . import (
    Object,
    ObjectType,
)
from ..utils.creds import Credentials


class AccountType(ObjectType):
    """Metaclass for `Account`."""

    async def create_credentials(cls) -> Credentials:
        data = await cls._handler.create_authorisation_token()
        return Credentials(
            consumer_key=data["consumer_key"], token_key=data["token_key"],
            token_secret=data["token_secret"])

    async def delete_credentials(cls, credentials: Credentials) -> None:
        await cls._handler.delete_authorisation_token(
            token_key=credentials.token_key)


class Account(Object, metaclass=AccountType):
    """The current account."""
