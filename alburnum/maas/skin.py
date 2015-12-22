# Copyright 2015 Alburnum Ltd. This software is licensed under
# the GNU Affero General Public License version 3 (see LICENSE).

"""Shell for interacting with a remote MAAS (https://maas.ubuntu.com/)."""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
)

str = None

__metaclass__ = type
__all__ = [
    "Shell",
]

import cmd
import re
import shlex
from textwrap import dedent

from alburnum.maas.utils import ProfileConfig
import colorclass
import terminaltables


class Shell(cmd.Cmd):

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
        return [
            name[3:] + " " for name in self.get_names()
            if name.startswith(dotext)
        ]

    #
    # list
    #

    def do_list(self, line):
        """List all profiles."""
        rows = [["Profile name", "URL"]]

        with ProfileConfig.open() as config:
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
        with ProfileConfig.open() as config:
            if text in config:
                self.switch_profile(text)
            else:
                self.error("Unrecognised profile: %s" % text)

    def complete_switch(self, text, line, begidx, endidx):
        with ProfileConfig.open() as config:
            return [
                profile_name for profile_name in config
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


# TODO: Do this via a metaclass or class-decorator.
for name, func in vars(Shell).items():
    if name.startswith("do_") and callable(func):
        doc = func.__doc__
        if doc is not None:
            parts = re.split(r'(?:\r\n|\r|\n)+', doc, maxsplit=1)
            if len(parts) == 2:
                doc = parts[0] + "\n\n" + dedent(parts[1])
            else:
                doc = parts[0]
            func.__doc__ = doc.strip() + "\n"


def main(argv=None):
    shell = Shell()
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        raise SystemExit(1)
