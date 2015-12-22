#!/usr/bin/env python3.5
# Copyright 2015 Alburnum Ltd. This software is licensed under
# the GNU Affero General Public License version 3 (see LICENSE).

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

str = None

__metaclass__ = type

import httplib
from pprint import pprint

from alburnum.maas.bones import (
    CallError,
    SessionAPI,
)


if __name__ == "__main__":
    # Load a MAAS CLI profile. The name below (here "madagascar") should be the
    # name of a profile created when using `maas login` at the command-line.
    papi = SessionAPI.fromProfileName("madagascar")

    # Create a tag if it doesn't exist.
    tag_name = "foo"
    try:
        tag = papi.Tag.read(name=tag_name)
    except CallError as error:
        if error.status == httplib.NOT_FOUND:
            tag = papi.Tags.new(
                name=tag_name, comment="%s's Stuff" % tag_name.capitalize())
        else:
            raise

    # List all the MAAS's tags.
    print(" Tags.list() ".center(50, "="))
    pprint(papi.Tags.list())

    # Associate the tag with all nodes.
    print(" Tag.update_nodes() ".center(50, "="))
    pprint(papi.Tag.update_nodes(
        name=tag["name"], add=[
            node["system_id"] for node in papi.Nodes.list()
        ]))
