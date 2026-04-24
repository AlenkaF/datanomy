"""Shared test fixtures for datanomy tests."""

from pathlib import Path

import pyarrow as pa
import pyarrow.ipc as ipc
import pyarrow.parquet as pq
import pytest


@pytest.fixture
def simple_parquet(tmp_path: Path) -> Path:
    """Create a simple test Parquet file with basic types.

    Returns:
        Path to the created Parquet file
    """
    table = pa.table(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
            "age": [25, 30, 35, 40, 45],
            "score": [85.5, 90.0, 78.5, 92.0, 88.5],
        }
    )
    file_path = tmp_path / "simple.parquet"
    pq.write_table(table, file_path)
    return file_path


@pytest.fixture
def multi_row_group_parquet(tmp_path: Path) -> Path:
    """Create a Parquet file with multiple row groups.

    Returns:
        Path to the created Parquet file
    """
    # Create a larger table
    num_rows = 10000
    table = pa.table(
        {
            "id": range(num_rows),
            "value": [i * 2 for i in range(num_rows)],
            "category": [f"cat_{i % 10}" for i in range(num_rows)],
        }
    )
    file_path = tmp_path / "multi_row_group.parquet"
    # Write with small row group size to create multiple row groups
    pq.write_table(table, file_path, row_group_size=2000)
    return file_path


@pytest.fixture
def complex_schema_parquet(tmp_path: Path) -> Path:
    """Create a Parquet file with complex nested schema.

    Returns:
        Path to the created Parquet file
    """
    # Create a table with nested types
    table = pa.table(
        {
            "id": [1, 2, 3],
            "data": [
                {"x": 1, "y": 2},
                {"x": 3, "y": 4},
                {"x": 5, "y": 6},
            ],
            "tags": [["a", "b"], ["c"], ["d", "e", "f"]],
        }
    )
    file_path = tmp_path / "complex.parquet"
    pq.write_table(table, file_path)
    return file_path


@pytest.fixture
def empty_parquet(tmp_path: Path) -> Path:
    """Create an empty Parquet file (schema but no rows).

    Returns:
        Path to the created Parquet file
    """
    schema = pa.schema(
        [
            ("id", pa.int64()),
            ("name", pa.string()),
        ]
    )
    table = pa.table({"id": [], "name": []}, schema=schema)
    file_path = tmp_path / "empty.parquet"
    pq.write_table(table, file_path)
    return file_path


@pytest.fixture
def large_schema_parquet(tmp_path: Path) -> Path:
    """Create a Parquet file with many columns.

    Returns:
        Path to the created Parquet file
    """
    # Create 50 columns
    num_cols = 50
    data = {f"col_{i}": [i, i + 1, i + 2] for i in range(num_cols)}
    table = pa.table(data)
    file_path = tmp_path / "large_schema.parquet"
    pq.write_table(table, file_path)
    return file_path


@pytest.fixture
def parquet_without_extension(tmp_path: Path) -> Path:
    """Create a valid Parquet file without .parquet extension.

    Returns:
        Path to the created Parquet file
    """
    table = pa.table(
        {
            "id": [1, 2, 3],
            "name": ["a", "b", "c"],
        }
    )
    file_path = tmp_path / "data_file"
    pq.write_table(table, file_path)
    return file_path


@pytest.fixture
def invalid_parquet_file(tmp_path: Path) -> Path:
    """Create a file with invalid Parquet content.

    Returns:
        Path to the created invalid file
    """
    file_path = tmp_path / "not_a_parquet.dat"
    file_path.write_text("This is not a Parquet file")
    return file_path


# --- Arrow IPC fixtures ---


@pytest.fixture
def simple_ipc(tmp_path: Path) -> Path:
    """Create a simple test Arrow IPC file with basic types.

    Returns:
        Path to the created Arrow IPC file
    """
    table = pa.table(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
            "age": [25, 30, 35, 40, 45],
            "score": [85.5, 90.0, 78.5, 92.0, 88.5],
        }
    )
    file_path = tmp_path / "simple.arrow"
    with ipc.new_file(file_path, table.schema) as writer:
        writer.write_table(table)
    return file_path


@pytest.fixture
def multi_batch_ipc(tmp_path: Path) -> Path:
    """Create an Arrow IPC file with multiple record batches.

    Returns:
        Path to the created Arrow IPC file
    """
    schema = pa.schema(
        [
            ("id", pa.int64()),
            ("value", pa.int64()),
            ("category", pa.string()),
        ]
    )
    file_path = tmp_path / "multi_batch.arrow"
    with ipc.new_file(file_path, schema) as writer:
        for batch_idx in range(3):
            offset = batch_idx * 100
            batch = pa.record_batch(
                {
                    "id": list(range(offset, offset + 100)),
                    "value": [i * 2 for i in range(offset, offset + 100)],
                    "category": [f"cat_{i % 10}" for i in range(100)],
                },
                schema=schema,
            )
            writer.write_batch(batch)
    return file_path


@pytest.fixture
def empty_ipc(tmp_path: Path) -> Path:
    """Create an empty Arrow IPC file (schema but no rows).

    Returns:
        Path to the created Arrow IPC file
    """
    schema = pa.schema(
        [
            ("id", pa.int64()),
            ("name", pa.string()),
        ]
    )
    file_path = tmp_path / "empty.arrow"
    with ipc.new_file(file_path, schema):
        pass
    return file_path


@pytest.fixture
def invalid_ipc_file(tmp_path: Path) -> Path:
    """Create a file with invalid Arrow IPC content.

    Returns:
        Path to the created invalid file
    """
    file_path = tmp_path / "not_an_arrow.arrow"
    file_path.write_text("This is not an Arrow IPC file")
    return file_path
