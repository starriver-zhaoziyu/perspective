################################################################################
#
# Copyright (c) 2019, the Perspective Authors.
#
# This file is part of the Perspective library, distributed under the terms of
# the Apache License 2.0.  The full license can be found in the LICENSE file.
#

import random
import pandas as pd
import numpy as np
from perspective import PerspectiveCppError
from perspective.table import Table
from datetime import date, datetime
from pytest import mark, raises


def compare_delta(received, expected):
    """Compare an arrow-serialized row delta by constructing a Table."""
    tbl = Table(received)
    assert tbl.view().to_dict() == expected


class TestView(object):
    def test_view_zero(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view()
        assert view.num_rows() == 2
        assert view.num_columns() == 2
        assert view.schema() == {
            "a": int,
            "b": int
        }
        assert view.to_records() == data

    def test_view_one(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view(row_pivots=["a"])
        assert view.num_rows() == 3
        assert view.num_columns() == 2
        assert view.schema() == {
            "a": int,
            "b": int
        }
        assert view.to_records() == [
            {"__ROW_PATH__": [], "a": 4, "b": 6},
            {"__ROW_PATH__": [1], "a": 1, "b": 2},
            {"__ROW_PATH__": [3], "a": 3, "b": 4}
        ]

    def test_view_two(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view(row_pivots=["a"], column_pivots=["b"])
        assert view.num_rows() == 3
        assert view.num_columns() == 4
        assert view.schema() == {
            "a": int,
            "b": int
        }
        assert view.to_records() == [
            {"2|a": 1, "2|b": 2, "4|a": 3, "4|b": 4, "__ROW_PATH__": []},
            {"2|a": 1, "2|b": 2, "4|a": None, "4|b": None, "__ROW_PATH__": [1]},
            {"2|a": None, "2|b": None, "4|a": 3, "4|b": 4, "__ROW_PATH__": [3]}
        ]

    def test_view_two_column_only(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view(column_pivots=["b"])
        assert view.num_rows() == 2
        assert view.num_columns() == 4
        assert view.schema() == {
            "a": int,
            "b": int
        }
        assert view.to_records() == [
            {"2|a": 1, "2|b": 2, "4|a": None, "4|b": None},
            {"2|a": None, "2|b": None, "4|a": 3, "4|b": 4}
        ]

    # column path

    def test_view_column_path_zero(self):
        data = {
            "a": [1, 2, 3],
            "b": [1.5, 2.5, 3.5]
        }
        tbl = Table(data)
        view = tbl.view()
        paths = view.column_paths()
        assert paths == ["a", "b"]

    def test_view_column_path_zero_schema(self):
        data = {
            "a": int,
            "b": float
        }
        tbl = Table(data)
        view = tbl.view()
        paths = view.column_paths()
        assert paths == ["a", "b"]

    def test_view_column_path_zero_hidden(self):
        data = {
            "a": [1, 2, 3],
            "b": [1.5, 2.5, 3.5]
        }
        tbl = Table(data)
        view = tbl.view(columns=["b"])
        paths = view.column_paths()
        assert paths == ["b"]

    def test_view_column_path_zero_respects_order(self):
        data = {
            "a": [1, 2, 3],
            "b": [1.5, 2.5, 3.5]
        }
        tbl = Table(data)
        view = tbl.view(columns=["b", "a"])
        paths = view.column_paths()
        assert paths == ["b", "a"]

    def test_view_column_path_one(self):
        data = {
            "a": [1, 2, 3],
            "b": [1.5, 2.5, 3.5]
        }
        tbl = Table(data)
        view = tbl.view(row_pivots=["a"])
        paths = view.column_paths()
        assert paths == ["__ROW_PATH__", "a", "b"]

    def test_view_column_path_two(self):
        data = {
            "a": [1, 2, 3],
            "b": [1.5, 2.5, 3.5]
        }
        tbl = Table(data)
        view = tbl.view(row_pivots=["a"], column_pivots=["b"])
        paths = view.column_paths()
        assert paths == ["__ROW_PATH__", "1.5|a", "1.5|b", "2.5|a", "2.5|b", "3.5|a", "3.5|b"]

    def test_view_column_path_two_column_only(self):
        data = {
            "a": [1, 2, 3],
            "b": [1.5, 2.5, 3.5]
        }
        tbl = Table(data)
        view = tbl.view(column_pivots=["b"])
        paths = view.column_paths()
        assert paths == ["1.5|a", "1.5|b", "2.5|a", "2.5|b", "3.5|a", "3.5|b"]

    def test_view_column_path_hidden_sort(self):
        data = {
            "a": [1, 2, 3],
            "b": [1.5, 2.5, 3.5],
            "c": [3, 2, 1]
        }
        tbl = Table(data)
        view = tbl.view(columns=["a", "b"], sort=[["c", "desc"]])
        paths = view.column_paths()
        assert paths == ["a", "b"]

    def test_view_column_path_hidden_col_sort(self):
        data = {
            "a": [1, 2, 3],
            "b": [1.5, 2.5, 3.5],
            "c": [3, 2, 1]
        }
        tbl = Table(data)
        view = tbl.view(column_pivots=["a"], columns=["a", "b"], sort=[["c", "col desc"]])
        paths = view.column_paths()
        assert paths == ["1|a", "1|b", "2|a", "2|b", "3|a", "3|b"]

    def test_view_column_path_pivot_by_bool(self):
        data = {
            "a": [1, 2, 3],
            "b": [True, False, True],
            "c": [3, 2, 1]
        }
        tbl = Table(data)
        view = tbl.view(column_pivots=["b"], columns=["a", "b", "c"])
        paths = view.column_paths()
        assert paths == ["false|a", "false|b", "false|c", "true|a", "true|b", "true|c"]

    # schema correctness

    def test_string_view_schema(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view()
        assert view.schema(as_string=True) == {
            "a": "integer",
            "b": "integer"
        }

    def test_zero_view_schema(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view()
        assert view.schema() == {
            "a": int,
            "b": int
        }

    def test_one_view_schema(self):
        data = [{"a": "abc", "b": 2}, {"a": "abc", "b": 4}]
        tbl = Table(data)
        view = tbl.view(row_pivots=["a"], aggregates={"a": "distinct count"})
        assert view.schema() == {
            "a": int,
            "b": int
        }

    def test_two_view_schema(self):
        data = [{"a": "abc", "b": "def"}, {"a": "abc", "b": "def"}]
        tbl = Table(data)
        view = tbl.view(
            row_pivots=["a"],
            column_pivots=["b"],
            aggregates={
                "a": "count",
                "b": "count"
            })
        assert view.schema() == {
            "a": int,
            "b": int
        }

    # aggregates and column specification

    def test_view_no_columns(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view(columns=[])
        assert view.num_columns() == 0
        assert view.to_records() == [{}, {}]

    def test_view_no_columns_pivoted(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view(row_pivots=["a"], columns=[])
        assert view.num_columns() == 0
        assert view.to_records() == [
            {
                "__ROW_PATH__": []
            }, {
                "__ROW_PATH__": [1]
            }, {
                "__ROW_PATH__": [3]
            }]

    def test_view_specific_column(self):
        data = [{"a": 1, "b": 2, "c": 3, "d": 4}, {"a": 3, "b": 4, "c": 5, "d": 6}]
        tbl = Table(data)
        view = tbl.view(columns=["a", "c", "d"])
        assert view.num_columns() == 3
        assert view.to_records() == [{"a": 1, "c": 3, "d": 4}, {"a": 3, "c": 5, "d": 6}]

    def test_view_column_order(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view(columns=["b", "a"])
        assert view.to_records() == [{"b": 2, "a": 1}, {"b": 4, "a": 3}]

    def test_view_dataframe_column_order(self):
        table = Table(pd.DataFrame({
            "0.1": [5, 6, 7, 8],
            "-0.05": [5, 6, 7, 8],
            "0.0": [1, 2, 3, 4],
            "-0.1": [1, 2, 3, 4],
            "str": ["a", "b", "c", "d"]
        }))
        view = table.view(
            columns=["-0.1", "-0.05", "0.0", "0.1"], row_pivots=["str"])
        assert view.column_paths() == [
            "__ROW_PATH__", "-0.1", "-0.05", "0.0", "0.1"]

    def test_view_aggregate_order_with_columns(self):
        '''If `columns` is provided, order is always guaranteed.'''
        data = [{"a": 1, "b": 2, "c": 3, "d": 4}, {"a": 3, "b": 4, "c": 5, "d": 6}]
        tbl = Table(data)
        view = tbl.view(
            row_pivots=["a"],
            columns=["a", "b", "c", "d"],
            aggregates={"d": "avg", "c": "avg", "b": "last", "a": "last"}
        )

        order = ["__ROW_PATH__", "a", "b", "c", "d"]
        assert view.column_paths() == order

    def test_view_df_aggregate_order_with_columns(self):
        '''If `columns` is provided, order is always guaranteed.'''
        data = pd.DataFrame({
            "a": [1, 2, 3],
            "b": [2, 3, 4],
            "c": [3, 4, 5],
            "d": [4, 5, 6]
        }, columns=["d", "a", "c", "b"])
        tbl = Table(data)
        view = tbl.view(
            row_pivots=["a"],
            aggregates={"d": "avg", "c": "avg", "b": "last", "a": "last"}
        )

        order = ["__ROW_PATH__", "index", "d", "a", "c", "b"]
        assert view.column_paths() == order

    def test_view_aggregates_with_no_columns(self):
        data = [{"a": 1, "b": 2, "c": 3, "d": 4}, {"a": 3, "b": 4, "c": 5, "d": 6}]
        tbl = Table(data)
        view = tbl.view(
            row_pivots=["a"],
            aggregates={"c": "avg", "a": "last"},
            columns=[]
        )
        assert view.to_records() == [
            {"__ROW_PATH__": []},
            {"__ROW_PATH__": [1]},
            {"__ROW_PATH__": [3]}
        ]

    def test_view_aggregates_column_order(self):
        '''Order of columns are entirely determined by the `columns` kwarg. If
        it is not provided, order of columns is undefined behavior.'''
        data = [{"a": 1, "b": 2, "c": 3, "d": 4}, {"a": 3, "b": 4, "c": 5, "d": 6}]
        tbl = Table(data)
        view = tbl.view(
            row_pivots=["a"],
            aggregates={"c": "avg", "a": "last"},
            columns=["a", "c"]
        )

        order = ["__ROW_PATH__", "a", "c"]
        assert view.column_paths() == order

    # row and column pivot paths
    def test_view_row_pivot_datetime_row_paths_are_same_as_data(self):
        """Tests row paths for datetimes in UTC. Timezone-related tests are
        in the `test_table_datetime` file."""
        data = {"a": [datetime(2019, 7, 11, 12, 30)], "b": [1]}
        tbl = Table(data)
        view = tbl.view(row_pivots=["a"])
        data = view.to_dict()

        for rp in data["__ROW_PATH__"]:
            if len(rp) > 0:
                assert rp[0] == datetime(2019, 7, 11, 12, 30)

        assert tbl.view().to_dict() == {
            "a": [datetime(2019, 7, 11, 12, 30)], "b": [1]
        }

    def test_view_column_pivot_datetime_names_utc(self):
        """Tests column paths for datetimes in UTC. Timezone-related tests are
        in the `test_table_datetime` file."""
        data = {"a": [datetime(2019, 7, 11, 12, 30)], "b": [1]}
        tbl = Table(data)
        view = tbl.view(column_pivots=["a"])
        cols = view.column_paths()
        assert cols == ["2019-07-11 12:30:00.000|a", "2019-07-11 12:30:00.000|b"]

    def test_view_column_pivot_datetime_names_min(self):
        """Tests column paths for datetimes in UTC. Timezone-related tests are
        in the `test_table_datetime` file."""
        data = {"a": [datetime.min], "b": [1]}
        tbl = Table(data)
        view = tbl.view(column_pivots=["a"])
        cols = view.column_paths()
        assert cols == ["1970-01-01 00:00:00.000|a", "1970-01-01 00:00:00.000|b"]

    @mark.skip
    def test_view_column_pivot_datetime_names_max(self):
        """Tests column paths for datetimes in UTC. Timezone-related tests are
        in the `test_table_datetime` file."""
        data = {"a": [datetime.max], "b": [1]}
        tbl = Table(data)
        view = tbl.view(column_pivots=["a"])
        cols = view.column_paths()
        assert cols == ["10000-01-01 00:00:00.000|a", "10000-01-01 00:00:00.000|b"]

    # aggregate

    def test_view_aggregate_int(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view(
            aggregates={"a": "avg"},
            row_pivots=["a"]
        )
        assert view.to_records() == [
            {"__ROW_PATH__": [], "a": 2.0, "b": 6},
            {"__ROW_PATH__": [1], "a": 1.0, "b": 2},
            {"__ROW_PATH__": [3], "a": 3.0, "b": 4}
        ]

    def test_view_aggregate_str(self):
        data = [{"a": "abc", "b": 2}, {"a": "def", "b": 4}]
        tbl = Table(data)
        view = tbl.view(
            aggregates={"a": "count"},
            row_pivots=["a"]
        )
        assert view.to_records() == [
            {"__ROW_PATH__": [], "a": 2, "b": 6},
            {"__ROW_PATH__": ["abc"], "a": 1, "b": 2},
            {"__ROW_PATH__": ["def"], "a": 1, "b": 4}
        ]

    def test_view_aggregate_datetime(self):
        data = [{"a": datetime(2019, 10, 1, 11, 30)}, {"a": datetime(2019, 10, 1, 11, 30)}]
        tbl = Table(data)
        view = tbl.view(
            aggregates={"a": "distinct count"},
            row_pivots=["a"]
        )
        assert view.to_records() == [
            {"__ROW_PATH__": [], "a": 1},
            {"__ROW_PATH__": [datetime(2019, 10, 1, 11, 30)], "a": 1}
        ]

    def test_view_aggregate_datetime_leading_zeroes(self):
        data = [{"a": datetime(2019, 1, 1, 5, 5, 5)}, {"a": datetime(2019, 1, 1, 5, 5, 5)}]
        tbl = Table(data)
        view = tbl.view(
            aggregates={"a": "distinct count"},
            row_pivots=["a"]
        )
        assert view.to_records() == [
            {"__ROW_PATH__": [], "a": 1},
            {"__ROW_PATH__": [datetime(2019, 1, 1, 5, 5, 5)], "a": 1}
        ]

    def test_view_aggregate_mean(self):
        data = [
            {"a": "a", "x": 1, "y": 200},
            {"a": "a", "x": 2, "y": 100},
            {"a": "a", "x": 3, "y": None}
        ]
        tbl = Table(data)
        view = tbl.view(
            aggregates={"y": "mean"},
            row_pivots=["a"],
            columns=['y']
        )
        assert view.to_records() == [
            {"__ROW_PATH__": [], "y": 300 / 2},
            {"__ROW_PATH__": ["a"], "y": 300 / 2}
        ]

    def test_view_aggregate_mean_from_schema(self):
        data = [
            {"a": "a", "x": 1, "y": 200},
            {"a": "a", "x": 2, "y": 100},
            {"a": "a", "x": 3, "y": None}
        ]
        tbl = Table({
            "a": str,
            "x": int,
            "y": float
        })
        view = tbl.view(
            aggregates={"y": "mean"},
            row_pivots=["a"],
            columns=['y']
        )
        tbl.update(data)
        assert view.to_records() == [
            {"__ROW_PATH__": [], "y": 300 / 2},
            {"__ROW_PATH__": ["a"], "y": 300 / 2}
        ]

    def test_view_aggregate_weighted_mean(self):
        data = [
            {"a": "a", "x": 1, "y": 200},
            {"a": "a", "x": 2, "y": 100},
            {"a": "a", "x": 3, "y": None}
        ]
        tbl = Table(data)
        view = tbl.view(
            aggregates={"y": ["weighted mean", "x"]},
            row_pivots=["a"],
            columns=['y']
        )
        assert view.to_records() == [
            {"__ROW_PATH__": [], "y": (1.0 * 200 + 2 * 100) / (1.0 + 2)},
            {"__ROW_PATH__": ["a"], "y": (1.0 * 200 + 2 * 100) / (1.0 + 2)}
        ]

    def test_view_aggregate_weighted_mean_with_negative_weights(self):
        data = [
            {"a": "a", "x": 1, "y": 200},
            {"a": "a", "x": -2, "y": 100},
            {"a": "a", "x": 3, "y": None}
        ]
        tbl = Table(data)
        view = tbl.view(
            aggregates={"y": ["weighted mean", "x"]},
            row_pivots=["a"],
            columns=['y']
        )
        assert view.to_records() == [
            {"__ROW_PATH__": [], "y": (1 * 200 + (-2) * 100) / (1 - 2)},
            {"__ROW_PATH__": ["a"], "y": (1 * 200 + (-2) * 100) / (1 - 2)}
        ]

    # sort

    def test_view_sort_int(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view(sort=[["a", "desc"]])
        assert view.to_records() == [{"a": 3, "b": 4}, {"a": 1, "b": 2}]

    def test_view_sort_float(self):
        data = [{"a": 1.1, "b": 2}, {"a": 1.2, "b": 4}]
        tbl = Table(data)
        view = tbl.view(sort=[["a", "desc"]])
        assert view.to_records() == [{"a": 1.2, "b": 4}, {"a": 1.1, "b": 2}]

    def test_view_sort_string(self):
        data = [{"a": "abc", "b": 2}, {"a": "def", "b": 4}]
        tbl = Table(data)
        view = tbl.view(sort=[["a", "desc"]])
        assert view.to_records() == [{"a": "def", "b": 4}, {"a": "abc", "b": 2}]

    def test_view_sort_date(self):
        data = [{"a": date(2019, 7, 11), "b": 2}, {"a": date(2019, 7, 12), "b": 4}]
        tbl = Table(data)
        view = tbl.view(sort=[["a", "desc"]])
        assert view.to_records() == [{"a": datetime(2019, 7, 12), "b": 4}, {"a": datetime(2019, 7, 11), "b": 2}]

    def test_view_sort_datetime(self):
        data = [{"a": datetime(2019, 7, 11, 8, 15), "b": 2}, {"a": datetime(2019, 7, 11, 8, 16), "b": 4}]
        tbl = Table(data)
        view = tbl.view(sort=[["a", "desc"]])
        assert view.to_records() == [{"a": datetime(2019, 7, 11, 8, 16), "b": 4}, {"a": datetime(2019, 7, 11, 8, 15), "b": 2}]

    def test_view_sort_hidden(self):
        data = [{"a": 1.1, "b": 2}, {"a": 1.2, "b": 4}]
        tbl = Table(data)
        view = tbl.view(sort=[["a", "desc"]], columns=["b"])
        assert view.to_records() == [{"b": 4}, {"b": 2}]

    def test_view_sort_avg_nan(self):
        data = {
            "w": [3.5, 4.5, None, None, None, None, 1.5, 2.5],
            "x": [1, 2, 3, 4, 4, 3, 2, 1],
            "y": ["a", "b", "c", "d", "e", "f", "g", "h"]
        }
        tbl = Table(data)
        view = tbl.view(
            columns=["x", "w"],
            row_pivots=["y"],
            sort=[["w", "asc"]],
            aggregates={
                "w": "avg",
                "x": "unique"
            },
        )
        assert view.to_dict() == {
            "__ROW_PATH__": [[], ["c"], ["d"], ["e"], ["f"], ["g"], ["h"], ["a"], ["b"]],
            "w": [3, None, None, None, None, 1.5, 2.5, 3.5, 4.5],
            "x": [None, 3, 4, 4, 3, 2, 1, 1, 2]
        }

    def test_view_sort_sum_nan(self):
        data = {
            "w": [3.5, 4.5, None, None, None, None, 1.5, 2.5],
            "x": [1, 2, 3, 4, 4, 3, 2, 1],
            "y": ["a", "b", "c", "d", "e", "f", "g", "h"]
        }
        tbl = Table(data)
        view = tbl.view(
            columns=["x", "w"],
            row_pivots=["y"],
            sort=[["w", "asc"]],
            aggregates={
                "w": "sum",
                "x": "unique"
            },
        )
        assert view.to_dict() == {
            "__ROW_PATH__": [[], ["c"], ["d"], ["e"], ["f"], ["g"], ["h"], ["a"], ["b"]],
            "w": [12, 0, 0, 0, 0, 1.5, 2.5, 3.5, 4.5],
            "x": [None, 3, 4, 4, 3, 2, 1, 1, 2]
        }

    def test_view_sort_unique_nan(self):
        data = {
            "w": [3.5, 4.5, None, None, None, None, 1.5, 2.5],
            "x": [1, 2, 3, 4, 4, 3, 2, 1],
            "y": ["a", "b", "c", "d", "e", "f", "g", "h"]
        }
        tbl = Table(data)
        view = tbl.view(
            columns=["x", "w"],
            row_pivots=["y"],
            sort=[["w", "asc"]],
            aggregates={
                "w": "unique",
                "x": "unique"
            },
        )
        assert view.to_dict() == {
            "__ROW_PATH__": [[], ["c"], ["d"], ["e"], ["f"], ["g"], ["h"], ["a"], ["b"]],
            "w": [None, None, None, None, None, 1.5, 2.5, 3.5, 4.5],
            "x": [None, 3, 4, 4, 3, 2, 1, 1, 2]
        }

    # filter

    def test_view_filter_int_eq(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "==", 1]])
        assert view.to_records() == [{"a": 1, "b": 2}]

    def test_view_filter_int_neq(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "!=", 1]])
        assert view.to_records() == [{"a": 3, "b": 4}]

    def test_view_filter_int_gt(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", ">", 1]])
        assert view.to_records() == [{"a": 3, "b": 4}]

    def test_view_filter_int_lt(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "<", 3]])
        assert view.to_records() == [{"a": 1, "b": 2}]

    def test_view_filter_float_eq(self):
        data = [{"a": 1.1, "b": 2}, {"a": 1.2, "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "==", 1.2]])
        assert view.to_records() == [{"a": 1.2, "b": 4}]

    def test_view_filter_float_neq(self):
        data = [{"a": 1.1, "b": 2}, {"a": 1.2, "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "!=", 1.2]])
        assert view.to_records() == [{"a": 1.1, "b": 2}]

    def test_view_filter_string_eq(self):
        data = [{"a": "abc", "b": 2}, {"a": "def", "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "==", "def"]])
        assert view.to_records() == [{"a": "def", "b": 4}]

    def test_view_filter_string_neq(self):
        data = [{"a": "abc", "b": 2}, {"a": "def", "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "!=", "def"]])
        assert view.to_records() == [{"a": "abc", "b": 2}]

    def test_view_filter_string_gt(self):
        data = [{"a": "abc", "b": 2}, {"a": "def", "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", ">", "abc"]])
        assert view.to_records() == [{"a": "def", "b": 4}]

    def test_view_filter_string_lt(self):
        data = [{"a": "abc", "b": 2}, {"a": "def", "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "<", "def"]])
        assert view.to_records() == [{"a": "abc", "b": 2}]

    def test_view_filter_date_eq(self):
        data = [{"a": date(2019, 7, 11), "b": 2}, {"a": date(2019, 7, 12), "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "==", date(2019, 7, 12)]])
        assert view.to_records() == [{"a": datetime(2019, 7, 12), "b": 4}]

    def test_view_filter_date_neq(self):
        data = [{"a": date(2019, 7, 11), "b": 2}, {"a": date(2019, 7, 12), "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "!=", date(2019, 7, 12)]])
        assert view.to_records() == [{"a": datetime(2019, 7, 11), "b": 2}]

    def test_view_filter_date_np_eq(self):
        data = [{"a": date(2019, 7, 11), "b": 2}, {"a": date(2019, 7, 12), "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "==", np.datetime64(date(2019, 7, 12))]])
        assert view.to_records() == [{"a": datetime(2019, 7, 12), "b": 4}]

    def test_view_filter_date_np_neq(self):
        data = [{"a": date(2019, 7, 11), "b": 2}, {"a": date(2019, 7, 12), "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "!=", np.datetime64(date(2019, 7, 12))]])
        assert view.to_records() == [{"a": datetime(2019, 7, 11), "b": 2}]

    def test_view_filter_date_str_eq(self):
        data = [{"a": date(2019, 7, 11), "b": 2}, {"a": date(2019, 7, 12), "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "==", "2019/7/12"]])
        assert view.to_records() == [{"a": datetime(2019, 7, 12), "b": 4}]

    def test_view_filter_date_str_neq(self):
        data = [{"a": date(2019, 7, 11), "b": 2}, {"a": date(2019, 7, 12), "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "!=", "2019/7/12"]])
        assert view.to_records() == [{"a": datetime(2019, 7, 11), "b": 2}]

    def test_view_filter_datetime_eq(self):
        data = [{"a": datetime(2019, 7, 11, 8, 15), "b": 2}, {"a": datetime(2019, 7, 11, 8, 16), "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "==", datetime(2019, 7, 11, 8, 15)]])
        assert view.to_records() == [{"a": datetime(2019, 7, 11, 8, 15), "b": 2}]

    def test_view_filter_datetime_neq(self):
        data = [{"a": datetime(2019, 7, 11, 8, 15), "b": 2}, {"a": datetime(2019, 7, 11, 8, 16), "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "!=", datetime(2019, 7, 11, 8, 15)]])
        assert view.to_records() == [{"a": datetime(2019, 7, 11, 8, 16), "b": 4}]

    def test_view_filter_datetime_np_eq(self):
        data = [{"a": datetime(2019, 7, 11, 8, 15), "b": 2}, {"a": datetime(2019, 7, 11, 8, 16), "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "==", np.datetime64(datetime(2019, 7, 11, 8, 15))]])
        assert view.to_records() == [{"a": datetime(2019, 7, 11, 8, 15), "b": 2}]

    def test_view_filter_datetime_np_neq(self):
        data = [{"a": datetime(2019, 7, 11, 8, 15), "b": 2}, {"a": datetime(2019, 7, 11, 8, 16), "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "!=", np.datetime64(datetime(2019, 7, 11, 8, 15))]])
        assert view.to_records() == [{"a": datetime(2019, 7, 11, 8, 16), "b": 4}]

    def test_view_filter_datetime_str_eq(self):
        data = [{"a": datetime(2019, 7, 11, 8, 15), "b": 2}, {"a": datetime(2019, 7, 11, 8, 16), "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "==", "2019/7/11 8:15"]])
        assert view.to_records() == [{"a": datetime(2019, 7, 11, 8, 15), "b": 2}]

    def test_view_filter_datetime_str_neq(self):
        data = [{"a": datetime(2019, 7, 11, 8, 15), "b": 2}, {"a": datetime(2019, 7, 11, 8, 16), "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "!=", "2019/7/11 8:15"]])
        assert view.to_records() == [{"a": datetime(2019, 7, 11, 8, 16), "b": 4}]

    def test_view_filter_string_is_none(self):
        data = [{"a": None, "b": 2}, {"a": "abc", "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "is null"]])
        assert view.to_records() == [{"a": None, "b": 2}]

    def test_view_filter_string_is_not_none(self):
        data = [{"a": None, "b": 2}, {"a": "abc", "b": 4}]
        tbl = Table(data)
        view = tbl.view(filter=[["a", "is not null"]])
        assert view.to_records() == [{"a": "abc", "b": 4}]

    # on_update
    def test_view_on_update(self, sentinel):
        s = sentinel(False)

        def callback(port_id):
            s.set(True)

        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view()
        view.on_update(callback)
        tbl.update(data)
        assert s.get() is True

    def test_view_on_update_multiple_callback(self, sentinel):
        s = sentinel(0)

        def callback(port_id):
            s.set(s.get() + 1)

        def callback1(port_id):
            s.set(s.get() - 1)

        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view()
        view.on_update(callback)
        view.on_update(callback1)
        tbl.update(data)
        assert s.get() == 0

    # on_delete

    def test_view_on_delete(self, sentinel):
        s = sentinel(False)

        def callback():
            s.set(True)

        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view()
        view.on_delete(callback)
        view.delete()
        assert s.get() is True

    # delete

    def test_view_delete(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view()
        view.delete()
        assert tbl._views == []

    def test_view_delete_multiple_callbacks(self, sentinel):
        # make sure that callbacks on views get filtered
        s = sentinel(0)

        def cb1(port_id):
            s.set(s.get() + 1)

        def cb2(port_id):
            s.set(s.get() + 2)

        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        v1 = tbl.view()
        v2 = tbl.view()
        v1.on_update(cb1)
        v2.on_update(cb2)
        v1.delete()
        assert len(tbl._views) == 1
        tbl.update(data)
        assert s.get() == 2

    def test_view_delete_full_cleanup(self, sentinel):
        s = sentinel(0)

        def cb1(port_id):
            s.set(s.get() + 1)

        def cb2(port_id):
            s.set(s.get() + 2)

        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        v1 = tbl.view()
        v2 = tbl.view()
        v1.on_update(cb1)
        v2.on_update(cb2)
        v1.delete()
        v2.delete()
        tbl.update(data)
        assert s.get() == 0

    # remove_update

    def test_view_remove_update(self, sentinel):
        s = sentinel(0)

        def cb1(port_id):
            s.set(s.get() + 1)

        def cb2(port_id):
            s.set(s.get() + 2)

        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view()
        view.on_update(cb1)
        view.on_update(cb2)
        view.remove_update(cb1)
        tbl.update(data)
        assert s.get() == 2

    def test_view_remove_multiple_update(self, sentinel):
        s = sentinel(0)

        def cb1(port_id):
            s.set(s.get() + 1)

        def cb2(port_id):
            s.set(s.get() + 2)

        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view()
        view.on_update(cb1)
        view.on_update(cb2)
        view.on_update(cb1)
        view.remove_update(cb1)
        assert len(view._update_callbacks) == 1
        tbl.update(data)
        assert s.get() == 2

    # row delta

    def test_view_row_delta_zero(self, util):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        update_data = {
            "a": [5],
            "b": [6]
        }

        def cb1(port_id, delta):
            compare_delta(delta, update_data)

        tbl = Table(data)
        view = tbl.view()
        view.on_update(cb1, mode="row")
        tbl.update(update_data)

    def test_view_row_delta_zero_column_subset(self, util):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        update_data = {
            "a": [5],
            "b": [6]
        }

        def cb1(port_id, delta):
            compare_delta(delta, {
                "b": [6]
            })

        tbl = Table(data)
        view = tbl.view(columns=["b"])
        view.on_update(cb1, mode="row")
        tbl.update(update_data)

    def test_view_row_delta_zero_from_schema(self, util):
        update_data = {
            "a": [5],
            "b": [6]
        }

        def cb1(port_id, delta):
            compare_delta(delta, update_data)

        tbl = Table({
            "a": int,
            "b": int
        })
        view = tbl.view()
        view.on_update(cb1, mode="row")
        tbl.update(update_data)

    def test_view_row_delta_zero_from_schema_column_subset(self, util):
        update_data = {
            "a": [5],
            "b": [6]
        }

        def cb1(port_id, delta):            
            compare_delta(delta, {
                "b": [6]
            })

        tbl = Table({
            "a": int,
            "b": int
        })

        view = tbl.view(columns=["b"])
        view.on_update(cb1, mode="row")
        tbl.update(update_data)

    def test_view_row_delta_zero_from_schema_filtered(self, util):
        update_data = {
            "a": [8, 9, 10, 11],
            "b": [1, 2, 3, 4]
        }

        def cb1(port_id, delta):
            compare_delta(delta, {
                "a": [11],
                "b": [4]
            })

        tbl = Table({
            "a": int,
            "b": int
        })
        view = tbl.view(filter=[["a", ">", 10]])
        view.on_update(cb1, mode="row")
        tbl.update(update_data)

    def test_view_row_delta_zero_from_schema_indexed(self, util):
        update_data = {
            "a": ["a", "b", "a"],
            "b": [1, 2, 3]
        }

        def cb1(port_id, delta):
            compare_delta(delta, {
                "a": ["a", "b"],
                "b": [3, 2]
            })

        tbl = Table({
            "a": str,
            "b": int
        }, index="a")

        view = tbl.view()
        view.on_update(cb1, mode="row")

        tbl.update(update_data)

    def test_view_row_delta_zero_from_schema_indexed_filtered(self, util):
        update_data = {
            "a": [8, 9, 10, 11, 11],
            "b": [1, 2, 3, 4, 5]
        }

        def cb1(port_id, delta):
            compare_delta(delta, {
                "a": [11],
                "b": [5]
            })

        tbl = Table({
            "a": int,
            "b": int
        }, index="a")
        view = tbl.view(filter=[["a", ">", 10]])
        view.on_update(cb1, mode="row")
        tbl.update(update_data)

    def test_view_row_delta_one(self, util):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        update_data = {
            "a": [5],
            "b": [6]
        }

        def cb1(port_id, delta):
            compare_delta(delta, {
                "a": [9, 5],
                "b": [12, 6]
            })

        tbl = Table(data)
        view = tbl.view(row_pivots=["a"])
        assert view.to_dict() == {
            "__ROW_PATH__": [[], [1], [3]],
            "a": [4, 1, 3],
            "b": [6, 2, 4]
        }
        view.on_update(cb1, mode="row")
        tbl.update(update_data)

    def test_view_row_delta_one_from_schema(self, util):
        update_data = {
            "a": [1, 2, 3, 4, 5],
            "b": [6, 7, 8, 9, 10]
        }

        def cb1(port_id, delta):
            compare_delta(delta, {
                "a": [15, 1, 2, 3, 4, 5],
                "b": [40, 6, 7, 8, 9, 10]
            })

        tbl = Table({
            "a": int,
            "b": int
        })
        view = tbl.view(row_pivots=["a"])
        view.on_update(cb1, mode="row")
        tbl.update(update_data)

    def test_view_row_delta_one_from_schema_sorted(self, util):
        update_data = {
            "a": [1, 2, 3, 4, 5],
            "b": [6, 7, 8, 9, 10]
        }

        def cb1(port_id, delta):
            compare_delta(delta, {
                "a": [15, 5, 4, 3, 2, 1],
                "b": [40, 10, 9, 8, 7, 6]
            })

        tbl = Table({
            "a": int,
            "b": int
        })
        view = tbl.view(row_pivots=["a"], sort=[["a", "desc"]])
        view.on_update(cb1, mode="row")
        tbl.update(update_data)

    def test_view_row_delta_one_from_schema_filtered(self, util):
        update_data = {
            "a": [1, 2, 3, 4, 5],
            "b": [6, 7, 8, 9, 10]
        }

        def cb1(port_id, delta):
            compare_delta(delta, {
                "a": [9, 4, 5],
                "b": [19, 9, 10]
            })

        tbl = Table({
            "a": int,
            "b": int
        })
        view = tbl.view(row_pivots=["a"], filter=[["a", ">", 3]])
        view.on_update(cb1, mode="row")
        tbl.update(update_data)

    def test_view_row_delta_one_from_schema_sorted_filtered(self, util):
        update_data = {
            "a": [1, 2, 3, 4, 5],
            "b": [6, 7, 8, 9, 10]
        }

        def cb1(port_id, delta):
            compare_delta(delta, {
                "a": [9, 5, 4],
                "b": [19, 10, 9]
            })

        tbl = Table({
            "a": int,
            "b": int
        })
        view = tbl.view(
            row_pivots=["a"],
            sort=[["a", "desc"]],
            filter=[["a", ">", 3]])
        view.on_update(cb1, mode="row")
        tbl.update(update_data)

    def test_view_row_delta_one_from_schema_indexed(self, util):
        update_data = {
            "a": [1, 2, 3, 4, 5, 5, 4],
            "b": [6, 7, 8, 9, 10, 11, 12]
        }

        def cb1(port_id, delta):
            compare_delta(delta, {
                "a": [15, 1, 2, 3, 4, 5],
                "b": [44, 6, 7, 8, 12, 11]
            })

        tbl = Table({
            "a": int,
            "b": int
        }, index="a")

        view = tbl.view(row_pivots=["a"])
        view.on_update(cb1, mode="row")

        tbl.update(update_data)

    def test_view_row_delta_one_from_schema_sorted_indexed(self, util):
        update_data = {
            "a": [1, 2, 3, 4, 5, 5, 4],
            "b": [6, 7, 8, 9, 10, 11, 12]
        }

        def cb1(port_id, delta):
            compare_delta(delta, {
                "a": [15, 4, 5, 3, 2, 1],
                "b": [44, 12, 11, 8, 7, 6]
            })

        tbl = Table({
            "a": int,
            "b": int
        }, index="a")

        view = tbl.view(row_pivots=["a"], sort=[["b", "desc"]])
        view.on_update(cb1, mode="row")

        tbl.update(update_data)

    def test_view_row_delta_one_from_schema_filtered_indexed(self, util):
        update_data = {
            "a": [1, 2, 3, 4, 5, 5, 4],
            "b": [6, 7, 8, 9, 10, 11, 12]
        }

        def cb1(port_id, delta):
            compare_delta(delta, {
                "a": [9, 4, 5],
                "b": [23, 12, 11]
            })

        tbl = Table({
            "a": int,
            "b": int
        }, index="a")

        view = tbl.view(row_pivots=["a"], filter=[["a", ">", 3]])
        view.on_update(cb1, mode="row")

        tbl.update(update_data)

    def test_view_row_delta_two(self, util):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        update_data = {
            "a": [5],
            "b": [6]
        }

        def cb1(port_id, delta):
            compare_delta(delta, {
                "2|a": [1, None],
                "2|b": [2, None],
                "4|a": [3, None],
                "4|b": [4, None],
                "6|a": [5, 5],
                "6|b": [6, 6]
            })

        tbl = Table(data)
        view = tbl.view(row_pivots=["a"], column_pivots=["b"])
        assert view.to_dict() == {
            "__ROW_PATH__": [[], [1], [3]],
            "2|a": [1, 1, None],
            "2|b": [2, 2, None],
            "4|a": [3, None, 3],
            "4|b": [4, None, 4],
        }
        view.on_update(cb1, mode="row")
        tbl.update(update_data)

    def test_view_row_delta_two_from_schema(self, util):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]

        def cb1(port_id, delta):
            compare_delta(delta, {
                "2|a": [1, 1, None],
                "2|b": [2, 2, None],
                "4|a": [3, None, 3],
                "4|b": [4, None, 4]
            })

        tbl = Table({
            "a": int,
            "b": int
        })
        view = tbl.view(row_pivots=["a"], column_pivots=["b"])
        view.on_update(cb1, mode="row")
        tbl.update(data)

    def test_view_row_delta_two_from_schema_indexed(self, util):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}, {"a": 3, "b": 5}]

        def cb1(port_id, delta):
            compare_delta(delta, {
                "2|a": [1, 1, None],
                "2|b": [2, 2, None],
                "5|a": [3, None, 3],
                "5|b": [5, None, 5]
            })

        tbl = Table({
            "a": int,
            "b": int
        }, index="a")
        view = tbl.view(row_pivots=["a"], column_pivots=["b"])
        view.on_update(cb1, mode="row")
        tbl.update(data)

    def test_view_row_delta_two_column_only(self, util):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        update_data = {
            "a": [5],
            "b": [6]
        }

        def cb1(port_id, delta):
            compare_delta(delta, {
                "2|a": [1, None],
                "2|b": [2, None],
                "4|a": [3, None],
                "4|b": [4, None],
                "6|a": [5, 5],
                "6|b": [6, 6]
            })

        tbl = Table(data)
        view = tbl.view(column_pivots=["b"])
        assert view.to_dict() == {
            "2|a": [1, None],
            "2|b": [2, None],
            "4|a": [None, 3],
            "4|b": [None, 4],
        }
        view.on_update(cb1, mode="row")
        tbl.update(update_data)

    def test_view_row_delta_two_column_only_indexed(self, util):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}, {"a": 3, "b": 5}]
        update_data = {
            "a": [5],
            "b": [6]
        }

        def cb1(port_id, delta):
            compare_delta(delta, {
                "2|a": [1, None],
                "2|b": [2, None],
                "5|a": [3, None],
                "5|b": [5, None],
                "6|a": [5, 5],
                "6|b": [6, 6]
            })

        tbl = Table(data, index="a")
        view = tbl.view(column_pivots=["b"])
        assert view.to_dict() == {
            "2|a": [1, None],
            "2|b": [2, None],
            "5|a": [None, 3],
            "5|b": [None, 5],
        }
        view.on_update(cb1, mode="row")
        tbl.update(update_data)

    def test_view_row_delta_two_column_only_from_schema(self, util):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]

        def cb1(port_id, delta):
            compare_delta(delta, {
                "2|a": [1, 1, None],
                "2|b": [2, 2, None],
                "4|a": [3, None, 3],
                "4|b": [4, None, 4]
            })

        tbl = Table({
            "a": int,
            "b": int
        })
        view = tbl.view(column_pivots=["b"])
        view.on_update(cb1, mode="row")
        tbl.update(data)

    def test_view_row_delta_two_column_only_from_schema_indexed(self, util):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}, {"a": 3, "b": 5}]

        def cb1(port_id, delta):
            compare_delta(delta, {
                "2|a": [1, 1, None],
                "2|b": [2, 2, None],
                "5|a": [3, None, 3],
                "5|b": [5, None, 5]
            })

        tbl = Table({
            "a": int,
            "b": int
        }, index="a")
        view = tbl.view(column_pivots=["b"])
        view.on_update(cb1, mode="row")
        tbl.update(data)

    # hidden cols

    def test_view_num_hidden_cols(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view(columns=["a"], sort=[["b", "desc"]])
        assert view._num_hidden_cols() == 1

    def test_view_context_two_update_clears_column_regression(self, util):
        """Tests that, when a 2-sided View() is updated to a state where one of
        the column groups is empty, an infinite loop is not encountered.
        """
        data = [
            {"a": "a", "b": 1, "c": 1.5, "i": 0},
            {"a": "a", "b": 2, "c": 2.5, "i": 1},
            {"a": "a", "b": 3, "c": 3.5, "i": 2},
            {"a": "b", "b": 1, "c": 4.5, "i": 3},
            {"a": "b", "b": 2, "c": 5.5, "i": 4},
            {"a": "b", "b": 3, "c": 6.5, "i": 5},
        ]

        tbl = Table(data, index="i")
        view = tbl.view(
            row_pivots=["b"],
            column_pivots=["a"],
            columns=["c"],
            filter=[["c", ">", 0]],
            sort=[["c", "asc"], ["a", "col asc"]],
        )

        assert view.to_records() == [
             {'__ROW_PATH__': [], 'a|c': 7.5, 'b|c': 16.5},
             {'__ROW_PATH__': [1], 'a|c': 1.5, 'b|c': 4.5},
             {'__ROW_PATH__': [2], 'a|c': 2.5, 'b|c': 5.5},
             {'__ROW_PATH__': [3], 'a|c': 3.5, 'b|c': 6.5}
        ]

        tbl.update(
            [
                {"c": -1, "i": 0},
                {"c": -1, "i": 1},
                {"c": -1, "i": 2},
            ]
        )

        assert view.to_records() == [
            {"__ROW_PATH__": [], "b|c": 16.5},
            {"__ROW_PATH__": [1], "b|c": 4.5},
            {"__ROW_PATH__": [2], "b|c": 5.5},
            {"__ROW_PATH__": [3], "b|c": 6.5},
        ]

        tbl.update(
            [
                {"a": "a", "b": 1, "c": 1.5, "i": 6},
                {"a": "a", "b": 2, "c": 2.5, "i": 7},
                {"a": "a", "b": 3, "c": 3.5, "i": 8},
            ]
        )

        assert view.to_records() == [
             {'__ROW_PATH__': [], 'a|c': 7.5, 'b|c': 16.5},
             {'__ROW_PATH__': [1], 'a|c': 1.5, 'b|c': 4.5},
             {'__ROW_PATH__': [2], 'a|c': 2.5, 'b|c': 5.5},
             {'__ROW_PATH__': [3], 'a|c': 3.5, 'b|c': 6.5}
        ]

        assert tbl.size() == 9

    # expand/collapse

    def test_view_collapse_one(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view(row_pivots=["a"])
        assert view.collapse(0) == 2

    def test_view_collapse_two(self):
        data = [{"a": 1, "b": 2, "c": "a"}, {"a": 3, "b": 4, "c": "b"}]
        tbl = Table(data)
        view = tbl.view(row_pivots=["a"], column_pivots=["c"])
        assert view.collapse(0) == 0

    def test_view_collapse_two_column_only(self):
        data = [{"a": 1, "b": 2, "c": "a"}, {"a": 3, "b": 4, "c": "b"}]
        tbl = Table(data)
        view = tbl.view(column_pivots=["c"])
        assert view.collapse(0) == 0

    def test_view_expand_one(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        tbl = Table(data)
        view = tbl.view(row_pivots=["a"])
        assert view.expand(0) == 0

    def test_view_expand_two(self):
        data = [{"a": 1, "b": 2, "c": "a"}, {"a": 3, "b": 4, "c": "b"}]
        tbl = Table(data)
        view = tbl.view(row_pivots=["a"], column_pivots=["c"])
        assert view.expand(1) == 1

    def test_view_expand_two_column_only(self):
        data = [{"a": 1, "b": 2, "c": "a"}, {"a": 3, "b": 4, "c": "b"}]
        tbl = Table(data)
        view = tbl.view(column_pivots=["c"])
        assert view.expand(0) == 0

    # view config validation

    def test_invalid_column_should_throw(self):
        data = [{"a": 1, "b": 2, "c": "a"}, {"a": 3, "b": 4, "c": "b"}]
        tbl = Table(data)
        with raises(PerspectiveCppError) as ex:
            tbl.view(columns=["x"])
        assert str(ex.value) == "Invalid column 'x' found in View columns.\n"

    def test_invalid_column_should_throw_and_updates_should_work(self):
        data = [{"a": 1, "b": 2, "c": "a"}, {"a": 3, "b": 4, "c": "b"}]
        tbl = Table(data)

        with raises(PerspectiveCppError) as ex:
            tbl.view(columns=["x"])
        assert str(ex.value) == "Invalid column 'x' found in View columns.\n"

        for i in range(100):
            tbl.update(data)
            # force call to _process which should shake out invalid column ptrs
            tbl.size()

        view2 = tbl.view()
        assert view2.num_rows() == 202

    def test_invalid_column_aggregate_should_throw(self):
        data = [{"a": 1, "b": 2, "c": "a"}, {"a": 3, "b": 4, "c": "b"}]
        tbl = Table(data)

        with raises(PerspectiveCppError) as ex:
            tbl.view(columns=["x"], aggregates={"x": "sum"})

        assert str(ex.value) == "Invalid column 'x' found in View columns.\n"

    def test_invalid_column_aggregate_should_throw_and_updates_should_work(self):
        data = [{"a": 1, "b": 2, "c": "a"}, {"a": 3, "b": 4, "c": "b"}]
        tbl = Table(data)

        with raises(PerspectiveCppError) as ex:
            tbl.view(columns=["x"], aggregates={"x": "sum"})

        assert str(ex.value) == "Invalid column 'x' found in View columns.\n"

        for i in range(100):
            tbl.update(data)
            # force call to _process which should shake out invalid column ptrs
            tbl.size()

        view2 = tbl.view()
        assert view2.num_rows() == 202

    def test_invalid_row_pivot_should_throw(self):
        data = [{"a": 1, "b": 2, "c": "a"}, {"a": 3, "b": 4, "c": "b"}]
        tbl = Table(data)
        with raises(PerspectiveCppError) as ex:
            tbl.view(row_pivots=["x"])
        assert str(ex.value) == "Invalid column 'x' found in View row_pivots.\n"

    def test_invalid_column_pivot_should_throw(self):
        data = [{"a": 1, "b": 2, "c": "a"}, {"a": 3, "b": 4, "c": "b"}]
        tbl = Table(data)
        with raises(PerspectiveCppError) as ex:
            tbl.view(column_pivots=["x"])
        assert str(ex.value) == "Invalid column 'x' found in View column_pivots.\n"

    def test_invalid_filters_should_throw(self):
        data = [{"a": 1, "b": 2, "c": "a"}, {"a": 3, "b": 4, "c": "b"}]
        tbl = Table(data)
        with raises(PerspectiveCppError) as ex:
            tbl.view(filter=[["x", "==", "abc"]])
        assert str(ex.value) == "Could not get dtype for column `x` as it does not exist in the schema.\n"

    def test_invalid_sorts_should_throw(self):
        data = [{"a": 1, "b": 2, "c": "a"}, {"a": 3, "b": 4, "c": "b"}]
        tbl = Table(data)
        with raises(PerspectiveCppError) as ex:
            tbl.view(sort=[["x", "desc"]])
        assert str(ex.value) == "Invalid column 'x' found in View sorts.\n"

    def test_should_throw_on_first_invalid(self):
        data = [{"a": 1, "b": 2, "c": "a"}, {"a": 3, "b": 4, "c": "b"}]
        tbl = Table(data)
        with raises(PerspectiveCppError) as ex:
            tbl.view(row_pivots=["a"], column_pivots=["c"], filter=[["a", ">", 1]], aggregates={"a": "avg"}, sort=[["x", "desc"]])
        assert str(ex.value) == "Invalid column 'x' found in View sorts.\n"

    def test_invalid_columns_not_in_expression_should_throw(self):
        data = [{"a": 1, "b": 2, "c": "a"}, {"a": 3, "b": 4, "c": "b"}]
        tbl = Table(data)
        with raises(PerspectiveCppError) as ex:
            tbl.view(
                columns=["abc", "x"],
                expressions=['// abc \n 1 + 2']
            )
        assert str(ex.value) == "Invalid column 'x' found in View columns.\n"

    def test_should_not_throw_valid_expression(self):
        data = [{"a": 1, "b": 2, "c": "a"}, {"a": 3, "b": 4, "c": "b"}]
        tbl = Table(data)
        view = tbl.view(
            columns=["abc"],
            expressions=["// abc \n 'hello!'"]
        )

        assert view.schema() == {
            "abc": str
        }

    def test_should_not_throw_valid_expression_config(self):
        data = [{"a": 1, "b": 2, "c": "a"}, {"a": 3, "b": 4, "c": "b"}]
        tbl = Table(data)
        view = tbl.view(
            aggregates={
                "abc": "dominant"
            },
            columns=["abc"],
            sort=[["abc", "desc"]],
            filter=[["abc", "==", "A"]],
            row_pivots=["abc"],
            column_pivots=["abc"],
            expressions=["// abc \n 'hello!'"]
        )

        assert view.schema() == {
            "abc": str
        }
