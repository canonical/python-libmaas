"""Objects for boot resources."""

__all__ = [
    "BootResource",
    "BootResources",
]

import enum
import hashlib
import httplib2
import io
from typing import Mapping

from . import (
    check,
    check_optional,
    mapping_of,
    Object,
    ObjectField,
    ObjectSet,
    ObjectType,
)
from .. import utils
from ..bones import CallError


def calc_size_and_sha265(content: io.IOBase, chunk_size: int):
    """Calculates the size and the sha2566 value of the content."""
    size = 0
    sha256 = hashlib.sha256()
    content.seek(0, io.SEEK_SET)
    while True:
        buf = content.read(chunk_size)
        length = len(buf)
        size += length
        sha256.update(buf)
        if length != chunk_size:
            break
    return size, sha256.hexdigest()


class BootResourceFiletype(enum.Enum):

    TGZ = "tgz"
    DDTGZ = "ddtgz"


class BootResourceFile(Object):
    """A boot resource file."""

    filename = ObjectField.Checked(
        "filename", check(str), readonly=True)
    filetype = ObjectField.Checked(
        "filetype", check(str), readonly=True)
    size = ObjectField.Checked(
        "size", check(int), readonly=True)
    sha256 = ObjectField.Checked(
        "sha256", check(str), readonly=True)
    complete = ObjectField.Checked(
        "complete", check(bool), readonly=True)


class BootResourceSet(Object):
    """A boot resource set."""

    version = ObjectField.Checked(
        "version", check(str), readonly=True)
    size = ObjectField.Checked(
        "size", check(int), readonly=True)
    label = ObjectField.Checked(
        "label", check(str), readonly=True)
    complete = ObjectField.Checked(
        "complete", check(bool), readonly=True)
    files = ObjectField.Checked(
        "files", mapping_of(BootResourceFile), default=None, readonly={})


class BootResourcesType(ObjectType):
    """Metaclass for `BootResources`."""

    def __iter__(cls):
        return map(cls._object, cls._handler.read())


