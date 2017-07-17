"""Tests for `maas.client.viscera.tags`."""

from testtools.matchers import (
    Equals,
    IsInstance,
    MatchesStructure,
)

from .. import tags

from ..testing import bind
from ...testing import (
    make_string_without_spaces,
    TestCase,
)


def make_origin():
    """
    Create a new origin with Tag and Tags. The former
    refers to the latter via the origin, hence why it must be bound.
    """
    return bind(tags.Tags, tags.Tag)


class TestTags(TestCase):

    def test__tags_create(self):
        origin = make_origin()
        name = make_string_without_spaces()
        comment = make_string_without_spaces()
        origin.Tags._handler.create.return_value = {
            "name": name,
            "comment": comment,
        }
        tag = origin.Tags.create(
            name=name,
            comment=comment,
        )
        origin.Tags._handler.create.assert_called_once_with(
            name=name,
            comment=comment,
        )
        self.assertThat(tag, IsInstance(origin.Tag))
        self.assertThat(tag, MatchesStructure.byEquality(
            name=name, comment=comment))

    def test__tags_create_without_comment(self):
        origin = make_origin()
        name = make_string_without_spaces()
        comment = ""
        origin.Tags._handler.create.return_value = {
            "name": name,
            "comment": comment,
        }
        tag = origin.Tags.create(name=name)
        origin.Tags._handler.create.assert_called_once_with(name=name)
        self.assertThat(tag, IsInstance(origin.Tag))
        self.assertThat(tag, MatchesStructure.byEquality(
            name=name, comment=comment))

    def test__tags_read(self):
        """Tags.read() returns a list of tags."""
        Tags = make_origin().Tags
        tags = [
            {
                "name": make_string_without_spaces(),
                "comment": make_string_without_spaces(),
            }
            for _ in range(3)
        ]
        Tags._handler.read.return_value = tags
        tags = Tags.read()
        self.assertThat(len(tags), Equals(3))


class TestTag(TestCase):

    def test__tag_read(self):
        Tag = make_origin().Tag
        tag = {
            "name": make_string_without_spaces(),
            "comment": make_string_without_spaces(),
        }
        Tag._handler.read.return_value = tag
        self.assertThat(Tag.read(name=tag["name"]), Equals(Tag(tag)))
        Tag._handler.read.assert_called_once_with(name=tag["name"])

    def test__tag_delete(self):
        Tag = make_origin().Tag
        tag_name = make_string_without_spaces()
        tag = Tag({
            "name": tag_name,
            "comment": make_string_without_spaces(),
        })
        tag.delete()
        Tag._handler.delete.assert_called_once_with(name=tag_name)
