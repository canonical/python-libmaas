""" Custom errors for libmaas """

__all__ = [
    "MAASException",
    "OperationNotAllowed"
]


class MAASException(Exception):

    def __init__(self, msg, obj):
        super().__init__(msg)
        self.obj = obj


class OperationNotAllowed(Exception):
    """ MAAS says this operation cannot be performed. """


class ObjectNotLoaded(Exception):
    """ Object is not loaded. """


class CannotDelete(Exception):
    """ Object cannot be deleted. """
