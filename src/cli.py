"""
Main CLI entry point for MP3 Library Comparator

Compares local MP3 library with zvuk.com collection
"""

import logging
import sys
from pathlib import Path

import click

from .config import Config
from .local_scanner import LocalLibraryScanner
from .zvuk_api import ZvukAPIClient
from .comparator import LibraryComparator
from .exporter import ResultExporter


def setup_logging(verbose: bool = False) -> None:
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )


@click.command()
@click.option(
    "--token", "-t",
    type=str,
    required=True,
    help="Zvuk.com API token (required)"
)
@click.option(
    "--library-path", "-l",
    type=click.Path(exists=True),
    required=True,
    help="Path to local MP3 library (required)"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default=None,
    help="Output directory for CSV files"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose output"
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Suppress console output except errors"
)
@click.option(
    "--test-connection",
    is_flag=True,
    help="Test API connection and exit"
)
def main(
    token: str,
    library_path: str,
    output: str | None,
    verbose: bool,
    quiet: bool,
    test_connection: bool
) -> int:
    """
    Compare your local MP3 library with zvuk.com collection.

    Results are exported to CSV files showing:
    - Tracks only in local library
    - Tracks only in zvuk.com
    - Tracks present in both
    """
    # Setup logging
    if quiet:
        logging.basicConfig(level=logging.CRITICAL)
    else:
        setup_logging(verbose)

    logger = logging.getLogger(__name__)

    try:
        # Initialize configuration
        cfg = Config(token=token, library_path=library_path)

        # Initialize API client
        api_client = ZvukAPIClient(cfg)

        # Test connection if requested
        if test_connection:
            click.echo("Testing connection to zvuk.com API...")
            if api_client.test_connection():
                click.echo("✓ Connection successful!")
                return 0
            else:
                click.echo("✗ Connection failed!", err=True)
                return 1

        # Scan local library
        click.echo(f"Scanning local library: {cfg.library_path}")
        scanner = LocalLibraryScanner(cfg.library_path)
        local_tracks = scanner.scan()
        click.echo(f"Found {len(local_tracks)} local tracks")

        # Get zvuk.com library
        click.echo("Fetching collection from zvuk.com...")
        zvuk_tracks = api_client.get_library()
        click.echo(f"Found {len(zvuk_tracks)} tracks in zvuk.com collection")

        # Compare libraries
        click.echo("Comparing libraries...")

        def progress_cb(current: int, total: int) -> None:
            if not quiet and total > 0:
                percent = (current / total) * 100
                click.echo(f"\rProgress: {percent:.1f}%", nl=False)

        comparator = LibraryComparator(
            local_tracks,
            zvuk_tracks,
            progress_callback=progress_cb if verbose else None
        )
        diff = comparator.compare()

        if not quiet:
            click.echo()  # New line after progress

        # Export results
        output_dir = Path(output) if output else None
        exporter = ResultExporter(diff, output_dir)
        
        # Export to CSV
        exporter.export_csv()

        if not quiet:
            exporter.print_detailed()
        else:
            exporter.print_summary()

        return 0

    except ValueError as e:
        click.echo(f"Configuration error: {e}", err=True)
        return 1
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user")
        return 130
    except Exception as e:
        logger.exception("Unexpected error")
        click.echo(f"Error: {e}", err=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
