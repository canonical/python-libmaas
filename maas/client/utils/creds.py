"""Handling of MAAS API credentials.

The API client deals with credentials consisting of 3 elements: consumer key,
token key, and token secret. These are parts of the OAuth 1.0 specification.
The consumer secret is hard-wired to the empty string.

Credentials are represented internally as `Credentials` tuples, but can also
be converted to a colon-separated string format for easy transport between
processes.
"""

__all__ = [
    "Credentials",
    ]

from collections import namedtuple
import typing


CredentialsBase = namedtuple(
    "CredentialsBase", ("consumer_key", "token_key", "token_secret"))


class Credentials(CredentialsBase):
    """MAAS API Credentials."""

    __slots__ = ()

    @classmethod
    def parse(cls, credentials) -> typing.Optional["Credentials"]:
        """Parse/interpret some given credentials.

        These may take the form of:

        * An empty string.

        * An empty sequence.

        * A string, containing three parts (consumer key, token key, and token
          secret) separated by colons.

        * A sequence of three strings (consumer key, token key, and token
          secret).

        * None.

        """
        if credentials is None:
            return None
        elif isinstance(credentials, cls):
            return credentials
        elif isinstance(credentials, str):
            if credentials == "":
                return None
            elif credentials.count(":") == 2:
                return cls(*credentials.split(":"))
            else:
                raise ValueError(
                    "Malformed credentials. Expected 3 colon-separated "
                    "parts, got %r." % (credentials, ))
        else:
            parts = list(credentials)
            if len(parts) == 0:
                return None
            elif len(parts) == 3:
                return cls(*parts)
            else:
                raise ValueError(
                    "Malformed credentials. Expected 3 parts, "
                    "got %r." % (credentials, ))

    def __str__(self):
        return ":".join(self)
