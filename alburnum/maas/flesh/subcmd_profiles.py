"""Commands for working with local profiles."""

__all__ = [
    "register_as",
]

from textwrap import fill
from urllib.parse import urlparse

from . import (
    colorized,
    Command,
    CommandError,
    PROFILE_DEFAULT,
    PROFILE_NAMES,
    TableCommand,
    tables,
)
from .. import (
    bones,
    utils,
)
from ..utils import (
    creds,
    profiles,
)
from ..utils.auth import (
    obtain_credentials,
    obtain_password,
    obtain_token,
)


def check_valid_apikey(_1, _2, _3):  # TODO
    return True


class cmd_login_base(Command):

    def __init__(self, parser):
        super(cmd_login_base, self).__init__(parser)
        parser.add_argument(
            "profile_name", metavar="profile-name", help=(
                "The name with which you will later refer to this remote "
                "server and credentials within this tool."
                ))
        parser.add_argument(
            "url", type=utils.api_url, help=(
                "The URL of the remote API, e.g. http://example.com/MAAS/ "
                "or http://example.com/MAAS/api/1.0/ if you wish to specify "
                "the API version."))
        parser.add_argument(
            '-k', '--insecure', action='store_true', help=(
                "Disable SSL certificate check"), default=False)

    @staticmethod
    def save_profile(options, credentials: creds.Credentials):
        # Check for bogus credentials. Do this early so that the user is not
        # surprised when next invoking the MAAS CLI.
        if credentials is not None:
            try:
                valid_apikey = check_valid_apikey(
                    options.url, credentials, options.insecure)
            except bones.CallError as e:
                raise SystemExit("%s" % e)
            else:
                if not valid_apikey:
                    raise SystemExit("The MAAS server rejected your API key.")

        # Establish a session with the remote API.
        session = bones.SessionAPI.fromURL(
            options.url, credentials=credentials, insecure=options.insecure)

        # Make a new profile and save it as the default.
        profile = profiles.Profile(
            options.profile_name, options.url, credentials=credentials,
            description=session.description)
        with profiles.ProfileManager.open() as config:
            config.save(profile)
            config.default = profile.name

        return profile

    @staticmethod
    def print_whats_next(profile):
        """Explain what to do next."""
        what_next = [
            "{{autogreen}}Congratulations!{{/autogreen}} You are logged in "
            "to the MAAS server at {{autoblue}}{profile.url}{{/autoblue}} "
            "with the profile name {{autoblue}}{profile.name}{{/autoblue}}.",
            "For help with the available commands, try:",
            "  maas --help",
            ]
        for message in what_next:
            message = message.format(profile=profile)
            print(colorized(fill(message)))
            print()


class cmd_login(cmd_login_base):
    """Log-in to a remote MAAS with username and password.

    The username and password will NOT be saved; a new API key will be
    obtained from MAAS and associated with the new profile. This key can be
    selectively revoked from the Web UI, for example, at a later date.
    """

    def __init__(self, parser):
        super(cmd_login, self).__init__(parser)
        parser.add_argument(
            "username", nargs="?", default=None, help=(
                "The username used to login to MAAS. Omit this and the "
                "password for anonymous API access."))
        parser.add_argument(
            "password", nargs="?", default=None, help=(
                "The password used to login to MAAS. Omit both the username "
                "and the password for anonymous API access, or pass a single "
                "hyphen to allow the password to be provided via standard-"
                "input. If a username is provided but no password, the "
                "password will be prompted for, interactively."
            ),
        )

    def __call__(self, options):
        url = urlparse(options.url)

        if options.username is None:
            username = url.username
        else:
            if url.username is None or len(url.username) == 0:
                username = options.username
            else:
                raise CommandError(
                    "Username provided on command-line (%r) and in URL (%r); "
                    "provide only one." % (options.username, url.username))

        if options.password is None:
            password = url.password
        else:
            if url.password is None or len(url.password) == 0:
                password = options.password
            else:
                raise CommandError(
                    "Password provided on command-line (%r) and in URL (%r); "
                    "provide only one." % (options.password, url.password))

        if username is None:
            if password is None or len(password) == 0:
                credentials = None  # Anonymous.
            else:
                raise CommandError(
                    "Password provided without username; specify username.")
        else:
            password = obtain_password(password)
            if password is None:
                raise CommandError("No password supplied.")
            else:
                credentials = obtain_token(
                    options.url, username, password)

        # Save a new profile, and print something useful.
        profile = self.save_profile(options, credentials)
        self.print_whats_next(profile)


