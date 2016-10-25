"""Test helpers for `maas.client.flesh`."""

__all__ = [
    "capture_parse_error",
]

import argparse


def capture_parse_error(parser, *args):
    """Capture the `ArgumentError` arising from parsing the given arguments.

    `argparse` is hard to test (and to introspect, and extend... but it is
    good at what it does) so we have to use a pseudo-private method here.
    """
    namespace = argparse.Namespace()
    try:
        parser._parse_known_args(list(args), namespace)
    except argparse.ArgumentError as error:
        return error
    else:
        return None
