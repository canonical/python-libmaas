"""Test for `maas.client.viscera.boot_source_selections`."""

import random

from testtools.matchers import (
    Equals,
    MatchesStructure,
)

from .. import (
    boot_source_selections,
    boot_sources,
)
from ...testing import (
    make_name_without_spaces,
    TestCase,
)
from ..testing import bind


def make_origin():
    # Create a new origin with BootSourceSelections and BootSourceSelection.
    # The former refers to the latter via the origin, hence why it must be
    # bound.
    return bind(
        boot_source_selections.BootSourceSelections,
        boot_source_selections.BootSourceSelection)


def make_boot_source():
    return boot_sources.BootSource({
        "id": random.randint(0, 100),
        "url": "http://images.maas.io/ephemeral-v3/daily/",
        "keyring_filename": (
            "/usr/share/keyrings/ubuntu-cloudimage-keyring.gpg"),
        "keyring_data": "",
    })


class TestBootSourceSelection(TestCase):

    def test__string_representation_includes_defined_keys(self):
        selection = boot_source_selections.BootSourceSelection({
            "os": make_name_without_spaces("os"),
            "release": make_name_without_spaces("release"),
            "arches": [make_name_without_spaces("arch")],
            "subarches": [make_name_without_spaces("subarches")],
            "labels": [make_name_without_spaces("labels")],
        }, {
            "boot_source_id": random.randint(0, 100),
        })
        self.assertThat(repr(selection), Equals(
            "<BootSourceSelection arches=%(arches)r labels=%(labels)r "
            "os=%(os)r release=%(release)r subarches=%(subarches)r>" % (
                selection._data)))

    def test__read_raises_TypeError_when_no_BootSource(self):
        BootSourceSelection = make_origin().BootSourceSelection
        self.assertRaises(
            TypeError, BootSourceSelection.read,
            random.randint(0, 100), random.randint(0, 100))

    def test__read(self):
        source = make_boot_source()
        selection_id = random.randint(0, 100)
        os = make_name_without_spaces("os")
        release = make_name_without_spaces("release")
        arches = [make_name_without_spaces("arch")]
        subarches = [make_name_without_spaces("subarches")]
        labels = [make_name_without_spaces("labels")]

        BootSourceSelection = make_origin().BootSourceSelection
        BootSourceSelection._handler.read.return_value = {
            "id": selection_id, "os": os, "release": release,
            "arches": arches, "subarches": subarches, "labels": labels}

        selection = BootSourceSelection.read(source, selection_id)
        BootSourceSelection._handler.read.assert_called_once_with(
            boot_source_id=source.id, id=selection_id)
        self.assertThat(selection, MatchesStructure.byEquality(
            id=selection_id, boot_source_id=source.id, os=os, release=release,
            arches=arches, subarches=subarches, labels=labels))

    def test__delete(self):
        source = make_boot_source()
        selection_id = random.randint(0, 100)
        os = make_name_without_spaces("os")
        release = make_name_without_spaces("release")
        arches = [make_name_without_spaces("arch")]
        subarches = [make_name_without_spaces("subarches")]
        labels = [make_name_without_spaces("labels")]

        BootSourceSelection = make_origin().BootSourceSelection
        selection = BootSourceSelection({
            "id": selection_id, "os": os, "release": release,
            "arches": arches, "subarches": subarches, "labels": labels}, {
            "boot_source_id": source.id})

        selection.delete()
        BootSourceSelection._handler.delete.assert_called_once_with(
            boot_source_id=source.id, id=selection_id)


class TestBootSources(TestCase):

    def test__read_raises_TypeError_when_no_BootSource(self):
        BootSourceSelections = make_origin().BootSourceSelections
        self.assertRaises(
            TypeError, BootSourceSelections.read, random.randint(0, 100))

    def test__read(self):
        source = make_boot_source()
        BootSourceSelections = make_origin().BootSourceSelections
        BootSourceSelections._handler.read.return_value = [
            {
                "id": random.randint(0, 9),
            },
            {
                "id": random.randint(10, 19),
            },
        ]

        selections = BootSourceSelections.read(source)
        self.assertEquals(2, len(selections))
        self.assertEquals(source.id, selections[0].boot_source_id)
        self.assertEquals(source.id, selections[1].boot_source_id)

    def test__create_raises_TypeError_when_no_BootSource(self):
        os = make_name_without_spaces("os")
        release = make_name_without_spaces("release")

        BootSourceSelections = make_origin().BootSourceSelections

        self.assertRaises(
            TypeError, BootSourceSelections.create,
            random.randint(0, 100), os, release)

    def test__create__without_kwargs(self):
        source = make_boot_source()
        selection_id = random.randint(0, 100)
        os = make_name_without_spaces("os")
        release = make_name_without_spaces("release")

        BootSourceSelections = make_origin().BootSourceSelections
        BootSourceSelections._handler.create.return_value = {
            "id": selection_id, "os": os, "release": release,
            "arches": ["*"], "subarches": ["*"], "labels": ["*"]}

        selection = BootSourceSelections.create(source, os, release)
        BootSourceSelections._handler.create.assert_called_once_with(
            boot_source_id=source.id, os=os, release=release,
            arches=["*"], subarches=["*"], labels=["*"])
        self.assertThat(selection, MatchesStructure.byEquality(
            id=selection_id, boot_source_id=source.id, os=os, release=release,
            arches=["*"], subarches=["*"], labels=["*"]))

    def test__create__with_kwargs(self):
        source = make_boot_source()
        selection_id = random.randint(0, 100)
        os = make_name_without_spaces("os")
        release = make_name_without_spaces("release")
        arches = [make_name_without_spaces("arch")]
        subarches = [make_name_without_spaces("subarches")]
        labels = [make_name_without_spaces("labels")]

        BootSourceSelections = make_origin().BootSourceSelections
        BootSourceSelections._handler.create.return_value = {
            "id": selection_id, "os": os, "release": release,
            "arches": arches, "subarches": subarches, "labels": labels}

        selection = BootSourceSelections.create(
            source, os, release,
            arches=arches, subarches=subarches, labels=labels)
        BootSourceSelections._handler.create.assert_called_once_with(
            boot_source_id=source.id, os=os, release=release,
            arches=arches, subarches=subarches, labels=labels)
        self.assertThat(selection, MatchesStructure.byEquality(
            id=selection_id, boot_source_id=source.id, os=os, release=release,
            arches=arches, subarches=subarches, labels=labels))
