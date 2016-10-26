"""Test for `maas.client.viscera.boot_resources`."""

__all__ = []

import hashlib
import httplib2
import io
import random

from testtools.matchers import (
    Equals,
    MatchesDict,
    MatchesStructure,
)
from unittest.mock import (
    call,
    MagicMock,
    sentinel,
)

from .. import boot_resources
from ..testing import bind
from ...testing import (
    make_string,
    make_name_without_spaces,
    pick_bool,
    TestCase,
)


def make_origin():
    # Create a new origin with BootResources and BootResource. The former
    # refers to the latter via the origin, hence why it must be bound.
    return bind(boot_resources.BootResources, boot_resources.BootResource)


class TestBootResource(TestCase):

    def test__string_representation_includes_type_name_architecture(self):
        source = boot_resources.BootResource({
            "id": random.randint(0, 100),
            "type": "Synced",
            "name": "ubuntu/xenial",
            "architecture": "amd64/ga-16.04",
            "subarches": "generic,ga-16.04",
        })
        self.assertThat(repr(source), Equals(
            "<BootResource architecture=%(architecture)r name=%(name)r "
            "type=%(type)r>" % (
                source._data)))

    def test__read(self):
        resource_id = random.randint(0, 100)
        rtype = random.choice(["Synced", "Uploaded", "Generated"])
        name = "%s/%s" % (
            make_name_without_spaces("os"),
            make_name_without_spaces("release"))
        architecture = "%s/%s" % (
            make_name_without_spaces("arch"),
            make_name_without_spaces("subarch"))
        subarches = ",".join([
            make_name_without_spaces("subarch")
            for _ in range(3)
        ])
        sets = {}
        for _ in range(3):
            version = make_name_without_spaces("version")
            files = {}
            for _ in range(3):
                filename = make_name_without_spaces("filename")
                files[filename] = {
                    "filename": filename,
                    "filetype": make_name_without_spaces("filetype"),
                    "size": random.randint(1000, 10000),
                    "sha256": make_name_without_spaces("sha256"),
                    "complete": pick_bool(),
                }
            sets[version] = {
                "version": version,
                "size": random.randint(1000, 10000),
                "label": make_name_without_spaces("label"),
                "complete": pick_bool(),
                "files": files,
            }

        BootResource = make_origin().BootResource
        BootResource._handler.read.return_value = {
            "id": resource_id, "type": rtype, "name": name,
            "architecture": architecture, "subarches":subarches,
            "sets": sets}

        resource = BootResource.read(resource_id)
        BootResource._handler.read.assert_called_once_with(id=resource_id)
        self.assertThat(resource, MatchesStructure(
            id=Equals(resource_id),
            type=Equals(rtype),
            name=Equals(name),
            architecture=Equals(architecture),
            subarches=Equals(subarches),
            sets=MatchesDict({
                version: MatchesStructure(
                    version=Equals(version),
                    size=Equals(rset["size"]),
                    label=Equals(rset["label"]),
                    complete=Equals(rset["complete"]),
                    files=MatchesDict({
                        filename: MatchesStructure(
                            filename=Equals(filename),
                            filetype=Equals(rfile["filetype"]),
                            size=Equals(rfile["size"]),
                            sha256=Equals(rfile["sha256"]),
                            complete=Equals(rfile["complete"]),
                        )
                        for filename, rfile in rset["files"].items()
                    }),
                )
                for version, rset in sets.items()
            })))

    def test__delete(self):
        resource_id = random.randint(0, 100)

        BootResource = make_origin().BootResource
        resource = BootResource({
            "id": resource_id,
            "type": "Synced",
            "name": "ubuntu/xenial",
            "architecture": "amd64/ga-16.04",
            "subarches": "generic,ga-16.04",
        })

        resource.delete()
        BootResource._handler.delete.assert_called_once_with(id=resource_id)


