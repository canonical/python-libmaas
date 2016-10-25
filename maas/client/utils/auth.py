"""MAAS CLI authentication."""

__all__ = [
    "obtain_credentials",
    "obtain_token",
    "try_getpass",
    ]

from getpass import (
    getpass,
    getuser,
)
from socket import gethostname
import sys
from urllib.parse import urljoin

import bs4
import requests

from .creds import Credentials


def try_getpass(prompt):
    """Call `getpass`, ignoring EOF errors."""
    try:
        return getpass(prompt)
    except EOFError:
        return None


def obtain_credentials(credentials):
    """Prompt for credentials if possible.

    If the credentials are "-" then read from stdin without interactive
    prompting.
    """
    if credentials == "-":
        credentials = sys.stdin.readline().strip()
    elif credentials is None:
        credentials = try_getpass(
            "API key (leave empty for anonymous access): ")
    # Ensure that the credentials have a valid form.
    if credentials and not credentials.isspace():
        return Credentials.parse(credentials)
    else:
        return None


def obtain_token(url, username, password, *, insecure=False):
    """Obtain a new API key by logging into MAAS.

    :param url: URL for the MAAS API (i.e. ends with ``/api/x.y/``).
    :param insecure: If true, don't verify SSL/TLS certificates.
    :return: A `Credentials` instance.
    """
    url_login = urljoin(url, "../../accounts/login/")
    url_token = urljoin(url, "account/")

    with requests.Session() as session:

        # Don't verify SSL/TLS certificates by default, if requested.
        session.verify = not insecure

        # Fetch the log-in page.
        response = session.get(url_login)
        response.raise_for_status()

        # Extract the CSRF token.
        login_doc = bs4.BeautifulSoup(response.content, "html.parser")
        login_button = login_doc.find('input', value="Login")
        login_form = login_button.findParent("form")
        login_data = {
            elem["name"]: elem["value"] for elem in login_form("input")
            if elem.has_attr("name") and elem.has_attr("value")
        }
        login_data["username"] = username
        login_data["password"] = password
        # The following `requester` field is not used (at the time of
        # writing) but it ought to be associated with this new token so
        # that tokens can be selectively revoked a later date.
        login_data["requester"] = "%s@%s" % (getuser(), gethostname())

        # Log-in to MAAS.
        response = session.post(url_login, login_data)
        response.raise_for_status()

        # Request a new API token.
        create_data = {
            "csrfmiddlewaretoken": session.cookies["csrftoken"],
            "op": "create_authorisation_token",
        }
        create_headers = {
            "Accept": "application/json",
        }
        response = session.post(url_token, create_data, create_headers)
        response.raise_for_status()

        # We have it!
        token = response.json()
        return Credentials(
            token["consumer_key"],
            token["token_key"],
            token["token_secret"],
        )
