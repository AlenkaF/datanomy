"""Arrow IPC file reader."""

from pathlib import Path
from typing import Any

import functools
import pyarrow as pa
import pyarrow.ipc as ipc


class IPCReader:
    """Main class to read and inspect Arrow IPC files."""

    def __init__(self, file_path: Path) -> None:
        """
        Initialize the RecordBatchFileReader for Arrow file format.

        Parameters
        ----------
            file_path: Path to the Arrow IPC file

        Raises
        ------
            FileNotFoundError: If the file does not exist
            ArrowInvalid: If the file is not a valid Arrow IPC file
            ArrowIOError: If the file cannot be read
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            self.file_path = file_path
            self.ipc_file = ipc.open_file(file_path)
        except pa.ArrowInvalid as e:
            raise pa.ArrowInvalid(
                f"{file_path} does not appear to be a valid Arrow IPC file"
            ) from e
        except pa.ArrowIOError as e:
            raise pa.ArrowIOError(f"{file_path} could not be read") from e

    @property
    def schema_arrow(self) -> Any:
        """
        Get the Arrow schema.

        Returns
        -------
            Arrow schema for the Arrow IPC file
        """
        return self.ipc_file.schema

    @property
    def metadata(self) -> Any:
        """
        Get schema-level metadata.

        Returns
        -------
            Dictionary of key-value pairs
        """
        return self.ipc_file.schema.metadata

    @property
    def num_record_batches(self) -> int:
        """
        Get total number of batches.

        Returns
        -------
            Total number of batches in the Arrow IPC file
        """
        return int(self.ipc_file.num_record_batches)

    @functools.cached_property
    def num_rows(self) -> int:
        """
        Get total number of rows.

        Returns
        -------
            Total number of rows in the Arrow IPC file
        """
        return sum(
            self.ipc_file.get_batch(i).num_rows for i in range(self.num_record_batches)
        )

    @property
    def file_size(self) -> int:
        """
        Get file size in bytes.

        Returns
        -------
            File size in bytes
        """
        return int(self.file_path.stat().st_size)

    def get_batch(self, index: int) -> pa.RecordBatch:
        """
        Get a specific record batch.

        Parameters
        ----------
            index: Record batch index

        Returns
        -------
            RecordBatch
        """
        return self.ipc_file.get_batch(index)
