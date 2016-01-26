#!/usr/bin/env python3.5

from argparse import ArgumentParser
from http import HTTPStatus
from pprint import pprint
import subprocess
import sys

from alburnum.maas import (
    bones,
    viscera,
)


parser = ArgumentParser()
parser.add_argument(
    "profile", nargs="?", default=None, help=(
        "Name of MAAS CLI profile to use. This should be the name of a "
        "profile created when using `maas login` at the command-line. "
        "(default: %(default)s)"
    ),
)


def title(message):
    print()
    print("*" * 78)
    print("*", message)
    print("*" * 78)


def heading(message):
    print()
    print((" " + message + " ").center(66, "-"))


if __name__ == "__main__":
    options = parser.parse_args()

    # #
    # #mmm    mmm   m mm    mmm    mmm
    # #" "#  #" "#  #"  #  #"  #  #   "
    # #   #  #   #  #   #  #""""   """m
    # ##m#"  "#m#"  #   #  "#mm"  "mmm"

    title("Working with `bones`, the low-level API.")

    # Load a MAAS CLI profile.
    if options.profile is None:
        result = subprocess.run(
            "/usr/bin/maas list | /usr/bin/awk '{ print $1 }'", shell=True,
            check=True, stdout=subprocess.PIPE)
        profiles = str(result.stdout, "utf-8").strip().split('\n')
        if len(profiles) == 0:
            sys.stderr.write(
                "No profiles found. Use the 'maas login' command to log in.\n")
        else:
            sys.stderr.write("Must specify one of the following profiles:\n")
            for profile in profiles:
                sys.stderr.write("    %s\n" % profile)
            sys.stderr.write("See 'maas list' for more information.\n")
        sys.exit(1)
    session = bones.SessionAPI.fromProfileName(options.profile)

    # Create a tag if it doesn't exist.
    tag_name = "foo"
    try:
        tag = session.Tag.read(name=tag_name)
    except bones.CallError as error:
        if error.status == HTTPStatus.NOT_FOUND:
            tag = session.Tags.new(
                name=tag_name, comment="%s's Stuff" % tag_name.capitalize())
        else:
            raise

    # List all the MAAS's tags.
    heading("Tags.list()")
    pprint(session.Tags.list())

    # Associate the tag with all nodes.
    heading("Tag.update_nodes()")
    pprint(session.Tag.update_nodes(
        name=tag["name"], add=[
            node["system_id"] for node in session.Nodes.list()
        ]))

    #          "
    # m   m  mmm     mmm    mmm    mmm    m mm   mmm
    # "m m"    #    #   "  #"  "  #"  #   #"  " "   #
    #  #m#     #     """m  #      #""""   #     m"""#
    #   #    mm#mm  "mmm"  "#mm"  "#mm"   #     "mm"#

    title("Working with `viscera`, the higher-level API.")

    origin = viscera.Origin(session)

    # List all the MAAS's tags.
    heading("list(origin.Tags), or origin.Tags.read()")
    pprint(list(origin.Tags))

    # List all the MAAS's nodes.
    heading("list(origin.Nodes), or origin.Nodes.read()")
    pprint(list(origin.Nodes))

    # Done.
    print()
