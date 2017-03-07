"""MAAS CLI authentication."""

__all__ = [
    "obtain_credentials",
    "try_getpass",
]

from getpass import getpass
import sys

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
