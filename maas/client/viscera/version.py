"""Objects for version."""

__all__ = [
    "Version",
]

from distutils.version import StrictVersion

from . import (
    Object,
    ObjectField,
    ObjectType,
)


def parse_version(version):
    return StrictVersion(version).version


class VersionType(ObjectType):
    """Metaclass for `Version`."""

    async def read(cls):
        data = await cls._handler.read()
        return cls(data)


class Version(Object, metaclass=VersionType):
    """MAAS version information."""

    version = ObjectField(
        "version", readonly=True)
    version_info = ObjectField.Checked(
        "version", parse_version, readonly=True)
    subversion = ObjectField(
        "subversion", readonly=True)
    capabilities = ObjectField.Checked(
        "capabilities", frozenset, readonly=True)

    def __repr__(self):
        return "<%s %s %s [%s]>" % (
            self.__class__.__name__, self.version, self.subversion,
            " ".join(sorted(self.capabilities)))
