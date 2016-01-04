# Copyright 2015 Alburnum Ltd. This software is licensed under
# the GNU Affero General Public License version 3 (see LICENSE).

"""Shell for interacting with a remote MAAS (https://maas.ubuntu.com/)."""

__all__ = [
    "Shell",
]

import cmd
import shlex

from alburnum.maas import utils
import colorclass
import terminaltables


def with_trailing_space(name):
    """Add a trailing space to a non-empty string.

    This is useful when generating completion choices; when the completion is
    unambiguous, <tab> will accept the whole completion and move the cursor
    one space after the completed text.
    """
    return (name) if name.endswith(" ") else (name + " ")


class ShellType(type):
    """Metaclass for the MAAS shell."""

    def __new__(cls, name, bases, attrs):
        for name, attr in attrs.items():
            if name.startswith("do_") and callable(attr):
                title, body = utils.parse_docstring(attr)
                if len(body) > 0:
                    attr.__doc__ = title + "\n\n" + body
                else:
                    attr.__doc__ = title
        return super(ShellType, cls).__new__(cls, name, bases, attrs)


class Shell(cmd.Cmd, metaclass=ShellType):
    """The MAAS shell."""

    # Improve the clarity of the default, and add a full-stop in order that
    # MAAS might alude to being developed by civilised human beings.
    nohelp = "*** No help for %s."

    # The name of the currently selected profile.
    profile_name = None

    @property
    def prompt(self):
        if self.stdin.isatty():
            if self.profile_name is None:
                return "(-) "
            else:
                return colorclass.Color(
                    "({autogreen}%s{/autogreen}) " % self.profile_name)
        else:
            return ""

    def switch_profile(self, profile_name):
        self.profile_name = profile_name

    def message(self, *parts):
        print(*parts, file=self.stdout)

    def error(self, message):
        stars = colorclass.Color("{autored}***{/autored}")
        print(stars, message, file=self.stdout)
        if not self.stdin.isatty():
            raise SystemExit(2)

    def make_table(self, data):
        if self.stdout.isatty():
            return terminaltables.SingleTable(data)
        else:
            return terminaltables.AsciiTable(data)

    def do_EOF(self, line):
        raise SystemExit(0)

    def completenames(self, text, *ignored):
        dotext = "do_" + text
        return sorted(
            with_trailing_space(name[3:]) for name in self.get_names()
            if name.startswith(dotext) and name != "do_EOF"
        )

    #
    # list
    #

    def do_list(self, line):
        """List all profiles."""
        rows = [["Profile name", "URL"]]

        with utils.ProfileConfig.open() as config:
            for profile_name in sorted(config):
                profile = config[profile_name]
                url, creds = profile["url"], profile["credentials"]
                if creds is None:
                    rows.append([profile_name, url, "(anonymous)"])
                else:
                    rows.append([profile_name, url])

        table = self.make_table(rows)
        self.message(table.table)

    #
    # switch
    #

    def do_switch(self, text):
        """Switch to an alternate profile."""
        with utils.ProfileConfig.open() as config:
            if text in config:
                self.switch_profile(text)
            else:
                self.error("Unrecognised profile: %s" % text)

    def complete_switch(self, text, line, begidx, endidx):
        with utils.ProfileConfig.open() as config:
            return [
                with_trailing_space(profile_name) for profile_name in config
                if profile_name.startswith(text)
            ]

    def help_switch(self):
        self.message("Switch to an alternate profile. Choose from:")
        self.do_list(None)

    #
    # login
    #

    def do_login(self, text):
        """Log in to a remote API, and remember its details.

        If credentials are not provided on the command-line, they will be
        prompted for interactively.
        """
        parts = shlex.split(text, comments=True)
        if len(parts) == 2:
            name, url = parts
        elif len(parts) == 3:
            name, url, creds = parts
        else:
            self.error("Unrecognised arguments: " + text)
            return self.do_help("login")


def main(argv=None):
    shell = Shell()
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        raise SystemExit(1)
