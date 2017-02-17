"""Basic entry points."""

import threading as _threading


def _connect(url, *, apikey=None, insecure=False):
    """Make an `Origin` by connecting with an apikey.

    :return: A tuple of ``profile`` and ``origin``, where the former is an
        unsaved `Profile` instance, and the latter is an `Origin` instance
        made using the profile.
    """
    _load()
    return connect(url, apikey=apikey, insecure=insecure)


def _login(url, *, username=None, password=None, insecure=False):
    """Make an `Origin` by logging-in with a username and password.

    :return: A tuple of ``profile`` and ``origin``, where the former is an
        unsaved `Profile` instance, and the latter is an `Origin` instance
        made using the profile.
    """
    _load()
    return login(url, username=username, password=password, insecure=insecure)


# Begin with stubs. We keep the stubs in _connect and _login for run-time
# reference, for the curious, but also for testing, where we verify that the
# stubs' signatures perfectly match those of the concrete implementation.
connect = _connect
login = _login


# Paranoia, belt-n-braces, call it what you will: replace the stubs only when
# holding this lock, just in case.
_load_lock = _threading.RLock()


def _load():
    """Replace stubs with concrete implementations."""
    global connect, login
    with _load_lock:
        from .viscera import Origin
        connect = Origin.connect
        login = Origin.login
