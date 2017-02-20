"""Connect to a remote MAAS instance with an apikey."""

__all__ = [
    "connect",
    "ConnectError",
]

from urllib.parse import urlparse

from . import api_url
from .creds import Credentials
from .profiles import Profile
from .async import asynchronous


class ConnectError(Exception):
    """An error with connecting."""


@asynchronous
async def connect(url, *, apikey=None, insecure=False):
    """Connect to a remote MAAS instance with `apikey`.

    Returns a new :class:`Profile` which has NOT been saved. To connect AND
    save a new profile::

        profile = connect(url, apikey=apikey)
        profile = profile.replace(name="mad-hatter")

        with profiles.ProfileStore.open() as config:
            config.save(profile)
            # Optionally, set it as the default.
            config.default = profile.name

    """
    url = api_url(url)
    url = urlparse(url)

    if url.username is not None:
        raise ConnectError(
            "Cannot provide user-name explicitly in URL (%r) when connecting; "
            "use login instead." % url.username)
    if url.password is not None:
        raise ConnectError(
            "Cannot provide password explicitly in URL (%r) when connecting; "
            "use login instead." % url.username)

    if apikey is None:
        credentials = None  # Anonymous access.
    else:
        credentials = Credentials.parse(apikey)

    # Circular import.
    from ..bones.helpers import fetch_api_description
    description = await fetch_api_description(url, credentials, insecure)

    # Return a new (unsaved) profile.
    return Profile(
        name=url.netloc, url=url.geturl(), credentials=credentials,
        description=description)
