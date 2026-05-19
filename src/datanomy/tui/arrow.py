"""Terminal UI tabs for exploring Arrow files."""

from typing import Any

from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import HorizontalScroll, Vertical
from textual.widgets import DataTable, Static

from datanomy.buffers import column_panel
from datanomy.reader.ipc import IPCReader
from datanomy.tui.common import create_column_grid
from datanomy.utils import format_size


class BaseArrowTab(Static):
    """Base class for Arrow tab widgets."""

    def __init__(self, reader: IPCReader) -> None:
        super().__init__()
        self.reader = reader

    def compose(self) -> ComposeResult:
        content_id = f"{self.__class__.__name__.lower().replace('tab', '')}-content"
        yield Static(self.render_tab_content(), id=content_id)

    def render_tab_content(self) -> Group:
        raise NotImplementedError("Subclasses must implement render_tab_content()")


class StructureTab(BaseArrowTab):
    """Widget displaying Arrow file structure."""

    def _header(self) -> Panel:
        header_text = Text()
        header_text.append("Magic Number: ARROW1\n", style="yellow")
        header_text.append("Size: 6 bytes")
        return Panel(header_text, title="Header", border_style="yellow")

    def _file_info(self) -> Text:
        file_size_str = format_size(self.reader.file_size)
        file_info = Text()
        file_info.append("File: ", style="bold")
        file_info.append(f"{self.reader.file_path.name}\n")
        file_info.append("Size: ", style="bold")
        file_info.append(file_size_str)
        return file_info

    def _record_batches(self) -> list[Panel]:
        panels: list[Panel] = []
        for i in range(self.reader.num_record_batches):
            batch = self.reader.get_batch(i)
            batch_text = Text()
            batch_text.append(f"Rows: {batch.num_rows:,}\n")
            batch_text.append(f"Columns: {batch.num_columns}\n")
            batch_text.append(f"Size: {format_size(batch.nbytes)}")
            panels.append(
                Panel(
                    batch_text,
                    title=f"[green]Record Batch {i}[/green]",
                    border_style="green",
                )
            )
        return panels

    def _footer(self) -> Panel:
        footer_text = Text()
        footer_text.append(f"Total Rows: {self.reader.num_rows:,}\n")
        footer_text.append(f"Record Batches: {self.reader.num_record_batches}\n")
        footer_text.append("Magic Number: ARROW1", style="yellow")
        footer_text.append(" (6 bytes)")
        return Panel(footer_text, title="[blue]Footer[/blue]", border_style="blue")

    def render_tab_content(self) -> Group:
        sections: list[Text | Panel] = [
            self._file_info(),
            Text(),
            self._header(),
            Text(),
        ]
        sections.extend(self._record_batches())
        sections.extend([Text(), self._footer()])
        return Group(*sections)


class SchemaTab(BaseArrowTab):
    """Widget displaying Arrow schema information."""

    def _schema_structure(self) -> Panel:
        schema = self.reader.schema_arrow
        schema_text = Text()
        for field in schema:
            nullable = "nullable" if field.nullable else "not null"
            schema_text.append(f"{field.name}: {field.type} ({nullable})\n", style="dim")
        return Panel(schema_text, title="[yellow]Arrow Schema[/yellow]", border_style="yellow")

    def _column_details(self) -> Panel:
        schema = self.reader.schema_arrow
        num_columns = len(schema)
        schema_table = create_column_grid(num_columns=3)

        cols_per_row = 3
        for row_idx in range(0, num_columns, cols_per_row):
            row_panels: list[Panel | Text] = []
            for col_offset in range(cols_per_row):
                col_idx = row_idx + col_offset
                if col_idx < num_columns:
                    field = schema.field(col_idx)
                    col_text = Text()
                    col_text.append("Type: ", style="bold")
                    col_text.append(f"{field.type}\n", style="yellow")
                    col_text.append("Nullable: ", style="bold")
                    col_text.append(f"{field.nullable}\n", style="dim")
                    if field.metadata:
                        col_text.append("Field metadata: ", style="bold")
                        col_text.append("Yes\n", style="dim")
                    row_panels.append(
                        Panel(
                            col_text,
                            title=f"[green]{field.name}[/green]",
                            border_style="cyan",
                            padding=(0, 1),
                        )
                    )
                else:
                    row_panels.append(Text(""))
            schema_table.add_row(*row_panels)

        return Panel(schema_table, title="[cyan]Column Details[/cyan]", border_style="cyan")

    def render_tab_content(self) -> Group:
        return Group(self._schema_structure(), Text(), self._column_details())


