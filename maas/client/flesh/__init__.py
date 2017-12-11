"""Commands for interacting with a remote MAAS."""

__all__ = [
    "colorized",
    "Command",
    "CommandError",
    "OriginCommand",
    "OriginTableCommand",
    "PROFILE_DEFAULT",
    "PROFILE_NAMES",
    "TableCommand",
]

from abc import (
    ABCMeta,
    abstractmethod,
)
import argparse
from importlib import import_module
import subprocess
import sys
import textwrap
import typing

import argcomplete
import colorclass

from . import tabular
from .. import (
    bones,
    utils,
    viscera,
)
from ..utils.auth import try_getpass
from ..utils.profiles import (
    Profile,
    ProfileStore,
)


PROG_DESCRIPTION = """\
MAAS provides complete automation of your physical servers for amazing data
center operational efficiency.

See https://maas.io/docs for documentation.

Common commands:

    maas login           Log-in to a MAAS.
    maas switch          Switch the active profile.
    maas machines        List machines.
    maas deploy          Allocate and deploy machine.
    maas release         Release machine.
    maas fabrics         List fabrics.
    maas subnets         List subnets.

Example help commands:

    `maas help`          This help page
    `maas help commands` Lists all commands
    `maas help deploy`   Shows help for command 'deploy'
"""


def colorized(text):
    if sys.stdout.isatty():
        # Don't return value_colors; returning the Color instance allows
        # terminaltables to correctly calculate alignment and padding.
        return colorclass.Color(text)
    else:
        return colorclass.Color(text).value_no_colors


def read_input(message, validator=None, password=False):
    message = "%s: " % message
    while True:
        if password:
            value = try_getpass(message)
        else:
            value = input(message)
        if value:
            if validator is not None:
                try:
                    validator(value)
                except Exception as exc:
                    print(
                        colorized("{{autored}}Error: {{/autored}} %s") %
                        str(exc))
                else:
                    return value
            else:
                return value


def yes_or_no(question):
    question = "%s [y/N] " % question
    while True:
        value = input(question)
        value = value.lower()
        if value in ['y', 'yes']:
            return True
        elif value in ['n', 'no']:
            return False


def print_with_pager(output):
    """Print the output to `stdout` using less when in a tty."""
    if sys.stdout.isatty():
        try:
            pager = subprocess.Popen(
                ['less', '-F', '-r', '-S', '-X', '-K'],
                stdin=subprocess.PIPE, stdout=sys.stdout)
        except subprocess.CalledProcessError:
            # Don't use the pager since starting it has failed.
            print(output)
            return
        else:
            pager.stdin.write(output.encode('utf-8'))
            pager.stdin.close()
            pager.wait()
    else:
        # Output directly to stdout since not in tty.
        print(output)


def get_profile_names_and_default() -> (
        typing.Tuple[typing.Sequence[str], typing.Optional[Profile]]):
    """Return the list of profile names and the default profile object.

    The list of names is sorted.
    """
    with ProfileStore.open() as config:
        return sorted(config), config.default


# Get profile names and the default profile now to avoid repetition when
# defining arguments (e.g. default and choices). Doing this as module-import
# time is imperfect but good enough for now.
PROFILE_NAMES, PROFILE_DEFAULT = get_profile_names_and_default()


class MinimalHelpAction(argparse._HelpAction):

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_minized_help()
        parser.exit()


class PagedHelpAction(argparse._HelpAction):

    def __call__(self, parser, namespace, values, option_string=None):
        print_with_pager(parser.format_help())
        parser.exit()


class HelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Specialization of argparse's raw description help formatter to modify
    usage to be in a better format.
    """

    def _format_usage(self, usage, actions, groups, prefix):
        if prefix is None:
            prefix = "Usage: "
        return super(HelpFormatter, self)._format_usage(
            usage, actions, groups, prefix)


class ArgumentParser(argparse.ArgumentParser):
    """Specialization of argparse's parser with better support for
    subparsers and better help output.

    Specifically, the one-shot `add_subparsers` call is disabled, replaced by
    a lazily evaluated `subparsers` property.

    `print_minized_help` is added to only show the description which is
    specially formatted.
    """

    def add_subparsers(self):
        raise NotImplementedError(
            "add_subparsers has been disabled")

    @property
    def subparsers(self):
        """Obtain the subparser's object."""
        try:
            return self.__subparsers
        except AttributeError:
            parent = super(ArgumentParser, self)
            self.__subparsers = parent.add_subparsers(title="drill down")
            self.__subparsers.metavar = "COMMAND"
            return self.__subparsers

    def add_argument_group(self, title, description=None):
        """Add an argument group, or return a pre-existing one."""
        try:
            groups = self.__groups
        except AttributeError:
            groups = self.__groups = {}

        if title not in groups:
            groups[title] = super().add_argument_group(
                title=title, description=description)

        return groups[title]

    @property
    def other(self):
        return self.add_argument_group("other arguments")

    def __getitem__(self, name):
        """Return the named subparser."""
        return self.subparsers.choices[name]

    def error(self, message):
        """Make the default error messages more helpful

        Override default ArgumentParser error method to print the help menu
        generated by ArgumentParser instead of just printing out a list of
        valid arguments.
        """
        self.exit(2, colorized("{autored}Error:{/autored} ") + message + "\n")

    def print_minized_help(self, *, no_pager=False):
        """Return the formatted help text.

        Override default ArgumentParser to just include the usage and the
        description. The `help` action is used for provide more detail.
        """
        formatter = self._get_formatter()
        formatter.add_usage(
            self.usage, self._actions,
            self._mutually_exclusive_groups)
        formatter.add_text(self.description)
        if no_pager:
            print(formatter.format_help())
        else:
            print_with_pager(formatter.format_help())


