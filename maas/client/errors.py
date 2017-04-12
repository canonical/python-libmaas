""" Custom errors for libmaas """

__all__ = [
    "OperationNotAllowed"
]


class OperationNotAllowed(Exception):
    """ MAAS says this operation cannot be performed. """
