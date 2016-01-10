# Copyright 2015 Alburnum Ltd. This software is licensed under
# the GNU Affero General Public License version 3 (see LICENSE).

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


CredentialsBase = namedtuple(
    "CredentialsBase", ("consumer_key", "token_key", "token_secret"))


class Credentials(CredentialsBase):
    """MAAS API Credentials."""

    __slots__ = ()

    @classmethod
    def parse(cls, credentials):
        parts = credentials.split(":")
        if len(parts) == 3:
            return cls(*parts)
        else:
            raise ValueError(
                "Malformed credentials string. Expected 3 colon-"
                "separated parts, got %r." % (credentials, ))

    def __str__(self):
        return ":".join(self)
