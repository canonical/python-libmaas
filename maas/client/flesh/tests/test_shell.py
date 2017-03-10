"""Tests for `maas.client.flesh.shell`."""

import random
import sys

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

    def setUp(self):
        super(TestShell, self).setUp()
        # Start with no profiles, and no profile default.
        self.patch(shell.cmd_shell, "profile_name_choices", ())
        self.patch(shell.cmd_shell, "profile_name_default", None)

    def test_offers_profile_name_option_when_no_profiles_exist(self):
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

    def electAttribute(self):
        # We're going to use an attribute in this module as the means for an
        # external script to report back, so choose an unlikely-to-be-in-use
        # attribute.
        module = sys.modules[__name__]
        attrname = make_name_without_spaces("attr", sep="_")
        self.patch(module, attrname, None)
        return module, attrname

    def callShell(self, *options):
        parser = ArgumentParser()
        subparser = shell.cmd_shell.register(parser)
        options = subparser.parse_args(list(options))
        options.execute(options)

    def test_runs_script_when_specified(self):
        module, attrname = self.electAttribute()

        # Mimic a non-interactive invocation of `maas shell` with a script.
        source = "import %s as mod; mod.%s = __file__" % (__name__, attrname)
        script = self.makeFile("script.py", source.encode("utf-8"))
        self.callShell(str(script))

        # That attribute has been updated.
        self.assertThat(getattr(module, attrname), Equals(str(script)))

    def test_runs_stdin_when_not_interactive(self):
        module, attrname = self.electAttribute()

        # Mimic a non-interactive invocation of `maas shell`.
        self.patch(shell, "sys")
        shell.sys.stdin.isatty.return_value = False
        shell.sys.stdin.read.return_value = (
            "import %s as mod; mod.%s = __file__" % (__name__, attrname))
        self.callShell()

        # That attribute has been updated.
        self.assertThat(getattr(module, attrname), Equals("<stdin>"))
