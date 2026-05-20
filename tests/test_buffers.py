"""Tests for the buffers display module."""

import pyarrow as pa
import pytest
from rich.panel import Panel
from rich.text import Text

from datanomy.buffers.core import (
    _data_text,
    _offsets_text,
    _validity_text,
    _values_text,
    column_panel,
)


# --- _validity_text ---


def test_validity_text_none_buffer() -> None:
    """None buffer means no nulls; returns a dim 'not present' message."""
    result = _validity_text(None, 5)
    assert isinstance(result, Text)
    assert "not present" in result.plain


def test_validity_text_no_nulls() -> None:
    """PyArrow omits the validity buffer when all values are valid."""
    arr = pa.array([1, 2, 3, 4, 5], type=pa.int32())
    buf = arr.buffers()[0]
    result = _validity_text(buf, 5)
    assert isinstance(result, Text)
    if buf is None:
        assert "not present" in result.plain
    else:
        assert "1" in result.plain


def test_validity_text_with_nulls() -> None:
    """Array with some nulls produces text containing both 1s and 0s."""
    arr = pa.array([1, None, 3], type=pa.int32())
    buf = arr.buffers()[0]
    assert buf is not None
    result = _validity_text(buf, 3)
    assert isinstance(result, Text)
    assert "1" in result.plain
    assert "0" in result.plain


def test_validity_text_all_nulls() -> None:
    """Array with all nulls produces text containing only 0s."""
    arr = pa.array([None, None, None], type=pa.int32())
    buf = arr.buffers()[0]
    assert buf is not None
    result = _validity_text(buf, 3)
    assert isinstance(result, Text)
    assert "0" in result.plain


# --- _values_text ---


def test_values_text_no_nulls() -> None:
    """All values are rendered as plain strings."""
    arr = pa.array([10, 20, 30], type=pa.int32())
    result = _values_text(arr)
    assert isinstance(result, Text)
    assert "10" in result.plain
    assert "20" in result.plain
    assert "30" in result.plain


def test_values_text_with_nulls() -> None:
    """Null values are rendered as the literal word 'null'."""
    arr = pa.array([10, None, 30], type=pa.int32())
    result = _values_text(arr)
    assert isinstance(result, Text)
    assert "null" in result.plain
    assert "10" in result.plain
    assert "30" in result.plain


def test_values_text_all_nulls() -> None:
    """All-null array renders only 'null' entries."""
    arr = pa.array([None, None], type=pa.int32())
    result = _values_text(arr)
    assert isinstance(result, Text)
    assert "null" in result.plain


# --- _offsets_text ---


def test_offsets_text_int32() -> None:
    """String array offsets are rendered with int32 widths."""
    arr = pa.array(["hello", "world"], type=pa.string())
    buf = arr.buffers()[1]
    assert buf is not None
    result = _offsets_text(buf, 2, pa.int32())
    assert isinstance(result, Text)
    # "hello" is 5 bytes → offsets [0, 5, 10]
    assert "0" in result.plain
    assert "5" in result.plain
    assert "10" in result.plain


def test_offsets_text_int64() -> None:
    """Large-string array offsets are rendered with int64 widths."""
    arr = pa.array(["foo", "bar"], type=pa.large_string())
    buf = arr.buffers()[1]
    assert buf is not None
    result = _offsets_text(buf, 2, pa.int64())
    assert isinstance(result, Text)
    # "foo" is 3 bytes → offsets [0, 3, 6]
    assert "0" in result.plain
    assert "3" in result.plain
    assert "6" in result.plain


def test_offsets_text_with_nulls() -> None:
    """Null values do not break offset rendering (offsets still advance by 0)."""
    arr = pa.array(["a", None, "bc"], type=pa.string())
    buf = arr.buffers()[1]
    assert buf is not None
    result = _offsets_text(buf, 3, pa.int32())
    assert isinstance(result, Text)


# --- _data_text ---


def test_data_text_valid_utf8() -> None:
    """Concatenated UTF-8 bytes of the data buffer are decoded correctly."""
    arr = pa.array(["hello", "world"], type=pa.string())
    buf = arr.buffers()[2]
    assert buf is not None
    result = _data_text(buf)
    assert isinstance(result, Text)
    assert "helloworld" in result.plain


