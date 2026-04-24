"""Tests for the reader modules."""

from pathlib import Path

import pytest
from pyarrow.lib import ArrowInvalid

from datanomy.reader.ipc import IPCReader
from datanomy.reader.parquet import ParquetReader


def test_reader_simple_file(simple_parquet: Path) -> None:
    """Test reader with a simple Parquet file."""
    reader = ParquetReader(simple_parquet)

    assert reader.file_path == simple_parquet
    assert reader.file_path.exists()

    assert reader.num_rows == 5
    assert reader.num_row_groups == 1
    assert len(reader.schema_arrow) == 4
    assert reader.file_size > 0

    metadata = reader.metadata
    assert metadata is not None
    assert metadata.num_rows == 5
    assert metadata.num_row_groups == 1


def test_reader_multi_row_groups(multi_row_group_parquet: Path) -> None:
    """Test reader with multiple row groups."""
    reader = ParquetReader(multi_row_group_parquet)

    assert reader.num_rows == 10000
    assert reader.num_row_groups == 5

    # Check each row group
    for i in range(reader.num_row_groups):
        rg = reader.get_row_group_info(i)
        assert rg.num_rows == 2000
        assert rg.total_byte_size > 0


def test_reader_empty_file(empty_parquet: Path) -> None:
    """Test reader with empty Parquet file."""
    reader = ParquetReader(empty_parquet)

    # file has schema but no rows
    assert reader.num_rows == 0
    assert reader.num_row_groups == 1
    assert len(reader.schema_arrow) == 2
    assert reader.file_size > 0


def test_reader_large_schema(large_schema_parquet: Path) -> None:
    """Test reader with many columns."""
    reader = ParquetReader(large_schema_parquet)

    assert reader.num_rows == 3
    assert len(reader.schema_arrow) == 50

    # Check all columns are named correctly
    field_names = [field.name for field in reader.schema_arrow]
    for i in range(50):
        assert f"col_{i}" in field_names


def test_reader_nonexistent_file(tmp_path: Path) -> None:
    """Test that ParquetReader raises FileNotFoundError for nonexistent files."""
    nonexistent = tmp_path / "nonexistent.parquet"

    with pytest.raises(FileNotFoundError, match="File not found"):
        ParquetReader(nonexistent)


def test_reader_invalid_parquet_file(invalid_parquet_file: Path) -> None:
    """Test that ParquetReader raises ArrowInvalid for non-Parquet files."""
    with pytest.raises(ArrowInvalid, match="does not appear to be a Parquet file"):
        ParquetReader(invalid_parquet_file)


def test_reader_accepts_file_without_parquet_extension(
    parquet_without_extension: Path,
) -> None:
    """Test that ParquetReader accepts valid Parquet files regardless of extension."""
    # Should successfully read the file
    reader = ParquetReader(parquet_without_extension)
    assert reader.num_rows == 3
    assert len(reader.schema_arrow) == 2


def test_row_group_total_sizes(simple_parquet: Path) -> None:
    """Test that row_group_total_sizes returns correct compressed and uncompressed sizes."""
    reader = ParquetReader(simple_parquet)

    row_group = reader.get_row_group(0)

    assert row_group.has_compression
    compressed_size, uncompressed_size = row_group.total_sizes
    assert compressed_size == 474
    assert uncompressed_size == 487


# --- IPCReader tests ---


def test_ipc_reader_simple_file(simple_ipc: Path) -> None:
    """Test reader with a simple Arrow IPC file."""
    reader = IPCReader(simple_ipc)

    assert reader.file_path == simple_ipc
    assert reader.num_rows == 5
    assert reader.num_record_batches == 1
    assert len(reader.schema_arrow) == 4
    assert reader.file_size > 0


def test_ipc_reader_multi_batches(multi_batch_ipc: Path) -> None:
    """Test reader with multiple record batches."""
    reader = IPCReader(multi_batch_ipc)

    assert reader.num_rows == 300
    assert reader.num_record_batches == 3

    for i in range(reader.num_record_batches):
        batch = reader.get_batch(i)
        assert batch.num_rows == 100


def test_ipc_reader_empty_file(empty_ipc: Path) -> None:
    """Test reader with empty Arrow IPC file."""
    reader = IPCReader(empty_ipc)

    assert reader.num_rows == 0
    assert reader.num_record_batches == 0
    assert len(reader.schema_arrow) == 2
    assert reader.file_size > 0


def test_ipc_reader_nonexistent_file(tmp_path: Path) -> None:
    """Test that IPCReader raises FileNotFoundError for nonexistent files."""
    nonexistent = tmp_path / "nonexistent.arrow"

    with pytest.raises(FileNotFoundError, match="File not found"):
        IPCReader(nonexistent)


def test_ipc_reader_invalid_file(invalid_ipc_file: Path) -> None:
    """Test that IPCReader raises ArrowInvalid for non-IPC files."""
    with pytest.raises(
        ArrowInvalid, match="does not appear to be a valid Arrow IPC file"
    ):
        IPCReader(invalid_ipc_file)


def test_ipc_reader_metadata(simple_ipc: Path) -> None:
    """Test that IPCReader can access schema metadata."""
    reader = IPCReader(simple_ipc)

    # Simple files without custom metadata should return None
    metadata = reader.metadata
    assert metadata is None or isinstance(metadata, dict)
