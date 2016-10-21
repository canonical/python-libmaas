""" Testing framework for alburnum.maas.viscera """

__all__ = ['bind']

from unittest.mock import MagicMock


def bind(cls, origin=None, handler=None):
    return cls.bind(
        (MagicMock() if origin is None else origin),
        (MagicMock() if handler is None else handler),
    )