class cmd_add(cmd_login_base):
    """Add a profile for a remote MAAS using an *API key*.

    The `login` command will typically be more convenient.
    """

    def __init__(self, parser):
        super(cmd_add, self).__init__(parser)
        parser.add_argument(
            "credentials", nargs="?", default=None, help=(
                "The credentials, also known as the API key, for the remote "
                "MAAS server. These can be found in the user preferences page "
                "in the Web UI; they take the form of a long random-looking "
                "string composed of three parts, separated by colons. Specify "
                "an empty string for anonymous API access, or pass a single "
                "hyphen to allow the credentials to be provided via standard-"
                "input. If no credentials are provided, they will be prompted "
                "for, interactively."
            ),
        )

    def __call__(self, options):
        # Try and obtain credentials interactively if they're not given, or
        # read them from stdin if they're specified as "-".
        credentials = obtain_credentials(options.credentials)
        # Save a new profile, and print something useful.
        profile = self.save_profile(options, credentials)
        self.print_whats_next(profile)


class cmd_remove(Command):
    """Remove a profile, purging any stored credentials.

    This will remove the given profile from your command-line client. You can
    re-create it later using `add` or `login`.
    """

    def __init__(self, parser):
        super(cmd_remove, self).__init__(parser)
        parser.add_argument(
            "profile_name", metavar="profile-name", nargs="?",
            choices=PROFILE_NAMES, help=(
                "The name with which a remote server and its "
                "credentials are referred to within this tool." +
                ("" if PROFILE_DEFAULT is None else " [default: %(default)s]")
            ),
        )
        if PROFILE_DEFAULT is not None:
            parser.set_defaults(profile_name=PROFILE_DEFAULT.name)

    def __call__(self, options):
        with profiles.ProfileManager.open() as config:
            config.delete(options.profile_name)


class cmd_switch(Command):
    """Switch the default profile."""

    def __init__(self, parser):
        super(cmd_switch, self).__init__(parser)
        parser.add_argument(
            "profile_name", metavar="profile-name", choices=PROFILE_NAMES,
            help=(
                "The name with which a remote server and its credentials "
                "are referred to within this tool."
            ),
        )

    def __call__(self, options):
        with profiles.ProfileManager.open() as config:
            profile = config.load(options.profile_name)
            config.default = profile


class cmd_list(TableCommand):
    """List remote APIs that have been logged-in to."""

    def __call__(self, options):
        table = tables.ProfilesTable()
        with profiles.ProfileManager.open() as config:
            print(table.render(options.output_format, config))


class cmd_refresh(Command):
    """Refresh the API descriptions of all profiles.

    This retrieves the latest version of the help information for each
    profile.  Use it to update your command-line client's information after
    an upgrade to the MAAS server.
    """

    def __call__(self, options):
        with profiles.ProfileManager.open() as config:
            for profile_name in config:
                profile = config.load(profile_name)
                session = bones.SessionAPI.fromProfile(profile)
                profile = profile.replace(description=session.description)
                config.save(profile)


def register_as(name, parser):
    """Register profile commands with the given parser."""
    parser = parser.subparsers.add_parser(
        name, help="Manage profiles, e.g. adding, removing, logging-in.",
        description=(
            "A profile is a convenient way to refer to a remote MAAS "
            "installation. It encompasses the URL, the credentials, and "
            "the retrieved API description. Each profile has a unique name "
            "which can be provided to commands that work with remote MAAS "
            "installations, or a default profile can be chosen."
        ),
        epilog=colorized(
            "If in doubt, try {autogreen}login{/autogreen}."
        ),
    )

    cmd_add.register(parser)
    cmd_remove.register(parser)
    cmd_login.register(parser)
    cmd_list.register(parser)
    cmd_switch.register(parser)
    cmd_refresh.register(parser)
