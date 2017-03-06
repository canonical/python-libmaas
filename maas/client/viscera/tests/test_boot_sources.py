"""Test for `maas.client.viscera.boot_sources`."""

import random

from testtools.matchers import (
    Equals,
    MatchesStructure,
)

from .. import boot_sources
from ...testing import (
    make_name_without_spaces,
    TestCase,
)
from ..testing import bind


def make_origin():
    # Create a new origin with BootSources and BootSource. The former refers
    # to the latter via the origin, hence why it must be bound.
    return bind(boot_sources.BootSources, boot_sources.BootSource)


class TestBootSource(TestCase):

    def test__string_representation_includes_url_keyring_info_only(self):
        source = boot_sources.BootSource({
            "url": "http://images.maas.io/ephemeral-v3/daily/",
            "keyring_filename": (
                "/usr/share/keyrings/ubuntu-cloudimage-keyring.gpg"),
            "keyring_data": "",
        })
        self.assertThat(repr(source), Equals(
            "<BootSource keyring_data=%(keyring_data)r "
            "keyring_filename=%(keyring_filename)r url=%(url)r>" % (
                source._data)))

    def test__read(self):
        source_id = random.randint(0, 100)
        url = "http://images.maas.io/ephemeral-v3/daily/"
        keyring_filename = (
            "/usr/share/keyrings/ubuntu-cloudimage-keyring.gpg")

        BootSource = make_origin().BootSource
        BootSource._handler.read.return_value = {
            "id": source_id, "url": url,
            "keyring_filename": keyring_filename, "keyring_data": ""}

        source = BootSource.read(source_id)
        BootSource._handler.read.assert_called_once_with(id=source_id)
        self.assertThat(source, MatchesStructure.byEquality(
            id=source_id, url=url, keyring_filename=keyring_filename,
            keyring_data=""))

    def test__delete(self):
        source_id = random.randint(0, 100)

        BootSource = make_origin().BootSource
        source = BootSource({
            "id": source_id,
            "url": "http://images.maas.io/ephemeral-v3/daily/",
            "keyring_filename": (
                "/usr/share/keyrings/ubuntu-cloudimage-keyring.gpg"),
            "keyring_data": "",
        })

        source.delete()
        BootSource._handler.delete.assert_called_once_with(id=source_id)


class TestBootSources(TestCase):

    def test__read(self):
        BootSources = make_origin().BootSources
        BootSources._handler.read.return_value = [
            {
                "id": random.randint(0, 9),
            },
            {
                "id": random.randint(10, 19),
            },
        ]

        sources = BootSources.read()
        self.assertEquals(2, len(sources))

    def test__create_calls_create_with_keyring_filename(self):
        source_id = random.randint(0, 100)
        url = "http://images.maas.io/ephemeral-v3/daily/"
        keyring_filename = (
            "/usr/share/keyrings/ubuntu-cloudimage-keyring.gpg")

        BootSources = make_origin().BootSources
        BootSources._handler.create.return_value = {
            "id": source_id, "url": url,
            "keyring_filename": keyring_filename, "keyring_data": ""}

        source = BootSources.create(url, keyring_filename=keyring_filename)
        BootSources._handler.create.assert_called_once_with(
            url=url, keyring_filename=keyring_filename, keyring_data="")
        self.assertThat(source, MatchesStructure.byEquality(
            id=source_id, url=url,
            keyring_filename=keyring_filename, keyring_data=""))

    def test__create_calls_create_with_keyring_data(self):
        source_id = random.randint(0, 100)
        url = "http://images.maas.io/ephemeral-v3/daily/"
        keyring_data = make_name_without_spaces("data")

        BootSources = make_origin().BootSources
        BootSources._handler.create.return_value = {
            "id": source_id, "url": url,
            "keyring_filename": "", "keyring_data": keyring_data}

        source = BootSources.create(url, keyring_data=keyring_data)
        BootSources._handler.create.assert_called_once_with(
            url=url, keyring_filename="", keyring_data=keyring_data)
        self.assertThat(source, MatchesStructure.byEquality(
            id=source_id, url=url,
            keyring_filename="", keyring_data=keyring_data))

    def test__create_calls_create_with_unsigned_url(self):
        source_id = random.randint(0, 100)
        url = "http://images.maas.io/ephemeral-v3/daily/streams/v1/index.json"

        BootSources = make_origin().BootSources
        BootSources._handler.create.return_value = {
            "id": source_id, "url": url,
            "keyring_filename": "", "keyring_data": ""}

        source = BootSources.create(url)
        BootSources._handler.create.assert_called_once_with(
            url=url, keyring_filename="", keyring_data="")
        self.assertThat(source, MatchesStructure.byEquality(
            id=source_id, url=url,
            keyring_filename="", keyring_data=""))
