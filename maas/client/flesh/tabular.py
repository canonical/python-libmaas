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
from os import linesep

import colorclass
import terminaltables
import yaml


class RenderTarget(enum.Enum):

    # Human-readable tabluar output.
    plain = "plain"
    pretty = "pretty"

    # Machine-readable output.
    yaml = "yaml"
    json = "json"
    csv = "csv"

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
        renderer = getattr(self, "_render_%s" % target.name, None)
        if renderer is None:
            raise ValueError(
                "Cannot render %r for %s." % (self.value, target))
        else:
            return renderer(columns, rows)

    def _render_plain(self, columns, rows):
        rows.insert(0, [column.title for column in columns])
        return terminaltables.AsciiTable(rows).table

    def _render_pretty(self, columns, rows):
        rows.insert(0, [column.title for column in columns])
        return terminaltables.SingleTable(rows).table

    def _render_yaml(self, columns, rows):
        return yaml.safe_dump({
            "columns": [
                {"name": column.name, "title": column.title}
                for column in columns
            ],
            "data": [
                {column.name: datum
                 for column, datum in zip(columns, row)}
                for row in rows
            ],
        }, default_flow_style=False).rstrip(linesep)

    def _render_json(self, columns, rows):
        return json.dumps({
            "columns": [
                {"name": column.name, "title": column.title}
                for column in columns
            ],
            "data": [
                {column.name: datum
                 for column, datum in zip(columns, row)}
                for row in rows
            ],
        })

    def _render_csv(self, columns, rows):
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([column.name for column in columns])
        writer.writerows(rows)
        return output.getvalue().rstrip(linesep)

    def __repr__(self):
        return "<%s [%s]>" % (
            self.__class__.__name__, " ".join(self.columns))


class Column:

    def __init__(self, name, title=None):
        super(Column, self).__init__()
        self.name = name
        self.title = name if title is None else title

    def render(self, target, datum):
        if target is RenderTarget.yaml:
            return datum
        elif target is RenderTarget.json:
            return datum
        elif target is RenderTarget.csv:
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
