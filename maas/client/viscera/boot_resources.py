"""Objects for boot resources."""

__all__ = [
    "BootResource",
    "BootResources",
]

import enum
import hashlib
import io
from urllib.parse import urlparse

import aiohttp

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


class BootResourceFileType(enum.Enum):

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
        "files", mapping_of(BootResourceFile), default=None, readonly=True)


class BootResourcesType(ObjectType):
    """Metaclass for `BootResources`."""

    async def read(cls):
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
        data = await cls._handler.read()
        return cls(map(cls._object, data))

    async def start_import(cls):
        """Start the import of `BootResource`'s."""
        # Cannot use cls._handler.import() as import is a reserved statement.
        return getattr(cls._handler, "import")()

    async def stop_import(cls):
        """Stop the import of `BootResource`'s."""
        return cls._handler.stop_import()

    async def create(
            cls, name: str, architecture: str, content: io.IOBase, *,
            title: str="",
            filetype: BootResourceFileType=BootResourceFileType.TGZ,
            chunk_size=(1 << 22), progress_callback=None):
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
        :param progress_callback: Called to inform the current progress of the
            upload. One argument is passed with the progress as a precentage.
            If the resource was already complete and no content
            needed to be uploaded then this callback will never be called.
        :type progress_callback: Callable
        :returns: Create boot resource.
        :rtype: `BootResource`.
        """
        if '/' not in name:
            raise ValueError(
                "name must be in format os/release; missing '/'")
        if '/' not in architecture:
            raise ValueError(
                "architecture must be in format arch/subarch; missing '/'")
        if not content.readable():
            raise ValueError("content must be readable")
        elif not content.seekable():
            raise ValueError("content must be seekable")
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than 0, not %d" % chunk_size)

        size, sha256 = calc_size_and_sha265(content, chunk_size)
        resource = cls._object(await cls._handler.create(
            name=name, architecture=architecture, title=title,
            filetype=filetype.value, size=str(size), sha256=sha256))
        newest_set = max(resource.sets, default=None)
        assert newest_set is not None
        resource_set = resource.sets[newest_set]
        assert len(resource_set.files) == 1
        rfile = list(resource_set.files.values())[0]
        if rfile.complete:
            # Already created and fully up-to-date.
            return resource
        else:
            # Upload in chunks and reload boot resource.
            await cls._upload_chunks(
                rfile, content, chunk_size, progress_callback)
            return cls._object.read(resource.id)

    async def _upload_chunks(
            cls, rfile: BootResourceFile, content: io.IOBase, chunk_size: int,
            progress_callback=None):
        """Upload the `content` to `rfile` in chunks using `chunk_size`."""
        content.seek(0, io.SEEK_SET)
        upload_uri = urlparse(
            cls._handler.uri)._replace(path=rfile._data['upload_uri']).geturl()
        uploaded_size = 0

        insecure = cls._handler.session.insecure
        connector = aiohttp.TCPConnector(verify_ssl=(not insecure))
        session = aiohttp.ClientSession(connector=connector)

        async with session:
            while True:
                buf = content.read(chunk_size)
                length = len(buf)
                if length > 0:
                    uploaded_size += length
                    await cls._put_chunk(session, upload_uri, buf)
                    if progress_callback is not None:
                        progress_callback(uploaded_size / rfile.size)
                if length != chunk_size:
                    break

    async def _put_chunk(
            cls, session: aiohttp.ClientSession,
            upload_uri: str, buf: bytes):
        """Upload one chunk to `upload_uri`."""
        # Build the correct headers.
        headers = {
            'Content-Type': 'application/octet-stream',
            'Content-Length': '%s' % len(buf),
        }
        credentials = cls._handler.session.credentials
        if credentials is not None:
            utils.sign(upload_uri, headers, credentials)

        # Perform upload of chunk.
        async with await session.put(
                upload_uri, data=buf, headers=headers) as response:
            if response.status != 200:
                content = await response.read()
                request = {
                    "body": buf,
                    "headers": headers,
                    "method": "PUT",
                    "uri": upload_uri,
                }
                raise CallError(request, response, content, None)


class BootResources(ObjectSet, metaclass=BootResourcesType):
    """The set of boot resources."""


class BootResourceType(ObjectType):

    async def read(cls, id: int):
        """Get `BootResource` by `id`."""
        data = await cls._handler.read(id=id)
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

    async def delete(self):
        """Delete boot resource."""
        await self._handler.delete(id=self.id)
