"""Miscellaneous helpers for Bones."""

__all__ = [
    "fetch_api_description",
    "RemoteError",
]

from http import HTTPStatus
from typing import Optional
from urllib.parse import urljoin

import aiohttp
import aiohttp.errors

from ..utils.creds import Credentials
from ..utils.typecheck import typed


class RemoteError(Exception):
    """Miscellaneous error related to a remote system."""


@typed
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
