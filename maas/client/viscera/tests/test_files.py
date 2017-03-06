"""Test for `maas.client.viscera.files`."""

from testtools.matchers import (
    AllMatch,
    IsInstance,
    MatchesSetwise,
    MatchesStructure,
)

from .. import files
from ...testing import (
    make_name_without_spaces,
    TestCase,
)
from ..testing import bind


def make_origin():
    # Create a new origin with Files and File. The former refers to the
    # latter via the origin, hence why it must be bound.
    origin = bind(files.Files, files.File)
    return origin


class TestFiles(TestCase):
    """Tests for `Files`."""

    def test__read(self):
        origin = make_origin()

        data = [
            {"filename": make_name_without_spaces()},
            {"filename": make_name_without_spaces()},
        ]
        origin.Files._handler.read.return_value = data

        resources = origin.Files.read()
        self.assertEquals(2, len(resources))
        self.assertThat(resources, IsInstance(origin.Files))
        self.assertThat(resources, AllMatch(IsInstance(origin.File)))
        self.assertThat(resources, MatchesSetwise(*(
            MatchesStructure.byEquality(filename=entry["filename"])
            for entry in data
        )))


class TestFile(TestCase):
    """Tests for `File`."""

    def test__read(self):
        origin = make_origin()
        data = {"filename": make_name_without_spaces()}
        self.assertThat(
            origin.File(data), MatchesStructure.byEquality(
                filename=data["filename"]))
