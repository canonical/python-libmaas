"""Test for `maas.client.viscera.spaces`."""

import random

from testtools.matchers import Equals

from ..spaces import (
    DeleteDefaultSpace,
    Space,
    Spaces,
)

from .. testing import bind
from ...testing import (
    make_string_without_spaces,
    TestCase,
)


def make_origin():
    """
    Create a new origin with Spaces and Space. The former
    refers to the latter via the origin, hence why it must be bound.
    """
    return bind(Spaces, Space)


class TestSpaces(TestCase):

    def test__spaces_create(self):
        Spaces = make_origin().Spaces
        name = make_string_without_spaces()
        description = make_string_without_spaces()
        Spaces._handler.create.return_value = {
            "id": 1,
            "name": name,
            "description": description,
        }
        Spaces.create(
            name=name,
            description=description,
        )
        Spaces._handler.create.assert_called_once_with(
            name=name,
            description=description,
        )

    def test__spaces_read(self):
        """Spaces.read() returns a list of Spaces."""
        Spaces = make_origin().Spaces
        spaces = [
            {
                "id": random.randint(0, 100),
                "name": make_string_without_spaces(),
            }
            for _ in range(3)
        ]
        Spaces._handler.read.return_value = spaces
        spaces = Spaces.read()
        self.assertThat(len(spaces), Equals(3))


class TestSpace(TestCase):

    def test__space_get_default(self):
        Space = make_origin().Space
        Space._handler.read.return_value = {
            "id": 0,
            "name": make_string_without_spaces(),
        }
        Space.get_default()
        Space._handler.read.assert_called_once_with(
            id=0
        )

    def test__space_read(self):
        Space = make_origin().Space
        space = {
            "id": random.randint(0, 100),
            "name": make_string_without_spaces(),
        }
        Space._handler.read.return_value = space
        self.assertThat(Space.read(id=space["id"]), Equals(Space(space)))
        Space._handler.read.assert_called_once_with(id=space["id"])

    def test__space_delete(self):
        Space = make_origin().Space
        space_id = random.randint(1, 100)
        space = Space({
            "id": space_id,
            "name": make_string_without_spaces(),
        })
        space.delete()
        Space._handler.delete.assert_called_once_with(id=space_id)

    def test__space_delete_default(self):
        Space = make_origin().Space
        space = Space({
            "id": 0,
            "name": make_string_without_spaces(),
        })
        self.assertRaises(DeleteDefaultSpace, space.delete)
