"""Helpers to assemble and render tabular data."""

__all__ = [
    "Column",
    "RenderTarget",
    "Table",
]

from abc import (
    ABCMeta,
    abstractmethod,
)
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


class Table(metaclass=ABCMeta):

    def __init__(self, *columns, visible_columns=None):
        super(Table, self).__init__()
        self.columns = collections.OrderedDict(
            (column.name, column) for column in columns)
        if visible_columns is None:
            self.visible_columns = collections.OrderedDict(
                self.columns.items())
        else:
            self.visible_columns = collections.OrderedDict(
                (column.name, column)
                for column in columns
                if column.name in visible_columns)

    def __getitem__(self, name):
        return self.columns[name]

    @abstractmethod
    def get_rows(self, target, data):
        """Get the rows for the table."""

    def _filter_rows(self, rows):
        """Filter `rows` based on the visible columns."""
        filtered_rows = []
        for row in rows:
            filtered_row = []
            for idx, name in enumerate(self.columns.keys()):
                if name in self.visible_columns:
                    filtered_row.append(row[idx])
            filtered_rows.append(filtered_row)
        return filtered_rows

    def render(self, target, data):
        """Render the table."""
        rows = self.get_rows(target, data)
        rows = self._filter_rows(rows)
        renderer = getattr(self, "_render_%s" % target.name, None)
        if renderer is None:
            raise ValueError(
                "Cannot render %r for %s." % (self.value, target))
        else:
            return renderer(rows)

    def _flatten_columns(self, columns):
        cols = []
        for _, column in columns.items():
            if isinstance(column, NestedTableColumn):
                cols.extend(self._flatten_columns(column.get_columns()))
            else:
                cols.append(column)
        return cols

    def _compute_rows(self, target, data, duplicate=False):
        columns = self.visible_columns.values()
        computed = []
        for row_data in data:
            row = []
            rows = [row]
            for datum, column in zip(row_data, columns):
                if isinstance(column, NestedTableColumn):
                    nested_rows = column.get_rows(
                        target, datum, duplicate=duplicate)
                    orig_row = list(row)
                    row.extend(nested_rows[0])
                    for nested_row in nested_rows[1:]:
                        new_row = list(orig_row)
                        if not duplicate:
                            for idx in range(len(new_row)):
                                new_row[idx] = ''
                        new_row.extend(nested_row)
                        rows.append(new_row)
                else:
                    row.append(column.render(target, datum))
            computed.extend(rows)
        return computed

    def _render_plain(self, data):
        rows = self._compute_rows(RenderTarget.plain, data)
        rows.insert(0, [column.title for column in self._flatten_columns(
            self.visible_columns)])
        return terminaltables.AsciiTable(rows).table

    def _render_pretty(self, data):
        rows = self._compute_rows(RenderTarget.pretty, data)
        rows.insert(0, [column.title for column in self._flatten_columns(
            self.visible_columns)])
        return terminaltables.SingleTable(rows).table

    def _render_yaml(self, data):
        columns = self.visible_columns.values()
        rows = [
            [column.render(RenderTarget.yaml, datum)
             for datum, column in zip(row, columns)]
            for row in data
        ]
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

    def _render_json(self, data):
        columns = self.visible_columns.values()
        rows = [
            [column.render(RenderTarget.json, datum)
             for datum, column in zip(row, columns)]
            for row in data
        ]
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

    def _render_csv(self, data):
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([column.name for column in self._flatten_columns(
            self.visible_columns)])
        writer.writerows(
            self._compute_rows(RenderTarget.csv, data, duplicate=True))
        return output.getvalue().rstrip(linesep)

    def __repr__(self):
        return "<%s [%s]>" % (
            self.__class__.__name__, " ".join(self.visible_columns))


