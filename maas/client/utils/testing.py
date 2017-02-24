"""Testing helpers for `maas.client.utils`."""

from ..testing import make_name_without_spaces
from .creds import Credentials


def make_credentials():
    return Credentials(
        make_name_without_spaces('consumer_key'),
        make_name_without_spaces('token_key'),
        make_name_without_spaces('secret_key'),
    )
