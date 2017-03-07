"""Miscellaneous helpers for Bones."""

__all__ = [
    "connect",
    "ConnectError",
    "fetch_api_description",
    "login",
    "LoginError",
    "PasswordWithoutUsername",
    "RemoteError",
    "UsernameWithoutPassword",
]

from http import HTTPStatus
from typing import Optional
from urllib.parse import (
    urljoin,
    urlparse,
)

import aiohttp
import aiohttp.errors

from ..utils import api_url
from ..utils.async import asynchronous
from ..utils.auth import obtain_token
from ..utils.creds import Credentials
from ..utils.profiles import Profile


class RemoteError(Exception):
    """Miscellaneous error related to a remote system."""


async def fetch_api_description(
        url: str, credentials: Optional[Credentials]=None,
        insecure: bool=False):
    """Fetch the API description from the remote MAAS instance."""
    url_describe = urljoin(url, "describe/")
    connector = aiohttp.TCPConnector(verify_ssl=(not insecure))
    session = aiohttp.ClientSession(connector=connector)
    async with session, session.get(url_describe) as response:
        if response.status != HTTPStatus.OK:
            raise RemoteError(
                "{0} -> {1.status} {1.reason}".format(
                    url, response))
        elif response.content_type != "application/json":
            raise RemoteError(
                "Expected application/json, got: %s"
                % response.content_type)
        else:
            return await response.json()


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


class LoginError(Exception):
    """An error with logging-in."""


class PasswordWithoutUsername(LoginError):
    """A password was provided without a corresponding user-name."""


class UsernameWithoutPassword(LoginError):
    """A user-name was provided without a corresponding password."""


@asynchronous
async def login(url, *, username=None, password=None, insecure=False):
    """Log-in to a remote MAAS instance.

    Returns a new :class:`Profile` which has NOT been saved. To log-in AND
    save a new profile::

        profile = login(url, username="alice", password="wonderland")
        profile = profile.replace(name="mad-hatter")

        with profiles.ProfileStore.open() as config:
            config.save(profile)
            # Optionally, set it as the default.
            config.default = profile.name

    """
    url = api_url(url)
    url = urlparse(url)

    if username is None:
        username = url.username
    else:
        if url.username is None:
            pass  # Anonymous access.
        else:
            raise LoginError(
                "User-name provided explicitly (%r) and in URL (%r); "
                "provide only one." % (username, url.username))

    if password is None:
        password = url.password
    else:
        if url.password is None:
            pass  # Anonymous access.
        else:
            raise LoginError(
                "Password provided explicitly (%r) and in URL (%r); "
                "provide only one." % (password, url.password))

    # Remove user-name and password from the URL.
    userinfo, _, hostinfo = url.netloc.rpartition("@")
    url = url._replace(netloc=hostinfo)

    if username is None:
        if password is None or len(password) == 0:
            credentials = None  # Anonymous.
        else:
            raise PasswordWithoutUsername(
                "Password provided without user-name; specify user-name.")
    else:
        if password is None:
            raise UsernameWithoutPassword(
                "User-name provided without password; specify password.")
        else:
            credentials = obtain_token(
                url.geturl(), username, password, insecure=insecure)

    # Circular import.
    from ..bones.helpers import fetch_api_description
    description = await fetch_api_description(url, credentials, insecure)

    # Return a new (unsaved) profile.
    return Profile(
        name=url.netloc, url=url.geturl(), credentials=credentials,
        description=description)
