"""CLI entry point for datanomy."""

import sys
from pathlib import Path

import click

from datanomy.reader import create_reader
from datanomy.tui.tui import DatanomyApp


@click.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
def main(file: Path) -> None:
    """
    Explore the anatomy of your data files.

    Parameters
    ----------
        file: Path to a Parquet or Arrow IPC file to inspect
    """
    try:
        reader = create_reader(file)
        app = DatanomyApp(reader)
        app.run()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
