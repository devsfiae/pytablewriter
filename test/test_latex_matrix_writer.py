# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import, print_function, unicode_literals

import collections
import itertools

import pytablewriter as ptw
import pytest
from pytablewriter.style import FontSize, Style

from ._common import print_test_result
from .data import float_header_list, float_value_matrix, style_list, style_tabledata, value_matrix


Data = collections.namedtuple("Data", "table header value expected")

normal_test_data_list = [
    Data(
        table="",
        header=float_header_list,
        value=float_value_matrix,
        expected=r"""\begin{equation}
    \left( \begin{array}{rrr}
        0.01 &      0.0012 & 0.000 \\
        1.00 &     99.9000 & 0.010 \\
        1.20 & 999999.1230 & 0.001 \\
    \end{array} \right)
\end{equation}
""",
    ),
    Data(
        table="A",
        header=float_header_list,
        value=float_value_matrix,
        expected=r"""\begin{equation}
    A = \left( \begin{array}{rrr}
        0.01 &      0.0012 & 0.000 \\
        1.00 &     99.9000 & 0.010 \\
        1.20 & 999999.1230 & 0.001 \\
    \end{array} \right)
\end{equation}
""",
    ),
    Data(
        table="B",
        header=None,
        value=[
            ["a_{11}", "a_{12}", r"\ldots", "a_{1n}"],
            ["a_{21}", "a_{22}", r"\ldots", "a_{2n}"],
            ["a_{31}", "a_{32}", r"\ldots", "a_{3n}"],
        ],
        expected=r"""\begin{equation}
    B = \left( \begin{array}{llll}
        a_{11} & a_{12} & \ldots & a_{1n} \\
        a_{21} & a_{22} & \ldots & a_{2n} \\
        a_{31} & a_{32} & \ldots & a_{3n} \\
    \end{array} \right)
\end{equation}
""",
    ),
    Data(
        table="C",
        header="",
        value=value_matrix,
        expected=r"""\begin{equation}
    C = \left( \begin{array}{rrlrl}
        1 & 123.1 & a   & 1.0 &    1 \\
        2 &   2.2 & bb  & 2.2 &  2.2 \\
        3 &   3.3 & ccc & 3.0 & cccc \\
    \end{array} \right)
\end{equation}
""",
    ),
]

exception_test_data_list = [
    Data(table=table, header=header, value=value, expected=ptw.EmptyTableDataError)
    for table, header, value in itertools.product([None, [], ""], [None, [], ""], [None, [], ""])
]

table_writer_class = ptw.LatexMatrixWriter


class Test_LatexMatrixWriter_write_new_line(object):
    def test_normal(self, capsys):
        writer = table_writer_class()
        writer.write_null_line()

        out, _err = capsys.readouterr()

        assert out == "\n"


class Test_LatexMatrixWriter_write_table(object):
    @pytest.mark.parametrize(
        ["table", "header", "value", "expected"],
        [[data.table, data.header, data.value, data.expected] for data in normal_test_data_list],
    )
    def test_normal(self, capsys, table, header, value, expected):
        writer = table_writer_class()
        writer.table_name = table
        writer.header_list = header
        writer.value_matrix = value
        writer.write_table()

        out, err = capsys.readouterr()
        print_test_result(expected=expected, actual=out, error=err)

        assert out == expected
        assert writer.dumps() == expected

    def test_normal_style_list(self):
        writer = table_writer_class()
        writer.from_tabledata(style_tabledata)
        writer.style_list = style_list

        expected = r"""\begin{equation}
    style test = \left( \begin{array}{rrrrrrlr}
         111 &         111 & \tiny 111 & \small 111 &  \normalsize 111 &  \large 111 &              & \large \bf 111 \\
        1234 &        1234 & \tiny 1234 & \small 1234 & \normalsize 1,234 & \large 1 234 &              & \large \bf 1234 \\
    \end{array} \right)
\end{equation}
"""
        out = writer.dumps()
        print_test_result(expected=expected, actual=out)
        assert out == expected

        writer.style_list = [
            None,
            Style(align="auto"),
            Style(align="auto", font_size="tiny", thousand_separator=","),
            Style(align="left", font_size="small", thousand_separator=" "),
            Style(align="right", font_size="medium"),
            Style(align="center", font_size="large"),
            Style(font_size="large", font_weight="bold"),
        ]
        out = writer.dumps()
        expected = r"""\begin{equation}
    style test = \left( \begin{array}{rrrlrclr}
         111 &         111 &  \tiny 111 & \small 111  & \normalsize 111 & \large 111 &              &        111 \\
        1234 &        1234 & \tiny 1,234 & \small 1 234 & \normalsize 1234 & \large 1234 &              &       1234 \\
    \end{array} \right)
\end{equation}
"""
        print_test_result(expected=expected, actual=out)
        assert out == expected

    @pytest.mark.parametrize(
        ["header", "value", "expected"],
        [[data.header, data.value, data.expected] for data in exception_test_data_list],
    )
    def test_exception(self, header, value, expected):
        writer = table_writer_class()
        writer.header_list = header
        writer.value_matrix = value

        with pytest.raises(expected):
            writer.write_table()
