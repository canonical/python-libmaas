"""Commands for running interactive and non-interactive shells."""

__all__ = [
    "register",
]

import code
import sys
import textwrap
import tokenize

from . import (
    colorized,
    Command,
    PROFILE_DEFAULT,
    PROFILE_NAMES,
)
from .. import (
    bones,
    facade,
    viscera,
)


class cmd_shell(Command):
    """Start a shell with some convenient local variables.

    If IPython is available it will be used, otherwise the familiar Python
    REPL will be started. If a script is piped in, it is read in its entirety
    then executed with the same namespace as the interactive shell.
    """

    profile_name_choices = PROFILE_NAMES
    profile_name_default = (
        None if PROFILE_DEFAULT is None else PROFILE_DEFAULT.name)

    def __init__(self, parser):
        super(cmd_shell, self).__init__(parser)
        if len(self.profile_name_choices) == 0:
            # There are no profiles, but we still offer the --profile-name
            # option so that users get a useful "profile not found" error
            # message instead of something more cryptic. Note that the help
            # string differs too.
            parser.add_argument(
                "--profile-name", metavar="NAME", required=False,
                default=None, help=(
                    "The name of the remote MAAS instance to use. "
                    "No profiles are currently defined; use the `profiles` "
                    "command to create one."
                ))
        else:
            parser.add_argument(
                "--profile-name", metavar="NAME", required=False,
                choices=self.profile_name_choices,
                default=self.profile_name_default, help=(
                    "The name of the remote MAAS instance to use." + (
                        "" if self.profile_name_default is None
                        else " [default: %(default)s]"
                    )
                ))
        parser.add_argument(
            "--viscera", action="store_true", default=False, help=(
                "Create a pre-canned viscera `Origin` for the selected "
                "profile. This is available as `origin` in the shell's "
                "namespace. You probably do not need this unless you're "
                "developing python-libmaas itself."
            ))
        parser.add_argument(
            "--bones", action="store_true", default=False, help=(
                "Create a pre-canned bones `Session` for the selected "
                "profile. This is available as `session` in the shell's "
                "namespace. You probably do not need this unless you're "
                "developing python-libmaas itself."
            ))
        parser.add_argument(
            "script", metavar="SCRIPT", nargs="?", default=None, help=(
                "Python script to run in the shell's namespace. An "
                "interactive shell is started if none is given."
            ))

    def __call__(self, options):
        """Execute this command."""

        # The namespace that code will run in.
        namespace = {}
        # Descriptions of the namespace variables.
        descriptions = {}

        # If a profile has been selected, set up a `bones` session and a
        # `viscera` origin in the default namespace.
        if options.profile_name is not None:
            session = bones.SessionAPI.fromProfileName(options.profile_name)
            if options.bones:
                namespace["session"] = session
                descriptions["session"] = (
                    "A pre-canned `bones` session for '%s'."
                    % options.profile_name)
            origin = viscera.Origin(session)
            if options.viscera:
                namespace["origin"] = origin
                descriptions["origin"] = (
                    "A pre-canned `viscera` origin for '%s'."
                    % options.profile_name)
            client = facade.Client(origin)
            namespace["client"] = client
            descriptions["client"] = (
                "A pre-canned client for '%s'."
                % options.profile_name)

        if options.script is None:
            if sys.stdin.isatty() and sys.stdout.isatty():
                self._run_interactive(namespace, descriptions)
            else:
                self._run_stdin(namespace)
        else:
            self._run_script(namespace, options.script)

    @staticmethod
    def _run_interactive(namespace, descriptions):
        # We at a fully interactive terminal — i.e. stdin AND stdout are
        # connected to the TTY — so display some introductory text...
        banner = ["{automagenta}Welcome to the MAAS shell.{/automagenta}"]
        if len(descriptions) > 0:
            banner += ["", "Predefined objects:", ""]
            wrap = textwrap.TextWrapper(60, "    ", "    ").wrap
            sortkey = lambda name: (name.casefold(), name)
            for name in sorted(descriptions, key=sortkey):
                banner.append("  {autoyellow}%s{/autoyellow}:" % name)
                banner.extend(wrap(descriptions[name]))
                banner.append("")
        for line in banner:
            print(colorized(line))
        # ... then start IPython, or the plain familiar Python REPL if
        # IPython is not installed.
        try:
            import IPython
        except ImportError:
            code.InteractiveConsole(namespace).interact(" ")
        else:
            IPython.start_ipython(
                argv=[], display_banner=False, user_ns=namespace)

    @staticmethod
    def _run_script(namespace, filename):
        namespace = dict(namespace, __file__=filename)
        with tokenize.open(filename) as fd:
            code = compile(fd.read(), filename, "exec")
        exec(code, namespace, namespace)

    @staticmethod
    def _run_stdin(namespace):
        namespace = dict(namespace, __file__="<stdin>")
        code = compile(sys.stdin.read(), "<stdin>", "exec")
        exec(code, namespace, namespace)


def register(parser):
    """Register profile commands with the given parser."""
    cmd_shell.register(parser)