class CommandError(Exception):
    """A command has failed during execution."""


class Command(metaclass=ABCMeta):
    """A base class for composing commands.

    This adheres to the expectations of `register`.
    """

    def __init__(self, parser):
        super(Command, self).__init__()
        self.parser = parser

    @abstractmethod
    def __call__(self, options):
        """Execute this command."""

    @classmethod
    def name(cls):
        """Return the preferred name as which this command will be known."""
        name = cls.__name__.replace("_", "-").lower()
        name = name[4:] if name.startswith("cmd-") else name
        return name

    @classmethod
    def register(cls, parser, name=None):
        """Register this command as a sub-parser of `parser`.

        :type parser: An instance of `ArgumentParser`.
        :return: The sub-parser created.
        """
        help_title, help_body = utils.parse_docstring(cls)
        command_parser = parser.subparsers.add_parser(
            cls.name() if name is None else name, help=help_title,
            description=help_title, epilog=help_body, add_help=False,
            formatter_class=HelpFormatter)
        command_parser.add_argument(
            "-h", "--help", action=PagedHelpAction, help=argparse.SUPPRESS)
        command_parser.set_defaults(execute=cls(command_parser))
        return command_parser


class TableCommand(Command):

    def __init__(self, parser):
        super(TableCommand, self).__init__(parser)
        if sys.stdout.isatty():
            default_target = tabular.RenderTarget.pretty
        else:
            default_target = tabular.RenderTarget.plain
        parser.other.add_argument(
            "--format", type=tabular.RenderTarget,
            choices=tabular.RenderTarget, default=default_target, help=(
                "Output tabular data as a formatted table (pretty), a "
                "formatted table using only ASCII for borders (plain), or "
                "one of several dump formats. Default: %(default)s."
            ),
        )


class OriginCommandBase(Command):

    def __init__(self, parser):
        super(OriginCommandBase, self).__init__(parser)
        parser.other.add_argument(
            "--profile", dest="profile_name", metavar="NAME",
            choices=PROFILE_NAMES, required=(PROFILE_DEFAULT is None),
            help=(
                "The name of the remote MAAS instance to use. Use "
                "`profiles list` to obtain a list of valid profiles." +
                ("" if PROFILE_DEFAULT is None else
                 " [default: %s]" % PROFILE_DEFAULT.name)
            ))
        if PROFILE_DEFAULT is not None:
            parser.set_defaults(profile=PROFILE_DEFAULT.name)


class OriginCommand(OriginCommandBase):

    def __call__(self, options):
        session = bones.SessionAPI.fromProfileName(options.profile)
        origin = viscera.Origin(session)
        return self.execute(origin, options)

    def execute(self, origin, options):
        raise NotImplementedError(
            "Implement execute() in subclasses.")


class OriginTableCommand(OriginCommandBase, TableCommand):

    def __call__(self, options):
        session = bones.SessionAPI.fromProfileName(options.profile)
        origin = viscera.Origin(session)
        return self.execute(origin, options, target=options.format)

    def execute(self, origin, options, *, target):
        raise NotImplementedError(
            "Implement execute() in subclasses.")


class OriginPagedTableCommand(OriginTableCommand):

    def __init__(self, parser):
        super(OriginPagedTableCommand, self).__init__(parser)
        parser.other.add_argument(
            "--no-pager", action='store_true',
            help=(
                "Don't use the pager when printing the output of the "
                "command."))

    def __call__(self, options):
        return_code = 0
        output = super(OriginPagedTableCommand, self).__call__(options)
        if isinstance(output, tuple):
            return_code, output = output
        elif isinstance(output, int):
            return_code = output
            output = None
        elif isinstance(output, str):
            pass
        else:
            raise TypeError(
                "execute must return either tuple, int or str, not %s" % (
                    type(output).__name__))
        if output:
            if options.no_pager:
                print(output)
            else:
                print_with_pager(output)
        return return_code


