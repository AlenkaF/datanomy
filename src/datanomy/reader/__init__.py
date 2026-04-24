"""Reader factory with format auto-detection."""

from pathlib import Path

from datanomy.reader.ipc import IPCReader
from datanomy.reader.parquet import ParquetReader

PARQUET_EXTENSIONS = {".parquet", ".parq"}
IPC_EXTENSIONS = {".arrow", ".feather", ".ipc"}

PARQUET_MAGIC = b"PAR1"
IPC_MAGIC = b"ARROW1"


def create_reader(file_path: Path) -> ParquetReader | IPCReader:
    """
    Create the appropriate reader based on file format.

    Detection strategy:
        1. File extension if recognized
        2. Magic bytes fallback for unknown extensions

    Parameters
    ----------
        file_path: Path to the file to inspect

    Returns
    -------
        ParquetReader or IPCReader

    Raises
    ------
        FileNotFoundError: If the file does not exist
        ValueError: If the file format cannot be determined
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = file_path.suffix.lower()

    if suffix in PARQUET_EXTENSIONS:
        return ParquetReader(file_path)

    if suffix in IPC_EXTENSIONS:
        return IPCReader(file_path)

    # Unknown extension — try magic bytes
    with open(file_path, "rb") as f:
        header = f.read(6)

    if header[:4] == PARQUET_MAGIC:
        return ParquetReader(file_path)

    if header == IPC_MAGIC:
        return IPCReader(file_path)

    raise ValueError(
        f"Cannot determine file format for {file_path}. "
        f"Supported formats: Parquet ({', '.join(PARQUET_EXTENSIONS)}), "
        f"Arrow IPC ({', '.join(IPC_EXTENSIONS)})"
    )
