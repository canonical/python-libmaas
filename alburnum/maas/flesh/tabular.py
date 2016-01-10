# Copyright 2015 Alburnum Ltd. This software is licensed under
# the GNU Affero General Public License version 3 (see LICENSE).

"""Helpers to assemble and render tabular data."""

__all__ = [
    "Column",
    "RenderTarget",
    "Table",
]

import collections
import csv
import enum
from io import StringIO
import json

import colorclass
import terminaltables
import yaml


class RenderTarget(enum.Enum):

    plain = "plain"
    pretty = "pretty"
    dump_yaml = "yaml"
    dump_json = "json"
    dump_csv = "csv"

    def __str__(self):
        # Return the value. This makes it better to use as a choices option to
        # argparse at the command-line.
        return self.value


class Table:

    def __init__(self, *columns):
        super(Table, self).__init__()
        self.columns = collections.OrderedDict(
            (column.name, column) for column in columns)

    def __getitem__(self, name):
        return self.columns[name]

    def render(self, target, data):
        columns = self.columns.values()
        rows = [
            [column.render(target, datum)
             for datum, column in zip(row, columns)]
            for row in data
        ]
        if target in (RenderTarget.dump_yaml, RenderTarget.dump_json):
            data = {
                "columns": [
                    {"name": column.name, "title": column.title}
                    for column in columns
                ],
                "data": [
                    {column.name: datum
                     for column, datum in zip(columns, row)}
                    for row in rows
                ],
            }
            if target is RenderTarget.dump_yaml:
                return yaml.safe_dump(data, default_flow_style=False)
            elif target is RenderTarget.dump_json:
                return json.dumps(data)
            else:
                raise AssertionError(target)
        elif target is RenderTarget.plain:
            rows.insert(0, [column.title for column in columns])
            return terminaltables.AsciiTable(rows).table
        elif target is RenderTarget.pretty:
            rows.insert(0, [column.title for column in columns])
            return terminaltables.SingleTable(rows).table
        elif target is RenderTarget.dump_csv:
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow([column.name for column in columns])
            writer.writerows(rows)
            return output.getvalue()
        else:
            raise ValueError(
                "Cannot render %r for %s" % (self.value, target))

    def __repr__(self):
        return "<%s [%s]>" % (
            self.__class__.__name__, " ".join(self.columns))


class Column:

    def __init__(self, name, title=None):
        super(Column, self).__init__()
        self.name = name
        self.title = name if title is None else title

    def render(self, target, datum):
        if target is RenderTarget.dump_yaml:
            return datum
        elif target is RenderTarget.dump_json:
            return datum
        elif target is RenderTarget.dump_csv:
            return datum
        elif target is RenderTarget.plain:
            if datum is None:
                return ""
            elif isinstance(datum, colorclass.Color):
                return datum.value_no_colors
            else:
                return str(datum)
        elif target is RenderTarget.pretty:
            if datum is None:
                return ""
            elif isinstance(datum, colorclass.Color):
                return datum
            else:
                return str(datum)
        else:
            raise ValueError(
                "Cannot render %r for %s" % (datum, target))

    def __repr__(self):
        return "<%s name=%s title=%r>" % (
            self.__class__.__name__, self.name, self.title)