class BootResources(ObjectSet, metaclass=BootResourcesType):
    """The set of boot resources."""

    @classmethod
    def read(cls):
        """Get list of `BootResource`'s.

        Each `BootResource` from the API is limited in that it does not
        contain the `sets` in the output. To get full data for each object
        a read needs to be performed on each object::

            resources = BootResources.read()
            resources = [
                BootResource.read(resource.id)
                for resource in resources
            ]

        """
        return cls(cls)

    @classmethod
    def create(
            cls, name: str, architecture: str, content: io.IOBase, *,
            title: str=None,
            filetype: BootResourceFiletype=BootResourceFiletype.TGZ,
            chunk_size=(1 << 22)):
        """Create a `BootResource`.

        Creates an uploaded boot resource with `content`. The `content` is
        uploaded in chunks of `chunk_size`. `content` must be seekable as the
        first pass through the `content` will calculate the size and sha256
        value then the second pass will perform the actual upload.

        :param name: Name of the boot resource. Must be in format 'os/release'.
        :type name: `str`
        :param architecture: Architecture of the boot resource. Must be in
            format 'arch/subarch'.
        :type architecture: `str`
        :param content: Content of the boot resource.
        :type content: `io.IOBase`
        :param title: Title of the boot resource.
        :type title: `str`
        :param filetype: Type of file in content.
        :type filetype: `str`
        :param chunk_size: Size in bytes to upload to MAAS in chunks.
            (Default is 4 MiB).
        :type chunk_size: `int`
        :returns: Create boot resource.
        :rtype: `BootResource`.
        """
        if not isinstance(name, str):
            raise TypeError("name must be a str, not %s" % type(name).__name__)
        elif '/' not in name:
            raise ValueError(
                "name must be in format os/release; missing '/'.")
        if not isinstance(architecture, str):
            raise TypeError(
                "architecture must be a str, not %s" % (
                    type(architecture).__name__))
        elif '/' not in architecture:
            raise ValueError(
                "architecture must be in format arch/subarch; missing '/'.")
        if not isinstance(content, io.IOBase):
            raise TypeError(
                "content must extend from io.IOBase; %s does not." % (
                    type(content).__name__))
        elif not content.readable():
            raise ValueError("content must be readable.")
        elif not content.seekable():
            raise ValueError("content must be seekable.")
        if title is None:
            title = ""
        if not isinstance(title, str):
            raise TypeError(
                "title must be a str, not %s" % type(title).__name__)
        if not isinstance(filetype, BootResourceFiletype):
            raise TypeError(
                "filetype must be a BootResourceFiletype, not %s" % (
                    type(filetype).__name__))
        if not isinstance(chunk_size, int):
            raise TypeError(
                "chunk_size must be a int, not %s" % (
                    type(chunk_size).__name__))
        elif chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than 0, not %d" % chunk_size)

        size, sha256 = calc_size_and_sha265(content, chunk_size)
        resource = cls._object(cls._handler.create(
            name=name, architecture=architecture, title=title,
            filetype=filetype.value, size=str(size), sha256=sha256))
        newest_set = sorted(resource.sets.keys(), reverse=True)[0]
        resource_set = resource.sets[newest_set]
        rfile = list(resource_set.files.values())[0]
        if rfile.complete:
            # Already created and fully up-to-date.
            return resource
        else:
            # Upload in chunks and reload boot resource.
            cls._upload_chunk(rfile, content, chunk_size)
            return cls._object.read(resource.id)

    @classmethod
    def _upload_chunk(
            cls, rfile: BootResourceFile, content: io.IOBase, chunk_size: int):
        content.seek(0, io.SEEK_SET)
        upload_uri = "%s%s" % (
            cls._handler.uri[:len(cls._handler.uri)-len(cls._handler.path)],
            rfile._data['upload_uri'])
        while True:
            buf = content.read(chunk_size)
            length = len(buf)
            if length > 0:
                cls._put_chunk(upload_uri, buf)
            if length != chunk_size:
                break

    @classmethod
    def _put_chunk(cls, upload_uri: str, buf: bytes):
        # Build the correct headers.
        headers = {
            'Content-Type': 'application/octet-stream',
            'Content-Length': '%s' % len(buf),
        }
        credentials = cls._handler.session.credentials
        if credentials is not None:
            utils.sign(upload_uri, headers, credentials)

        # Perform upload of chunk.
        insecure = cls._handler.session.insecure
        http = httplib2.Http(disable_ssl_certificate_validation=insecure)
        response, content = http.request(
            upload_uri, "PUT", body=buf, headers=headers)
        if response.status != 200:
            request = {
                "body": buf,
                "headers": headers,
                "method": "PUT",
                "uri": upload_uri,
            }
            raise CallError(request, response, content, None)


class BootResourceType(ObjectType):

    def read(cls, id: int):
        """Get `BootResource` by `id`."""
        data = cls._handler.read(id=id)
        return cls(data)


class BootResource(Object, metaclass=BootResourceType):
    """A boot resource."""

    id = ObjectField.Checked(
        "id", check(int), readonly=True)
    type = ObjectField.Checked(
        "type", check(str), check(str), readonly=True)
    name = ObjectField.Checked(
        "name", check(str), check(str), readonly=True)
    architecture = ObjectField.Checked(
        "architecture", check(str), check(str), readonly=True)
    subarches = ObjectField.Checked(
        "subarches", check_optional(str), check_optional(str),
        default=None, readonly=True)
    sets = ObjectField.Checked(
        "sets", mapping_of(BootResourceSet), default=None, readonly=True)

    def __repr__(self):
        return super(BootResource, self).__repr__(
            fields={"type", "name", "architecture"})

    def delete(self):
        """Delete boot resource."""
        self._handler.delete(id=self.id)
