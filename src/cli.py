"""
Main CLI entry point for MP3 Library Comparator

Compares local MP3 library with zvuk.com collection
Optionally searches for missing tracks on torrent trackers
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
from .torrent.search_engine import TorrentSearchEngine
from .torrent.exporter import TorrentResultExporter
from .torrent.qbittorrent_client import QBittorrentClient
from .torrent.models import TorrentSource


def setup_logging(verbose: bool = False) -> None:
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress console output except errors")
@click.pass_context
def cli(ctx, verbose: bool, quiet: bool):
    """MP3 Library Comparator - Compare and enhance your music collection"""
    if quiet:
        logging.basicConfig(level=logging.CRITICAL)
    else:
        setup_logging(verbose)
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet


@cli.command()
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
    "--test-connection",
    is_flag=True,
    help="Test API connection and exit"
)
@click.pass_context
def compare(ctx, token: str, library_path: str, output: str | None, test_connection: bool) -> int:
    """Compare local MP3 library with zvuk.com collection"""
    verbose = ctx.obj.get('verbose', False)
    quiet = ctx.obj.get('quiet', False)
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
            click.echo()

        # Export results
        output_dir = Path(output) if output else None
        exporter = ResultExporter(diff, output_dir)
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


@cli.command()
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
    help="Output directory for search results"
)
@click.option(
    "--sources", "-s",
    type=click.Choice(['rutracker', '1337x', 'nnmclub'], case_sensitive=False),
    multiple=True,
    default=['rutracker', '1337x', 'nnmclub'],
    help="Torrent sources to search"
)
@click.option(
    "--rutracker-login",
    type=str,
    default=None,
    help="RuTracker login (optional)"
)
@click.option(
    "--rutracker-password",
    type=str,
    default=None,
    help="RuTracker password (optional)"
)
@click.option(
    "--limit",
    type=int,
    default=5,
    help="Max results per track"
)
@click.pass_context
def search_missing(ctx, token: str, library_path: str, output: str | None,
                   sources: tuple[str], rutracker_login: str | None,
                   rutracker_password: str | None, limit: int) -> int:
    """Search for missing tracks on torrent trackers"""
    verbose = ctx.obj.get('verbose', False)
    quiet = ctx.obj.get('quiet', False)
    logger = logging.getLogger(__name__)

    try:
        # First, compare libraries to find missing tracks
        click.echo("Step 1: Comparing libraries to find missing tracks...")
        cfg = Config(token=token, library_path=library_path)
        
        scanner = LocalLibraryScanner(cfg.library_path)
        local_tracks = scanner.scan()
        click.echo(f"Found {len(local_tracks)} local tracks")

        api_client = ZvukAPIClient(cfg)
        click.echo("Fetching zvuk.com collection...")
        zvuk_tracks = api_client.get_library()
        click.echo(f"Found {len(zvuk_tracks)} tracks in zvuk.com")

        comparator = LibraryComparator(local_tracks, zvuk_tracks)
        diff = comparator.compare()

        click.echo(f"\nFound {len(diff.only_local)} tracks missing from zvuk.com")
        
        if not diff.only_local:
            click.echo("🎉 All local tracks are in zvuk.com collection!")
            return 0

        # Initialize torrent search engine
        click.echo("\nStep 2: Searching torrent trackers...")
        
        # Parse sources
        source_enums = []
        for s in sources:
            if s == 'rutracker':
                source_enums.append(TorrentSource.RUTRACKER)
            elif s == '1337x':
                source_enums.append(TorrentSource.THIRTEEN_X)
            elif s == 'nnmclub':
                source_enums.append(TorrentSource.NNMCLUB)

        search_engine = TorrentSearchEngine(
            rutracker_login=rutracker_login,
            rutracker_password=rutracker_password,
            sources=source_enums
        )

        # Search for each missing track
        all_results = []
        track_results = {}
        
        for i, track in enumerate(diff.only_local):
            if not quiet:
                click.echo(f"[{i+1}/{len(diff.only_local)}] Searching: {track.artist} - {track.title}")
            
            results = search_engine.search_track(
                artist=track.artist,
                title=track.title,
                album=track.album,
                year=track.year,
                limit=limit
            )
            
            if results:
                key = (track.title.lower(), track.artist.lower())
                track_results[key] = results
                all_results.extend(results)

        # Export results
        output_dir = Path(output) if output else None
        exporter = TorrentResultExporter(output_dir)
        
        # Export to CSV
        csv_path = exporter.export_to_csv(all_results)
        click.echo(f"\nExported results to: {csv_path}")

        # Export missing tracks summary
        if track_results:
            summary_files = exporter.export_missing_tracks(
                diff.only_local,
                track_results
            )
            click.echo(f"Exported summary to: {summary_files['summary']}")
            click.echo(f"Exported magnet links to: {summary_files['magnets']}")

        # Print summary
        if not quiet:
            exporter.print_summary(all_results)

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


@cli.command()
@click.option(
    "--magnet", "-m",
    type=str,
    required=True,
    help="Magnet link or torrent URL"
)
@click.option(
    "--save-path", "-p",
    type=str,
    default=None,
    help="Download path"
)
@click.option(
    "--host",
    type=str,
    default="localhost",
    help="qBittorrent host"
)
@click.option(
    "--port",
    type=int,
    default=8080,
    help="qBittorrent Web UI port"
)
@click.option(
    "--username",
    type=str,
    default=None,
    help="qBittorrent Web UI username"
)
@click.option(
    "--password",
    type=str,
    default=None,
    help="qBittorrent Web UI password"
)
@click.pass_context
def add_torrent(ctx, magnet: str, save_path: str | None, host: str, port: int,
                username: str | None, password: str | None) -> int:
    """Add torrent to qBittorrent"""
    try:
        client = QBittorrentClient(
            host=host,
            port=port,
            username=username,
            password=password
        )

        if not client.is_connected():
            click.echo("✗ Failed to connect to qBittorrent", err=True)
            return 1

        if magnet.startswith("magnet:") or magnet.startswith("http"):
            success = client.add_torrent(magnet, save_path)
        else:
            success = client.add_torrent_file(magnet, save_path)

        if success:
            click.echo("✓ Torrent added successfully!")
            return 0
        else:
            click.echo("✗ Failed to add torrent", err=True)
            return 1

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1


def main() -> int:
    """Main entry point"""
    return cli(obj={})


if __name__ == "__main__":
    sys.exit(main())