class DetailTable(Table):

    def _filter_rows(self, rows, visible_columns=None):
        """Filter `rows` based on the visible columns."""
        if visible_columns is None:
            visible_columns = self.visible_columns
        filtered_row = []
        for idx, name in enumerate(self.columns.keys()):
            if name in self.visible_columns:
                filtered_row.append(rows[idx])
        return filtered_row

    def render(self, target, data):
        renderer = getattr(self, "_render_%s" % target.name, None)
        if renderer is None:
            raise ValueError(
                "Cannot render %r for %s." % (self.value, target))
        else:
            return renderer(data)

    def _split_nested_tables(self):
        table_columns = collections.OrderedDict(
            (name, column)
            for name, column in self.visible_columns.items()
            if isinstance(column, NestedTableColumn)
        )
        data_columns = collections.OrderedDict(
            (name, column)
            for name, column in self.visible_columns.items()
            if not isinstance(column, NestedTableColumn)
        )
        return data_columns, table_columns

    def _render_nested_table(self, target, data, column):
        data_idx = list(self.columns.keys()).index(column.name)
        data = data[data_idx]
        table = column.get_table()
        return table.render(target, data)

    def _render_nested_tables(self, target, data, columns):
        tables = [
            self._render_nested_table(target, data, column)
            for _, column in columns.items()
        ]
        if len(tables) > 0:
            return "\n" + "\n".join(tables)
        else:
            return ""

    def _render_table(self, target, terminaltable, data):
        columns, table_columns = self._split_nested_tables()
        all_rows = self.get_rows(target, data)
        rows = self._filter_rows(all_rows, visible_columns=columns)
        rows = [
            column.render(target, datum)
            for column, datum in zip(columns.values(), rows)
        ]
        table = terminaltable([
            (column.title, datum)
            for column, datum in zip(columns.values(), rows)
        ])
        table.inner_heading_row_border = False
        return table.table + self._render_nested_tables(
            target, all_rows, table_columns)

    def _render_plain(self, data):
        return self._render_table(
            RenderTarget.plain, terminaltables.AsciiTable, data)

    def _render_pretty(self, data):
        return self._render_table(
            RenderTarget.pretty, terminaltables.SingleTable, data)

    def _render_yaml(self, data):
        columns = self.visible_columns.values()
        rows = self.get_rows(RenderTarget.yaml, data)
        rows = self._filter_rows(rows)
        rows = [
            column.render(RenderTarget.yaml, datum)
            for column, datum in zip(columns, rows)
        ]
        return yaml.safe_dump({
            column.name: datum
            for column, datum in zip(columns, rows)
        }, default_flow_style=False).rstrip(linesep)

    def _render_json(self, data):
        columns = self.visible_columns.values()
        rows = self.get_rows(RenderTarget.json, data)
        rows = self._filter_rows(rows)
        rows = [
            column.render(RenderTarget.json, datum)
            for column, datum in zip(columns, rows)
        ]
        return json.dumps({
            column.name: datum
            for column, datum in zip(columns, rows)
        })

    def _render_csv(self, data):
        columns, table_columns = self._split_nested_tables()
        all_rows = self.get_rows(RenderTarget.csv, data)
        rows = self._filter_rows(all_rows, visible_columns=columns)
        rows = [
            column.render(RenderTarget.csv, datum)
            for column, datum in zip(columns.values(), rows)
        ]
        output = StringIO()
        writer = csv.writer(output)
        writer.writerows([
            (column.name, datum)
            for column, datum in zip(columns.values(), rows)
        ])
        return output.getvalue().rstrip(linesep) + (
            self._render_nested_tables(
                RenderTarget.csv, all_rows, table_columns))


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
            if (isinstance(datum, collections.Iterable) and
                    not isinstance(datum, (str, bytes))):
                return ",".join(datum)
            else:
                return datum
        elif target is RenderTarget.plain:
            if datum is None:
                return ""
            elif isinstance(datum, colorclass.Color):
                return datum.value_no_colors
            elif (isinstance(datum, collections.Iterable) and
                    not isinstance(datum, (str, bytes))):
                return "\n".join(datum)
            else:
                return str(datum)
        elif target is RenderTarget.pretty:
            if datum is None:
                return ""
            elif isinstance(datum, colorclass.Color):
                return datum
            elif (isinstance(datum, collections.Iterable) and
                    not isinstance(datum, (str, bytes))):
                return "\n".join(datum)
            else:
                return str(datum)
        else:
            raise ValueError(
                "Cannot render %r for %s" % (datum, target))

    def __repr__(self):
        return "<%s name=%s title=%r>" % (
            self.__class__.__name__, self.name, self.title)


class NestedTableColumn(Column):

    def __init__(
            self, name, title=None,
            table=None, table_args=None, table_kwargs=None):
        super(NestedTableColumn, self).__init__(name, title=title)
        self.table = table
        self.table_args = table_args
        self.table_kwargs = table_kwargs
        if table is None:
            raise ValueError("table is required.")

    def get_table(self):
        table_args = self.table_args
        if table_args is None:
            table_args = []
        table_kwargs = self.table_kwargs
        if table_kwargs is None:
            table_kwargs = {}
        return self.table(*table_args, **table_kwargs)

    def get_columns(self):
        return self.get_table().visible_columns

    def get_rows(self, target, data, duplicate=False):
        table = self.get_table()
        rows = table.get_rows(target, data)
        rows = table._filter_rows(rows)
        rows = table._compute_rows(
            target, rows, duplicate=duplicate)
        if len(rows) == 0:
            # Nested table column must always return one row even if its
            # an empty row.
            rows = [[
                ' '
                for _ in range(len(table.visible_columns))
            ]]
        return rows

    def render(self, target, datum):
        table = self.get_table()
        if target is RenderTarget.yaml:
            return yaml.safe_load(table.render(target, datum))
        elif target is RenderTarget.json:
            return json.loads(table.render(target, datum))
        else:
            raise ValueError(
                "Should not be called on a nested table column, the "
                "table render should handle this correctly.")
