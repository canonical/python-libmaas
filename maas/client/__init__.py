"""Basic entry points."""

from . import _client


def connect(url, *, apikey=None, insecure=False):
    """Connect to MAAS at `url` using a previously obtained API key.

    :param url: The URL of MAAS, e.g. http://maas.example.com:5240/MAAS/
    :param apikey: The API key to use, e.g.
        SkTvsyHhzkREvvdtNk:Ywn5FvXVupVPvNUhrN:cm3Q2f5naXYPYsrPDPfQy9Q9cUFaEgbM
    :param insecure: Whether to check TLS certificates when using HTTPS.

    :return: A client object.
    """
    from .viscera import Origin  # Lazy.
    profile, origin = Origin.connect(
        url, apikey=apikey, insecure=insecure)
    return _client.Client(origin)


def login(url, *, username=None, password=None, insecure=False):
    """Connect to MAAS at `url` with a user name and password.

    :param url: The URL of MAAS, e.g. http://maas.example.com:5240/MAAS/
    :param username: The user name to use, e.g. fred.
    :param password: The user's password.
    :param insecure: Whether to check TLS certificates when using HTTPS.

    :return: A client object.
    """
    from .viscera import Origin  # Lazy.
    profile, origin = Origin.login(
        url, username=username, password=password, insecure=insecure)
    return _client.Client(origin)