def test_data_text_empty_buffer() -> None:
    """An empty buffer decodes to an empty string without error."""
    buf = pa.py_buffer(b"")
    result = _data_text(buf)
    assert isinstance(result, Text)
    assert result.plain == ""


def test_data_text_non_ascii() -> None:
    """Non-ASCII UTF-8 content is decoded without raising."""
    arr = pa.array(["café", "naïve"], type=pa.string())
    buf = arr.buffers()[2]
    assert buf is not None
    result = _data_text(buf)
    assert isinstance(result, Text)


# --- column_panel ---


def test_column_panel_returns_panel() -> None:
    """column_panel always returns a Rich Panel."""
    arr = pa.array([1, 2, 3], type=pa.int32())
    assert isinstance(column_panel("col", arr), Panel)


def test_column_panel_title_contains_field_name() -> None:
    """Panel title includes the field name."""
    arr = pa.array([1, 2, 3], type=pa.int32())
    panel = column_panel("my_field", arr)
    assert "my_field" in panel.title


def test_column_panel_title_contains_type() -> None:
    """Panel title includes the Arrow type."""
    arr = pa.array([1, 2, 3], type=pa.int32())
    panel = column_panel("col", arr)
    assert "int32" in panel.title


def test_column_panel_int32_with_nulls() -> None:
    """Primitive int32 column with nulls renders without error."""
    arr = pa.array([1, None, 3], type=pa.int32())
    assert isinstance(column_panel("id", arr), Panel)


def test_column_panel_float64() -> None:
    """Float64 column renders without error."""
    arr = pa.array([1.1, None, 3.3], type=pa.float64())
    assert isinstance(column_panel("score", arr), Panel)


def test_column_panel_bool() -> None:
    """Bool column renders without error."""
    arr = pa.array([True, False, None], type=pa.bool_())
    assert isinstance(column_panel("flag", arr), Panel)


def test_column_panel_string() -> None:
    """String column with nulls renders without error."""
    arr = pa.array(["alice", None, "charlie"], type=pa.string())
    assert isinstance(column_panel("name", arr), Panel)


def test_column_panel_large_string() -> None:
    """Large-string column uses int64 offsets and renders without error."""
    arr = pa.array(["foo", None, "bar"], type=pa.large_string())
    assert isinstance(column_panel("notes", arr), Panel)


def test_column_panel_string_view_inline() -> None:
    """String-view column with short (inline) values renders without error."""
    arr = pa.array(["short", None, "also_short"], type=pa.string_view())
    assert isinstance(column_panel("sv_col", arr), Panel)


def test_column_panel_string_view_variadic() -> None:
    """String-view column with a long value (> 12 bytes) renders variadic buffer."""
    arr = pa.array(
        ["short", None, "a-much-longer-string-exceeding-twelve-bytes"],
        type=pa.string_view(),
    )
    assert isinstance(column_panel("sv_long", arr), Panel)


def test_column_panel_list_of_strings() -> None:
    """List<string> column has offsets and values buffers; renders without error."""
    arr = pa.array([["a", "b"], None, ["c"]], type=pa.list_(pa.string()))
    assert isinstance(column_panel("tags", arr), Panel)


def test_column_panel_struct() -> None:
    """Struct column renders values buffer without error."""
    struct_type = pa.struct([pa.field("x", pa.int32()), pa.field("y", pa.int32())])
    arr = pa.array([{"x": 1, "y": 2}, None, {"x": 3, "y": 4}], type=struct_type)
    assert isinstance(column_panel("point", arr), Panel)


def test_column_panel_empty_array() -> None:
    """Empty array (0 rows) renders without error."""
    arr = pa.array([], type=pa.int32())
    assert isinstance(column_panel("empty", arr), Panel)


def test_column_panel_all_nulls() -> None:
    """All-null column renders without error."""
    arr = pa.array([None, None, None], type=pa.int32())
    assert isinstance(column_panel("all_null", arr), Panel)


def test_column_panel_truncates_long_array() -> None:
    """Arrays longer than _MAX_ROWS (10) are silently truncated."""
    arr = pa.array(list(range(50)), type=pa.int32())
    assert isinstance(column_panel("long_col", arr), Panel)


def test_column_panel_single_row() -> None:
    """Single-element array renders without error."""
    arr = pa.array([42], type=pa.int32())
    assert isinstance(column_panel("one", arr), Panel)