class TestBootResources(TestCase):

    def test__read(self):
        BootResources = make_origin().BootResources
        BootResources._handler.read.return_value = [
            {
                "id": random.randint(0, 9),
            },
            {
                "id": random.randint(10, 19),
            },
        ]

        resources = BootResources.read()
        self.assertEquals(2, len(resources))

    def test__start_import(self):
        BootResources = make_origin().BootResources
        import_action = getattr(BootResources._handler, "import")
        import_action.return_value = sentinel.result

        self.assertEquals(sentinel.result, BootResources.start_import())
        import_action.assert_called_once_with()

    def test__stop_import(self):
        BootResources = make_origin().BootResources
        BootResources._handler.stop_import.return_value = sentinel.result

        self.assertEquals(sentinel.result, BootResources.stop_import())
        BootResources._handler.stop_import.assert_called_once_with()

    def test__create_raises_TypeError_when_name_not_str(self):
        BootResources = make_origin().BootResources

        error = self.assertRaises(TypeError, BootResources.create, 1, 1, 1)
        self.assertEquals(
            "name must be a str, not int", str(error))

    def test__create_raises_ValueError_when_name_missing_slash(self):
        BootResources = make_origin().BootResources

        error = self.assertRaises(ValueError, BootResources.create, "", 1, 1)
        self.assertEquals(
            "name must be in format os/release; missing '/'", str(error))

    def test__create_raises_TypeError_when_architecture_not_str(self):
        BootResources = make_origin().BootResources

        error = self.assertRaises(
            TypeError, BootResources.create, "os/release", 1, 1)
        self.assertEquals(
            "architecture must be a str, not int", str(error))

    def test__create_raises_ValueError_when_architecture_missing_slash(self):
        BootResources = make_origin().BootResources

        error = self.assertRaises(
            ValueError, BootResources.create, "os/release", "", 1)
        self.assertEquals(
            "architecture must be in format arch/subarch; missing '/'",
            str(error))

    def test__create_raises_TypeError_when_content_not_from_IOBase(self):
        BootResources = make_origin().BootResources

        error = self.assertRaises(
            TypeError, BootResources.create,
            "os/release", "arch/subarch", "")
        self.assertEquals(
            "content must extend from io.IOBase; str does not", str(error))

    def test__create_raises_ValueError_when_content_cannot_be_read(self):
        BootResources = make_origin().BootResources

        buf = io.BytesIO(b"")
        self.patch(buf, "readable").return_value = False
        error = self.assertRaises(
            ValueError, BootResources.create,
            "os/release", "arch/subarch", buf)
        self.assertEquals(
            "content must be readable", str(error))

    def test__create_raises_ValueError_when_content_cannot_seek(self):
        BootResources = make_origin().BootResources

        buf = io.BytesIO(b"")
        self.patch(buf, "seekable").return_value = False
        error = self.assertRaises(
            ValueError, BootResources.create,
            "os/release", "arch/subarch", buf)
        self.assertEquals(
            "content must be seekable", str(error))

    def test__create_raises_TypeError_when_title_not_str(self):
        BootResources = make_origin().BootResources

        buf = io.BytesIO(b"")
        error = self.assertRaises(
            TypeError, BootResources.create,
            "os/release", "arch/subarch", buf, title=1)
        self.assertEquals(
            "title must be a str, not int", str(error))

    def test__create_raises_TypeError_when_filetype_not_enum(self):
        BootResources = make_origin().BootResources

        buf = io.BytesIO(b"")
        error = self.assertRaises(
            TypeError, BootResources.create,
            "os/release", "arch/subarch", buf, filetype="tgz")
        self.assertEquals(
            "filetype must be a BootResourceFiletype, not str", str(error))

    def test__create_raises_TypeError_when_chunk_size_not_int(self):
        BootResources = make_origin().BootResources

        buf = io.BytesIO(b"")
        error = self.assertRaises(
            TypeError, BootResources.create,
            "os/release", "arch/subarch", buf, chunk_size="")
        self.assertEquals(
            "chunk_size must be a int, not str", str(error))

    def test__create_raises_ValueError_when_chunk_size_is_zero(self):
        BootResources = make_origin().BootResources

        buf = io.BytesIO(b"")
        error = self.assertRaises(
            ValueError, BootResources.create,
            "os/release", "arch/subarch", buf, chunk_size=0)
        self.assertEquals(
            "chunk_size must be greater than 0, not 0", str(error))

    def test__create_raises_ValueError_when_chunk_size_is_less_than_zero(self):
        BootResources = make_origin().BootResources

        buf = io.BytesIO(b"")
        error = self.assertRaises(
            ValueError, BootResources.create,
            "os/release", "arch/subarch", buf, chunk_size=-1)
        self.assertEquals(
            "chunk_size must be greater than 0, not -1", str(error))

    def test__create_calls_create_on_handler_does_nothing_if_complete(self):
        resource_id = random.randint(0, 100)
        name = "%s/%s" % (
            make_name_without_spaces("os"),
            make_name_without_spaces("release"))
        architecture = "%s/%s" % (
            make_name_without_spaces("arch"),
            make_name_without_spaces("subarch"))
        title = make_name_without_spaces("title")
        filetype = random.choice([
            boot_resources.BootResourceFiletype.TGZ,
            boot_resources.BootResourceFiletype.DDTGZ])

        data = make_string().encode("ascii")
        sha256 = hashlib.sha256()
        sha256.update(data)
        sha256 = sha256.hexdigest()
        size = len(data)
        buf = io.BytesIO(data)

        BootResources = make_origin().BootResources
        BootResources._handler.create.return_value = {
            "id": resource_id,
            "type": "Uploaded",
            "name": name,
            "architecture": architecture,
            "sets": {
                "20161026": {
                    "version": "20161026",
                    "size": size,
                    "label": "uploaded",
                    "complete": True,
                    "files": {
                        "root-tgz": {
                            "filename": "root-tgz",
                            "filetype": "root-dd",
                            "size": size,
                            "sha256": sha256,
                            "complete": True,
                        }
                    }
                }
            }
        }
        mock_upload_chunks = self.patch(BootResources, "_upload_chunks")

        resource = BootResources.create(
            name, architecture, buf, title=title, filetype=filetype)
        self.assertThat(resource, MatchesStructure.byEquality(
            id=resource_id, type="Uploaded",
            name=name, architecture=architecture))
        self.assertFalse(mock_upload_chunks.called)

    def test__create_uploads_in_chunks_and_reloads_resource(self):
        resource_id = random.randint(0, 100)
        name = "%s/%s" % (
            make_name_without_spaces("os"),
            make_name_without_spaces("release"))
        architecture = "%s/%s" % (
            make_name_without_spaces("arch"),
            make_name_without_spaces("subarch"))
        title = make_name_without_spaces("title")
        filetype = random.choice([
            boot_resources.BootResourceFiletype.TGZ,
            boot_resources.BootResourceFiletype.DDTGZ])
        upload_uri = "/MAAS/api/2.0/boot-resources/%d/upload/1" % resource_id

        # Make chunks and upload in pieces of 4, where the last piece is
        # smaller than chunk size.
        chunk_size = random.randint(10, 100)
        data = make_string(int(chunk_size * 3.25)).encode("ascii")
        sha256 = hashlib.sha256()
        sha256.update(data)
        sha256 = sha256.hexdigest()
        size = len(data)
        buf = io.BytesIO(data)

        # Mock the handler calls. BootResource.read will be called after the
        # upload is complete to get the updated object.
        origin = make_origin()
        BootResources = origin.BootResources
        BootResource = origin.BootResource
        BootResources._handler.uri = (
            "http://localhost:5240/MAAS/api/2.0/boot-resources/")
        BootResources._handler.path = "/MAAS/api/2.0/boot-resources/"
        BootResources._handler.create.return_value = {
            "id": resource_id,
            "type": "Uploaded",
            "name": name,
            "architecture": architecture,
            "sets": {
                "20161026": {
                    "version": "20161026",
                    "size": size,
                    "label": "uploaded",
                    "complete": False,
                    "files": {
                        "root-tgz": {
                            "filename": "root-tgz",
                            "filetype": "root-dd",
                            "size": size,
                            "sha256": sha256,
                            "complete": False,
                            "upload_uri": upload_uri,
                        }
                    }
                }
            }
        }
        BootResource._handler.read.return_value = {
            "id": resource_id,
            "type": "Uploaded",
            "name": name,
            "architecture": architecture,
            "sets": {
                "20161026": {
                    "version": "20161026",
                    "size": size,
                    "label": "uploaded",
                    "complete": True,
                    "files": {
                        "root-tgz": {
                            "filename": "root-tgz",
                            "filetype": "root-dd",
                            "size": size,
                            "sha256": sha256,
                            "complete": True,
                        }
                    }
                }
            }
        }

        # Mock signing. Test checks that its actually called.
        mock_sign = self.patch(boot_resources.utils, "sign")

        # Mock the httplib as the create performs PUT directly to the API.
        http = MagicMock()
        http.return_value.request.return_value = (
            httplib2.Response({"status": 200}), b"")
        self.patch(boot_resources.httplib2, "Http", http)

        resource = BootResources.create(
            name, architecture, buf,
            title=title, filetype=filetype, chunk_size=chunk_size)

        # Check that returned resource is correct and updated.
        self.assertThat(resource, MatchesStructure.byEquality(
            id=resource_id, type="Uploaded",
            name=name, architecture=architecture))
        self.assertTrue(resource.sets["20161026"].complete)

        # Check that sign was called.
        self.assertTrue(mock_sign.called)

        # Check that the PUT was called for each chunk.
        calls = [
            call(
                "http://localhost:5240/MAAS/api/2.0/"
                "boot-resources/%d/upload/1" % resource_id,
                "PUT", body=data[0 + i:chunk_size + i],
                headers={
                    'Content-Type': 'application/octet-stream',
                    'Content-Length': str(len(data[0 + i:chunk_size + i])),
                })
            for i in range(0, len(data), chunk_size)
        ]
        self.assertEquals(calls, http.return_value.request.call_args_list)

    def test__create_raises_CallError_on_chunk_upload_failure(self):
        resource_id = random.randint(0, 100)
        name = "%s/%s" % (
            make_name_without_spaces("os"),
            make_name_without_spaces("release"))
        architecture = "%s/%s" % (
            make_name_without_spaces("arch"),
            make_name_without_spaces("subarch"))
        title = make_name_without_spaces("title")
        filetype = random.choice([
            boot_resources.BootResourceFiletype.TGZ,
            boot_resources.BootResourceFiletype.DDTGZ])
        upload_uri = "/MAAS/api/2.0/boot-resources/%d/upload/1" % resource_id

        # Make chunks and upload in pieces of 4, where the last piece is
        # smaller than chunk size.
        chunk_size = random.randint(10, 100)
        data = make_string(int(chunk_size * 3.25)).encode("ascii")
        sha256 = hashlib.sha256()
        sha256.update(data)
        sha256 = sha256.hexdigest()
        size = len(data)
        buf = io.BytesIO(data)

        # Mock the handler calls. BootResource.read will be called after the
        # upload is complete to get the updated object.
        origin = make_origin()
        BootResources = origin.BootResources
        BootResource = origin.BootResource
        BootResources._handler.uri = (
            "http://localhost:5240/MAAS/api/2.0/boot-resources/")
        BootResources._handler.path = "/MAAS/api/2.0/boot-resources/"
        BootResources._handler.create.return_value = {
            "id": resource_id,
            "type": "Uploaded",
            "name": name,
            "architecture": architecture,
            "sets": {
                "20161026": {
                    "version": "20161026",
                    "size": size,
                    "label": "uploaded",
                    "complete": False,
                    "files": {
                        "root-tgz": {
                            "filename": "root-tgz",
                            "filetype": "root-dd",
                            "size": size,
                            "sha256": sha256,
                            "complete": False,
                            "upload_uri": upload_uri,
                        }
                    }
                }
            }
        }

        # Mock signing. Test checks that its actually called.
        mock_sign = self.patch(boot_resources.utils, "sign")

        # Mock the httplib as the create performs PUT directly to the API.
        http = MagicMock()
        http.return_value.request.return_value = (
            httplib2.Response({"status": 500}), b"Error")
        self.patch(boot_resources.httplib2, "Http", http)

        self.assertRaises(
            boot_resources.CallError, BootResources.create,
            name, architecture, buf,
            title=title, filetype=filetype, chunk_size=chunk_size)
