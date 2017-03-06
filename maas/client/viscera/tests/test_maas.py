"""Tests for MAAS configuration and suchlike."""

from testtools.matchers import HasLength

from .. import maas
from ...testing import TestCase


def find_getters(cls):
    return {
        name[4:]: getattr(cls, name) for name in dir(cls)
        if name.startswith("get_") and name != "get_config"
    }


def find_setters(cls):
    return {
        name[4:]: getattr(cls, name) for name in dir(cls)
        if name.startswith("set_") and name != "set_config"
    }


class TestConfiguration(TestCase):

    def test__every_getter_has_a_setter_and_vice_versa(self):
        getters, setters = find_getters(maas.MAAS), find_setters(maas.MAAS)
        getters_without_setters = set(getters).difference(setters)
        self.assertThat(getters_without_setters, HasLength(0))
        setters_without_getters = set(setters).difference(getters)
        self.assertThat(setters_without_getters, HasLength(0))
