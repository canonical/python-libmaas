"""Commands for working with local profiles."""

__all__ = [
    "register",
]

import sys

from . import (
    colorized,
    Command,
    print_with_pager,
    PROFILE_DEFAULT,
    PROFILE_NAMES,
    read_input,
    TableCommand,
    tables,
)
from .. import (
    bones,
    utils,
)
from ..bones import helpers
from ..utils import (
    auth,
    profiles,
)
from ..utils.maas_async import asynchronous


class cmd_login(Command):
    """Log-in to a MAAS with either username and password or apikey.

    The username and password will NOT be saved; a new API key will be
    obtained from MAAS and associated with the new profile. This key can be
    selectively revoked from the Web UI, for example, at a later date.
    """

    def __init__(self, parser):
        super(cmd_login, self).__init__(parser)
        parser.add_argument(
            "-p", "--profile-name", default=None, help=(
                "The name to give the profile. Default is the username used "
                "to login."))
        parser.add_argument(
            '--anonymous', default=False, action='store_true', help=(
                "Create an anonymous profile, no credentials are associated "
                "to it."))
        parser.add_argument(
            '--apikey', default=None, help=(
                "The API key acquired from MAAS. This requires the profile "
                "name to be provided as well."))
        parser.add_argument(
            '-k', '--insecure', action='store_true', help=(
                "Disable SSL certificate check"), default=False)
        parser.add_argument(
            "url", nargs="?", type=utils.api_url, help=(
                "The URL of the API, e.g. http://example.com/MAAS/ "
                "or http://example.com/MAAS/api/2.0/ if you wish to specify "
                "the API version. If no URL is provided then it will be "
                "prompted for, interactively."))
        parser.add_argument(
            "username", nargs="?", default=None, help=(
                "The username used to login to MAAS. If no username is "
                "provided and API key is not being used it will be prompted "
                "for, interactively."))
        parser.add_argument(
            "password", nargs="?", default=None, help=(
                "The password used to login to MAAS. If no password is "
                "proviced and API key is not being used it will be promoed "
                "for, interactively."))

    @asynchronous
    async def __call__(self, options):
        has_auth_info = any(
            (options.apikey, options.username, options.password))
        if options.anonymous and has_auth_info:
            raise ValueError(
                "Can't specify username, password or--apikey with --anonymous")

        if options.apikey and not options.profile_name:
            raise ValueError(
                "-p,--profile-name must be provided with --apikey")

        if not options.url:
            url = read_input("URL", validator=utils.api_url)
        else:
            url = options.url

        if not options.apikey:
            if options.anonymous:
                password = None
            elif options.username and not options.password:
                password = read_input("Password", password=True)
            else:
                password = options.password
                if password == '-':
                    password = sys.stdin.readline().strip()
            try:
                profile = await helpers.login(
                    url, anonymous=options.anonymous,
                    username=options.username,
                    password=password, insecure=options.insecure)
            except helpers.MacaroonLoginNotSupported:
                # the server doesn't have external authentication enabled,
                # propmt for username/password
                username = read_input("Username")
                password = read_input("Password", password=True)
                profile = await helpers.login(
                    url, username=username, password=password,
                    insecure=options.insecure)
        else:
            credentials = auth.obtain_credentials(options.apikey)
            session = await bones.SessionAPI.fromURL(
                url, credentials=credentials, insecure=options.insecure)
            profile = profiles.Profile(
                options.profile_name, url, credentials=credentials,
                description=session.description)

        if options.profile_name:
            profile = profile.replace(name=options.profile_name)

        # Save a new profile.
        with profiles.ProfileStore.open() as config:
            config.save(profile)
            config.default = profile

        self.print_whats_next(profile)

    @staticmethod
    def print_whats_next(profile):
        """Explain what to do next."""
        what_next = [
            "{{autogreen}}Congratulations!{{/autogreen}} You are logged in "
            "to the MAAS server at {{autoblue}}{profile.url}{{/autoblue}} "
            "with the profile name {{autoblue}}{profile.name}{{/autoblue}}.",
            "For help with the available commands, try:",
            "  maas help",
            ]
        for message in what_next:
            message = message.format(profile=profile)
            print(colorized(message))
            print()


class cmd_logout(Command):
    """Logout of a MAAS profile, purging any stored credentials.

    This will remove the given profile from your command-line client. You can
    re-create it later using `add` or `login`.
    """

    def __init__(self, parser):
        super(cmd_logout, self).__init__(parser)
        parser.add_argument(
            "profile_name", metavar="profile-name",
            nargs="?", choices=PROFILE_NAMES, help=(
                "The profile name you want to logout of." +
                ("" if PROFILE_DEFAULT is None else " [default: %(default)s]")
            ),
        )
        if PROFILE_DEFAULT is not None:
            parser.set_defaults(profile_name=PROFILE_DEFAULT.name)

    def __call__(self, options):
        with profiles.ProfileStore.open() as config:
            config.delete(options.profile_name)


class cmd_switch(Command):
    """Switch the active profile.

    This will switch the currently active profile to the given profile. The
    previous profile will remain, just use `switch` again to go back.
    """

    def __init__(self, parser):
        super(cmd_switch, self).__init__(parser)
        parser.add_argument(
            "profile_name", metavar="profile-name", choices=PROFILE_NAMES,
            help=(
                "The profile name you want to switch to."
            ),
        )

    def __call__(self, options):
        with profiles.ProfileStore.open() as config:
            profile = config.load(options.profile_name)
            config.default = profile


class cmd_profiles(TableCommand):
    """List profiles (aka. logged in MAAS's)."""

    def __init__(self, parser):
        super(cmd_profiles, self).__init__(parser)
        parser.add_argument(
            "--refresh", action='store_true', default=False, help=(
                "Retrieves the latest version of the help information for "
                "all profiles. Use it to update your command-line client's "
                "information after an upgrade to the MAAS server."),
        )
        parser.other.add_argument(
            "--no-pager", action='store_true',
            help=(
                "Don't use the pager when printing the output of the "
                "command."))

    def __call__(self, options):
        if options.refresh:
            with profiles.ProfileStore.open() as config:
                for profile_name in config:
                    profile = config.load(profile_name)
                    session = bones.SessionAPI.fromProfile(profile)
                    profile = profile.replace(description=session.description)
                    config.save(profile)
        else:
            table = tables.ProfilesTable()
            with profiles.ProfileStore.open() as config:
                if options.no_pager:
                    print(table.render(options.format, config))
                else:
                    print_with_pager(table.render(options.format, config))


def register(parser):
    """Register profile commands with the given parser."""
    cmd_login.register(parser)
    cmd_logout.register(parser)
    cmd_switch.register(parser)
    cmd_profiles.register(parser)