class DataTab(BaseArrowTab):
    """Widget displaying data preview."""

    def __init__(self, reader: IPCReader, num_rows: int = 50) -> None:
        super().__init__(reader)
        self.num_rows = num_rows
        self.id = "data-content"

    @staticmethod
    def _format_value(value: Any, max_length: int = 50) -> str:
        if value is None:
            return "NULL"
        value_str = str(value)
        if len(value_str) > max_length:
            return f"{value_str[: max_length - 3]}..."
        return value_str

    def _read_data(self) -> tuple[Any, int, int]:
        table = self.reader.ipc_file.read_all()
        if len(table) > self.num_rows:
            table = table.slice(0, self.num_rows)
        return table, len(table), self.reader.num_rows

    def _create_data_table(self, table: Any, num_rows_display: int) -> DataTable:
        data_table: DataTable = DataTable(id="data-preview-table", zebra_stripes=True)
        data_table.border_title = "Data Preview"
        data_table.styles.border = ("round", "cyan")
        data_table.styles.width = "auto"

        columns = list(table.schema.names)
        if not columns:
            return data_table

        min_width = max(80, sum(max(12, len(name) + 2) for name in columns))
        data_table.styles.min_width = min_width
        data_table.add_columns(*columns)

        for row_idx in range(num_rows_display):
            row_values: list[str | Text] = []
            for name in columns:
                value = table[name][row_idx].as_py()
                formatted_value = self._format_value(value)
                if value is None:
                    row_values.append(Text(formatted_value, style="dim yellow"))
                else:
                    row_values.append(formatted_value)
            data_table.add_row(*row_values)

        return data_table

    def compose(self) -> ComposeResult:
        try:
            table, num_rows_display, total_rows = self._read_data()
        except Exception as e:
            error_text = Text()
            error_text.append(f"Error reading data: {e}", style="red")
            yield Static(Panel(error_text, title="[red]Error[/red]"), id="data-content")
            return

        columns = list(table.schema.names)
        data_widget: DataTable | None = None
        empty_panel: Panel | None = None

        if columns:
            data_widget = self._create_data_table(table, num_rows_display)
        else:
            empty_panel = Panel(
                Text("Table has no columns", style="yellow"),
                title="[cyan]Data Preview[/cyan]",
                border_style="cyan",
            )

        header_text = Text()
        header_text.append(
            f"Showing {num_rows_display:,} of {total_rows:,} rows", style="cyan bold"
        )

        with Vertical(id="data-content"):
            yield Static(header_text)
            if data_widget is not None:
                with HorizontalScroll():
                    yield data_widget
            elif empty_panel is not None:
                yield Static(empty_panel)


class MetadataTab(BaseArrowTab):
    """Display Arrow file metadata."""

    def _file_info(self) -> Panel:
        file_info = Text()
        file_info.append("File size: ", style="bold")
        file_info.append(f"{format_size(self.reader.file_size)}\n", style="cyan")
        file_info.append("Total rows: ", style="bold")
        file_info.append(f"{self.reader.num_rows:,}\n", style="green")
        file_info.append("Total columns: ", style="bold")
        file_info.append(f"{len(self.reader.schema_arrow)}\n", style="green")
        file_info.append("Record batches: ", style="bold")
        file_info.append(f"{self.reader.num_record_batches}\n", style="green")
        return Panel(file_info, title="[cyan]File Information[/cyan]", border_style="cyan")

    def _custom_metadata(self) -> Panel:
        metadata = self.reader.metadata
        custom_metadata = Text()
        if metadata:
            for key, value in metadata.items():
                key_str = key.decode("utf-8") if isinstance(key, bytes) else key
                value_str = value.decode("utf-8") if isinstance(value, bytes) else value
                custom_metadata.append(f"{key_str}:\n", style="bold yellow")
                if len(value_str) > 200:
                    custom_metadata.append(f"  {value_str[:200]}...\n", style="dim white")
                    custom_metadata.append(
                        f"  (truncated, {len(value_str)} bytes total)\n",
                        style="italic magenta",
                    )
                else:
                    custom_metadata.append(f"  {value_str}\n", style="white")
                custom_metadata.append("\n")
        else:
            custom_metadata.append("No custom metadata found", style="dim yellow")
        return Panel(
            custom_metadata, title="[cyan]Custom Metadata[/cyan]", border_style="cyan"
        )

    def render_tab_content(self) -> Group:
        return Group(self._file_info(), Text(), self._custom_metadata())


class BuffersTab(BaseArrowTab):
    """Widget displaying buffer-level physical layout for each column."""

    def _batch_group(self, batch_idx: int) -> Group:
        schema = self.reader.schema_arrow
        batch = self.reader.get_batch(batch_idx)
        header = Text()
        header.append(f"Record Batch {batch_idx}", style="bold cyan")
        header.append(f"  ({batch.num_rows} rows)", style="dim")
        panels = [
            column_panel(schema.field(i).name, batch.column(i))
            for i in range(len(schema))
        ]
        return Group(header, Text(), *panels)

    def render_tab_content(self) -> Group:
        num_batches = self.reader.num_record_batches
        batches_to_show = min(num_batches, 2)

        note = Text()
        note.append(
            f"Showing first {batches_to_show} of {num_batches} batch(es), "
            "up to first 10 rows per column.",
            style="dim",
        )

        grid = create_column_grid(num_columns=batches_to_show)
        grid.add_row(*[self._batch_group(i) for i in range(batches_to_show)])

        return Group(note, Text(), grid)