class cmd_help(Command):
    """Show the help summary or help for a specific command."""

    def __init__(self, parser, parent_parser):
        self.parent_parser = parent_parser
        super(cmd_help, self).__init__(parser)
        parser.add_argument(
            "-h", "--help", action=PagedHelpAction, help=argparse.SUPPRESS)
        parser.add_argument(
            'command', nargs='?', help="Show help for this command.")
        parser.other.add_argument(
            "--no-pager", action='store_true',
            help=(
                "Don't use the pager when printing the output of the "
                "command."))

    def __call__(self, options):
        if options.command is None:
            self.parent_parser.print_minized_help(no_pager=options.no_pager)
        else:
            command = self.parent_parser.subparsers.choices.get(
                options.command, None)
            if command is None:
                if options.command == 'commands':
                    self.print_all_commands(no_pager=options.no_pager)
                else:
                    self.parser.error(
                        "unknown command %s" % options.command)
            else:
                if options.no_pager:
                    command.print_help()
                else:
                    print_with_pager(command.format_help())

    def print_all_commands(self, *, no_pager=False):
        """Print help for all commands.

        Commands are sorted in alphabetical order and wrapping is done
        based on the width of the terminal.
        """
        formatter = self.parent_parser._get_formatter()
        command_names = sorted(self.parent_parser.subparsers.choices.keys())
        max_name_len = max([len(name) for name in command_names]) + 1
        commands = ""
        for name in command_names:
            command = self.parent_parser.subparsers.choices[name]
            extra_padding = max_name_len - len(name)
            command_line = '%s%s%s' % (
                name, ' ' * extra_padding, command.description)
            while len(command_line) > formatter._width:
                lines = textwrap.wrap(command_line, formatter._width)
                commands += "%s\n" % lines[0]
                if len(lines) > 1:
                    lines[1] = (' ' * max_name_len) + lines[1]
                    command_line = ' '.join(lines[1:])
                else:
                    command_line = None
            if command_line:
                commands += "%s\n" % command_line
        if no_pager:
            print(commands[:-1])
        else:
            print_with_pager(commands[:-1])

    @classmethod
    def register(cls, parser, name=None):
        """Register this command as a sub-parser of `parser`.

        :type parser: An instance of `ArgumentParser`.
        :return: The sub-parser created.
        """
        help_title, help_body = utils.parse_docstring(cls)
        command_parser = parser.subparsers.add_parser(
            cls.name() if name is None else name, help=help_title,
            description=help_title, epilog=help_body, add_help=False,
            formatter_class=HelpFormatter)
        command_parser.set_defaults(execute=cls(command_parser, parser))
        return command_parser


def prepare_parser(program):
    """Create and populate an argument parser."""
    parser = ArgumentParser(
        description=PROG_DESCRIPTION, prog=program,
        formatter_class=HelpFormatter,
        add_help=False)
    parser.add_argument(
        "-h", "--help", action=MinimalHelpAction, help=argparse.SUPPRESS)

    # Register sub-commands.
    submodules = (
        "nodes", "machines", "devices", "controllers",
        "fabrics", "vlans", "subnets", "spaces",
        "files", "tags", "users",
        "profiles", "shell",
    )
    cmd_help.register(parser)
    for submodule in submodules:
        module = import_module("." + submodule, __name__)
        module.register(parser)

    # Register global options.
    parser.add_argument(
        '--debug', action='store_true', default=False,
        help=argparse.SUPPRESS)

    return parser


def post_mortem(traceback):
    """Work with an exception in a post-mortem debugger.

    Try to use `ipdb` first, falling back to `pdb`.
    """
    try:
        from ipdb import post_mortem
    except ImportError:
        from pdb import post_mortem

    message = "Entering post-mortem debugger. Type `help` for help."
    redline = colorized("{autored}%s{/autored}") % "{0:=^{1}}"

    print()
    print(redline.format(" CRASH! ", len(message)))
    print(message)
    print(redline.format("", len(message)))
    print()

    post_mortem(traceback)


def main(argv=sys.argv):
    program, *arguments = argv
    parser, options = None, None

    try:
        parser = prepare_parser(program)
        argcomplete.autocomplete(parser, exclude=("-h", "--help"))
        options = parser.parse_args(arguments)
        try:
            execute = options.execute
        except AttributeError:
            parser.error("Argument missing.")
        else:
            return execute(options)
    except KeyboardInterrupt:
        raise SystemExit(1)
    except Exception as error:
        # This is unexpected. Why? Because the CLI code raises SystemExit or
        # invokes something that raises SystemExit when it chooses to exit.
        # SystemExit does not subclass Exception, and so it would not be
        # handled here, hence this is not a deliberate exit.
        if parser is None or options is None or options.debug:
            # The user has either chosen to debug OR we crashed before/while
            # parsing arguments. Either way, let's not be terse.
            if sys.stdin.isatty() and sys.stdout.isatty():
                # We're at a fully interactive terminal so let's post-mortem.
                *_, exc_traceback = sys.exc_info()
                post_mortem(exc_traceback)
                # Exit non-zero, but quietly; dumping the traceback again on
                # the way out is confusing after doing a post-mortem.
                raise SystemExit(1)
            else:
                # Re-raise so the traceback is dumped and we exit non-zero.
                raise
        else:
            # Display a terse error message. Note that parser.error() will
            # raise SystemExit(>0) after printing its message.
            parser.error("%s" % error)
