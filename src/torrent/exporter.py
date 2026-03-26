"""
Module for exporting torrent search results

Supports CSV export and magnet link files
"""

import csv
import logging
from pathlib import Path

from .models import TorrentSearchResult


logger = logging.getLogger(__name__)


class TorrentResultExporter:
    """Exporter for torrent search results"""
    
    def __init__(self, output_dir: Path | None = None):
        """
        Initialize exporter
        
        Args:
            output_dir: Directory for output files (default: ./torrent_output)
        """
        self.output_dir = output_dir or Path("./torrent_output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Torrent exporter initialized, output dir: {self.output_dir}")
    
    def export_to_csv(self, results: list[TorrentSearchResult],
                      filename: str = "torrent_search_results.csv") -> Path:
        """
        Export results to CSV

        Args:
            results: List of search results
            filename: Output filename

        Returns:
            Path to created file
        """
        filepath = self.output_dir / filename
        fieldnames = ["title", "source", "torrent_id", "magnet_link", "size",
                      "seeds", "leeches", "uploader", "upload_date", "category", "url"]

        # Use UTF-8 with BOM for proper Cyrillic support in Excel
        # Use semicolon delimiter for better compatibility
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', extrasaction='ignore')
            writer.writeheader()

            for result in results:
                writer.writerow(result.to_dict())

        logger.info(f"Exported {len(results)} results to {filepath}")
        return filepath
    
    def export_magnet_links(self, results: list[TorrentSearchResult],
                            magnet_links: dict[str, str],
                            filename: str = "magnet_links.txt") -> Path:
        """
        Export magnet links to text file
        
        Args:
            results: List of search results
            magnet_links: Dict mapping torrent_id to magnet link
            filename: Output filename
            
        Returns:
            Path to created file
        """
        filepath = self.output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            for result in results:
                magnet = magnet_links.get(result.torrent_id)
                if magnet:
                    f.write(f"{result.title}\n")
                    f.write(f"{magnet}\n\n")
        
        logger.info(f"Exported magnet links to {filepath}")
        return filepath
    
    def export_missing_tracks(
        self, 
        missing_tracks: list,
        search_results: dict[str, list[TorrentSearchResult]],
        filename_base: str = "missing_tracks"
    ) -> dict[str, Path]:
        """
        Export missing tracks with search results
        
        Args:
            missing_tracks: List of Track objects that are missing
            search_results: Dict mapping track key to search results
            filename_base: Base filename
            
        Returns:
            Dict with paths to created files
        """
        files = {}
        
        # Export summary CSV
        summary_data = []
        for track in missing_tracks:
            key = (track.title.lower(), track.artist.lower())
            results = search_results.get(key, [])
            
            summary_data.append({
                "title": track.title,
                "artist": track.artist,
                "album": track.album or "",
                "results_count": len(results),
                "top_result": results[0].title if results else "",
                "top_source": results[0].source.value if results else "",
                "top_seeds": results[0].seeds if results else ""
            })
        
        summary_path = self.output_dir / f"{filename_base}_summary.csv"
        # Use UTF-8 with BOM for proper Cyrillic support in Excel
        # Use semicolon delimiter for better compatibility
        with open(summary_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "artist", "album",
                                                    "results_count", "top_result",
                                                    "top_source", "top_seeds"],
                                    delimiter=';')
            writer.writeheader()
            writer.writerows(summary_data)
        
        files["summary"] = summary_path
        
        # Export magnet links
        all_magnets = {}
        all_results = []
        for results in search_results.values():
            all_results.extend(results)
        
        # Get magnet links (this would need search engine)
        # For now, export without magnets
        
        magnet_path = self.export_magnet_links(
            all_results, 
            {},  # Would need to fetch magnets
            f"{filename_base}_magnets.txt"
        )
        files["magnets"] = magnet_path
        
        return files
    
    def print_summary(self, results: list[TorrentSearchResult]) -> None:
        """Print search summary to console"""
        print("\n" + "=" * 60)
        print("TORRENT SEARCH RESULTS")
        print("=" * 60)
        
        # Group by source
        by_source = {}
        for result in results:
            source = result.source.value
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(result)
        
        for source, source_results in by_source.items():
            print(f"\n{source.upper()} ({len(source_results)} results):")
            print("-" * 40)
            for result in source_results[:5]:
                seeds = f"🌱 {result.seeds}" if result.seeds else ""
                size = f"💾 {result.size}" if result.size else ""
                print(f"  • {result.artist} - {result.title} {seeds} {size}")
            if len(source_results) > 5:
                print(f"  ... and {len(source_results) - 5} more")
        
        print("\n" + "=" * 60)
        print(f"Results saved to: {self.output_dir.absolute()}")
        print("=" * 60 + "\n")
