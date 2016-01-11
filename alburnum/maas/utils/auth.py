# Copyright 2012-2015 Canonical Ltd. Copyright 2015 Alburnum Ltd.
# This software is licensed under the GNU Affero General Public
# License version 3 (see the file LICENSE).

"""MAAS CLI authentication."""

__all__ = [
    'obtain_credentials',
    ]

from getpass import getpass
import sys

from alburnum.maas.utils.creds import Credentials


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
