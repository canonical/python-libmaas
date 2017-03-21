"""Miscellaneous helpers for Bones."""

__all__ = [
    "authenticate",
    "connect",
    "ConnectError",
    "derive_resource_name",
    "fetch_api_description",
    "login",
    "LoginError",
    "LoginNotSupported",
    "PasswordWithoutUsername",
    "RemoteError",
    "UsernameWithoutPassword",
]

from getpass import getuser
from http import HTTPStatus
from socket import gethostname
import typing
from urllib.parse import (
    ParseResult,
    SplitResult,
    urljoin,
    urlparse,
)

import aiohttp

from ..utils import api_url
from ..utils.async import asynchronous
from ..utils.creds import Credentials
from ..utils.profiles import Profile


class RemoteError(Exception):
    """Miscellaneous error related to a remote system."""


async def fetch_api_description(
        url: typing.Union[str, ParseResult, SplitResult],
        credentials: typing.Optional[Credentials]=None,
        insecure: bool=False):
    """Fetch the API description from the remote MAAS instance."""
    url_describe = urljoin(_ensure_url_string(url), "describe/")
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


def _ensure_url_string(url):
    """Convert `url` to a string URL if it isn't one already."""
    if isinstance(url, str):
        return url
    elif isinstance(url, ParseResult):
        return url.geturl()
    elif isinstance(url, SplitResult):
        return url.geturl()
    else:
        raise TypeError(
            "Could not convert %r to a string URL." % (url,))


def derive_resource_name(name):
    """A stable, human-readable name and identifier for a resource."""
    if name.startswith("Anon"):
        name = name[4:]
    if name.endswith("Handler"):
        name = name[:-7]
    if name == "Maas":
        name = "MAAS"
    return name


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


class LoginNotSupported(LoginError):
    """Server does not support login-type auth for API clients."""


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

    :raise RemoteError: An unexpected error from the remote system.
    :raise LoginError: An error related to logging-in.
    :raise PasswordWithoutUsername: Password given, but not username.
    :raise UsernameWithoutPassword: Username given, but not password.
    :raise LoginNotSupported: Server does not support API client log-in.
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
            credentials = await authenticate(
                url.geturl(), username, password, insecure=insecure)

    # Circular import.
    from ..bones.helpers import fetch_api_description
    description = await fetch_api_description(url, credentials, insecure)

    # Return a new (unsaved) profile.
    return Profile(
        name=url.netloc, url=url.geturl(), credentials=credentials,
        description=description)


async def authenticate(url, username, password, *, insecure=False):
    """Obtain a new API key by logging into MAAS.

    :param url: URL for the MAAS API (i.e. ends with ``/api/x.y/``).
    :param insecure: If true, don't verify SSL/TLS certificates.
    :return: A `Credentials` instance.

    :raise RemoteError: An unexpected error from the remote system.
    :raise LoginNotSupported: Server does not support API client log-in.
    """
    url_versn = urljoin(url, "version/")
    url_authn = urljoin(url, "../../accounts/authenticate/")

    def check_response_is_okay(response):
        if response.status != HTTPStatus.OK:
            raise RemoteError(
                "{0} -> {1.status} {1.reason}".format(
                    response.url_obj.human_repr(), response))

    connector = aiohttp.TCPConnector(verify_ssl=(not insecure))
    session = aiohttp.ClientSession(connector=connector)
    async with session:
        # Check that this server supports `authenticate-api`.
        async with session.get(url_versn) as response:
            check_response_is_okay(response)
            version_info = await response.json()

        if "authenticate-api" not in version_info["capabilities"]:
            raise LoginNotSupported(
                "Server does not support automated client log-in. "
                "Please obtain an API token via the MAAS UI.")

        # POST to the `authenticate` endpoint.
        data = {
            "username": username, "password": password,
            "consumer": "%s@%s" % (getuser(), gethostname())
        }
        async with session.post(url_authn, data=data) as response:
            check_response_is_okay(response)
            token_info = await response.json()

        return Credentials(
            token_info["consumer_key"],
            token_info["token_key"],
            token_info["token_secret"],
        )
