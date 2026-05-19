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
    t = Text()
    for i, v in enumerate(array.to_pylist()):
        if i > 0:
            t.append("  ")
        t.append("null", style="dim") if v is None else t.append(str(v))
    return t


def _offsets_text(buf: pa.Buffer, num_rows: int, offset_type: pa.DataType) -> Text:
    arr = pa.Array.from_buffers(offset_type, num_rows + 1, [None, buf])
    t = Text()
    for i, v in enumerate(arr.to_pylist()):
        if i > 0:
            t.append("  ")
        t.append(str(v))
    return t


def _data_text(buf: pa.Buffer) -> Text:
    return Text(bytes(memoryview(buf)).decode("utf-8", errors="replace"))


def _buffer_items(name: str, content: Text) -> list:
    """Return a label + compact box pair for one buffer."""
    label = Text(name, style=_title_color(name))
    box = Panel(content, border_style="white", expand=False, padding=(0, 1))
    return [label, box, Text()]


def column_panel(field_name: str, array: pa.Array) -> Panel:
    """Render a column's buffer layout as a Rich Panel."""
    t = array.type
    n = min(len(array), _MAX_ROWS)
    array = array.slice(0, n)
    buffers = array.buffers()
    items: list = _buffer_items("Validity buffer", _validity_text(buffers[0], n))

    if pa.types.is_string(t) or pa.types.is_binary(t):
        items += _buffer_items("Offsets buffer", _offsets_text(buffers[1], n, pa.int32()))
        if buffers[2] is not None:
            items += _buffer_items("Data buffer", _data_text(buffers[2]))

    elif pa.types.is_large_string(t) or pa.types.is_large_binary(t):
        items += _buffer_items("Offsets buffer", _offsets_text(buffers[1], n, pa.int64()))
        if buffers[2] is not None:
            items += _buffer_items("Data buffer", _data_text(buffers[2]))

    elif pa.types.is_list(t):
        items += _buffer_items("Offsets buffer", _offsets_text(buffers[1], n, pa.int32()))
        child_n = array.offsets[n].as_py()
        items += _buffer_items("Values buffer", _values_text(array.values.slice(0, child_n)))

    elif pa.types.is_large_list(t):
        items += _buffer_items("Offsets buffer", _offsets_text(buffers[1], n, pa.int64()))
        child_n = array.offsets[n].as_py()
        items += _buffer_items("Values buffer", _values_text(array.values.slice(0, child_n)))

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
