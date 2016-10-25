"""Logging-in to a remote MAAS instance with a user-name and password.

Instead of copy-and-pasting API keys, this allows clients to log-in using
their user-name and password, and automatically retrieve an API key. These
credentials can then be saved with the profile manager.
"""

__all__ = [
    "login",
    "LoginError",
    "PasswordWithoutUsername",
    "UsernameWithoutPassword",
]

from urllib.parse import urlparse

from . import (
    api_url,
    fetch_api_description,
)
from .auth import obtain_token
from .profiles import Profile


class LoginError(Exception):
    """An error with logging-in."""


class PasswordWithoutUsername(LoginError):
    """A password was provided without a corresponding user-name."""


class UsernameWithoutPassword(LoginError):
    """A user-name was provided without a corresponding password."""


def login(url, *, username=None, password=None, insecure=False):
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

    # Return a new (unsaved) profile.
    return Profile(
        name=url.netloc, url=url.geturl(), credentials=credentials,
        description=fetch_api_description(url, credentials, insecure))
