"""Commands for running interactive and non-interactive shells."""

__all__ = [
    "register",
]

import code
import sys

from . import (
    colorized,
    Command,
    PROFILE_DEFAULT,
    PROFILE_NAMES,
)
from .. import (
    bones,
    viscera,
)


class cmd_shell(Command):
    """Start a shell with some convenient local variables.

    If IPython is available it will be used, otherwise the familiar Python
    REPL will be started. If a script is piped in, it is read in its entirety
    then executed with the same namespace as the interactive shell.
    """

    def __init__(self, parser):
        super(cmd_shell, self).__init__(parser)
        parser.add_argument(
            "--profile-name", metavar="NAME", choices=PROFILE_NAMES,
            required=False, help=(
                "The name of the remote MAAS instance to use. Use "
                "`list-profiles` to obtain a list of valid profiles." +
                ("" if PROFILE_DEFAULT is None else " [default: %(default)s]")
            ))
        if PROFILE_DEFAULT is None:
            parser.set_defaults(profile_name=None)
        else:
            parser.set_defaults(profile_name=PROFILE_DEFAULT.name)

    def __call__(self, options):
        """Execute this command."""

        namespace = {}  # The namespace that code will run in.
        variables = {}  # Descriptions of the namespace variables.

        # If a profile has been selected, set up a `bones` session and a
        # `viscera` origin in the default namespace.
        if options.profile_name is not None:
            session = bones.SessionAPI.fromProfileName(options.profile_name)
            namespace["session"] = session
            variables["session"] = (
                "A `bones` session, configured for %s."
                % options.profile_name)
            origin = viscera.Origin(session)
            namespace["origin"] = origin
            variables["origin"] = (
                "A `viscera` origin, configured for %s."
                % options.profile_name)

        if sys.stdin.isatty() and sys.stdout.isatty():
            # We at a fully interactive terminal — i.e. stdin AND stdout are
            # connected to the TTY — so display some introductory text...
            banner = ["{automagenta}Welcome to the MAAS shell.{/automagenta}"]
            if len(variables) > 0:
                banner += ["", "Predefined variables:", ""]
                banner += [
                    "{autoyellow}%10s{/autoyellow}: %s" % variable
                    for variable in sorted(variables.items())
                ]
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
        else:
            # Either stdin or stdout is NOT connected to the TTY, so simply
            # slurp from stdin and exec in the already created namespace.
            source = sys.stdin.read()
            exec(source, namespace, namespace)


def register(parser):
    """Register profile commands with the given parser."""
    cmd_shell.register(parser)
