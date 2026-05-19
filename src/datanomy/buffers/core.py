"""Arrow buffer display using PyArrow buffers."""

from __future__ import annotations

import math

import pyarrow as pa
from rich.console import Group
from rich.panel import Panel
from rich.text import Text

_MAX_ROWS = 10


def _title_color(name: str) -> str:
    return "orange1"


def _validity_text(buf: pa.Buffer | None, num_rows: int) -> Text:
    """
    Render a validity bitmap buffer as colored bit text.

    Parameters
    ----------
        buf: Validity bitmap buffer, or None if not allocated
        num_rows: Number of array elements to unpack

    Returns
    -------
        Text: Rich Text with white 1s and violet 0s, or a dim not-present message
    """
    if buf is None or len(memoryview(buf)) == 0:
        return Text("not present (no nulls)", style="dim")
    bits = []
    for byte in memoryview(buf)[: math.ceil(num_rows / 8)]:
        for bit_pos in range(8):
            bits.append((byte >> bit_pos) & 1)
    t = Text()
    for b in bits[:num_rows]:
        t.append("1 ", style="white") if b else t.append("0 ", style="violet")
    return t


def _values_text(array: pa.Array) -> Text:
    """
    Render array values as space-separated text with dim nulls.

    Parameters
    ----------
        array: PyArrow array to render

    Returns
    -------
        Text: Rich Text with values separated by two spaces
    """
    t = Text()
    for i, v in enumerate(array.to_pylist()):
        if i > 0:
            t.append("  ")
        t.append("null", style="dim") if v is None else t.append(str(v))
    return t


def _offsets_text(buf: pa.Buffer, num_rows: int, offset_type: pa.DataType) -> Text:
    """
    Render an offsets buffer as space-separated integer text.

    Parameters
    ----------
        buf: Raw offsets buffer
        num_rows: Number of array elements (offsets array has num_rows + 1 entries)
        offset_type: PyArrow integer type for the offsets (int32 or int64)

    Returns
    -------
        Text: Rich Text with offset values separated by two spaces
    """
    arr = pa.Array.from_buffers(offset_type, num_rows + 1, [None, buf])
    t = Text()
    for i, v in enumerate(arr.to_pylist()):
        if i > 0:
            t.append("  ")
        t.append(str(v))
    return t


def _data_text(buf: pa.Buffer) -> Text:
    """
    Decode a raw data buffer as UTF-8 text.

    Parameters
    ----------
        buf: Raw data buffer containing UTF-8 bytes

    Returns
    -------
        Text: Rich Text with the decoded string content
    """
    return Text(bytes(memoryview(buf)).decode("utf-8", errors="replace"))


def _buffer_items(name: str, content: Text) -> list:
    """
    Return an orange label and a compact white-bordered box for one buffer.

    Parameters
    ----------
        name: Buffer name shown as the label above the box
        content: Rich Text content to display inside the box

    Returns
    -------
        list: [Text label, Panel box, Text spacer]
    """
    label = Text(name, style=_title_color(name))
    box = Panel(content, border_style="white", expand=False, padding=(0, 1))
    return [label, box, Text()]


def column_panel(field_name: str, array: pa.Array) -> Panel:
    """
    Render a column's buffer layout as a Rich Panel.

    Parameters
    ----------
        field_name: Column name shown in the panel title
        array: PyArrow array whose buffers are displayed

    Returns
    -------
        Panel: Rich Panel containing labeled buffer boxes for the column
    """
    t = array.type
    n = min(len(array), _MAX_ROWS)
    array = array.slice(0, n)
    buffers = array.buffers()
    items: list = _buffer_items("Validity buffer", _validity_text(buffers[0], n))

    if pa.types.is_string(t) or pa.types.is_binary(t):
        items += _buffer_items(
            "Offsets buffer", _offsets_text(buffers[1], n, pa.int32())
        )
        if buffers[2] is not None:
            items += _buffer_items("Data buffer", _data_text(buffers[2]))

    elif pa.types.is_large_string(t) or pa.types.is_large_binary(t):
        items += _buffer_items(
            "Offsets buffer", _offsets_text(buffers[1], n, pa.int64())
        )
        if buffers[2] is not None:
            items += _buffer_items("Data buffer", _data_text(buffers[2]))

    elif pa.types.is_list(t):
        items += _buffer_items(
            "Offsets buffer", _offsets_text(buffers[1], n, pa.int32())
        )
        child_n = array.offsets[n].as_py()
        items += _buffer_items(
            "Values buffer", _values_text(array.values.slice(0, child_n))
        )

    elif pa.types.is_large_list(t):
        items += _buffer_items(
            "Offsets buffer", _offsets_text(buffers[1], n, pa.int64())
        )
        child_n = array.offsets[n].as_py()
        items += _buffer_items(
            "Values buffer", _values_text(array.values.slice(0, child_n))
        )

    elif pa.types.is_string_view(t) or pa.types.is_binary_view(t):
        items += _buffer_items("Views buffer", _values_text(array))
        for i, buf in enumerate(buffers[2:]):
            if buf is not None:
                items += _buffer_items(f"Variadic data buffer [{i}]", _data_text(buf))

    elif pa.types.is_struct(t) or pa.types.is_fixed_size_list(t) or pa.types.is_map(t):
        items += _buffer_items("Values buffer", _values_text(array))

    else:
        if len(buffers) > 1 and buffers[1] is not None:
            items += _buffer_items("Values buffer", _values_text(array))

    return Panel(
        Group(*items),
        title=f"[green]{field_name}[/green]  [dim]{t}[/dim]",
        border_style="cyan",
        padding=(0, 1),
    )
