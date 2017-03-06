"""Tests for `maas.client.flesh.shell`."""

import random

from testtools.matchers import (
    Contains,
    Equals,
    Is,
)

from .. import (
    ArgumentParser,
    shell,
)
from ...testing import (
    make_name_without_spaces,
    TestCase,
)
from .testing import capture_parse_error


class TestShell(TestCase):
    """Tests for `cmd_shell`."""

    def test_offers_profile_name_option_when_no_profiles_exist(self):
        self.patch(shell.cmd_shell, "profile_name_choices", ())
        self.patch(shell.cmd_shell, "profile_name_default", None)

        parser = ArgumentParser()
        subparser = shell.cmd_shell.register(parser)

        # By default, the profile_name option is None.
        options = subparser.parse_args([])
        self.assertThat(options.profile_name, Is(None))

        # But any profile name can be given.
        profile_name = make_name_without_spaces("profile-name")
        options = subparser.parse_args(["--profile-name", profile_name])
        self.assertThat(options.profile_name, Equals(profile_name))

    def test_offers_profile_name_option_when_profiles_exist(self):
        profile_name_choices = tuple(
            make_name_without_spaces("profile-name") for _ in range(5))
        profile_name_default = random.choice(profile_name_choices)

        self.patch(
            shell.cmd_shell, "profile_name_choices", profile_name_choices)
        self.patch(
            shell.cmd_shell, "profile_name_default", profile_name_default)

        parser = ArgumentParser()
        subparser = shell.cmd_shell.register(parser)

        # By default, the profile_name option is profile_name_default.
        options = subparser.parse_args([])
        self.assertThat(options.profile_name, Equals(profile_name_default))

        # But any profile name in profile_name_choices can be given.
        profile_name = random.choice(profile_name_choices)
        options = subparser.parse_args(["--profile-name", profile_name])
        self.assertThat(options.profile_name, Equals(profile_name))

        # Other profile names are not permitted.
        self.patch(subparser, "error").side_effect = Exception
        profile_name = make_name_without_spaces("foo")
        error = capture_parse_error(subparser, "--profile-name", profile_name)
        self.assertThat(str(error), Contains(
            "argument --profile-name: invalid choice: "))
