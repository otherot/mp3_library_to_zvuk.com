"""
Module for exporting comparison results

Supports console output and CSV export
"""

import csv
import logging
from pathlib import Path
from typing import TextIO

from .models import LibraryDiff


logger = logging.getLogger(__name__)


class ResultExporter:
    """Exporter for comparison results"""
    
    def __init__(self, diff: LibraryDiff, output_dir: Path | None = None):
        """
        Initialize exporter
        
        Args:
            diff: Comparison results
            output_dir: Directory for output files (default: ./output)
        """
        self.diff = diff
        self.output_dir = output_dir or Path("./output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Exporter initialized, output dir: {self.output_dir}")
    
    def export_all(self, filename_base: str = "comparison_result") -> dict[str, Path]:
        """
        Export results to all formats
        
        Args:
            filename_base: Base filename without extension
            
        Returns:
            Dictionary with paths to created files
        """
        files = {}
        
        csv_path = self.export_csv(filename_base)
        files["csv"] = csv_path
        
        logger.info(f"Exported results to {len(files)} file(s)")
        return files
    
    def export_csv(self, filename_base: str = "comparison_result") -> Path:
        """
        Export results to CSV file
        
        Creates three separate files:
        - {filename_base}_only_local.csv
        - {filename_base}_only_zvuk.csv
        - {filename_base}_match.csv
        
        Args:
            filename_base: Base filename
            
        Returns:
            Path to the directory containing CSV files
        """
        logger.info("Exporting results to CSV")
        
        self._write_csv_file(f"{filename_base}_only_local.csv", self.diff.only_local)
        self._write_csv_file(f"{filename_base}_only_zvuk.csv", self.diff.only_zvuk)
        self._write_csv_file(f"{filename_base}_match.csv", self.diff.match)
        
        return self.output_dir
    
    def _write_csv_file(self, filename: str, tracks: list) -> None:
        """
        Write tracks to a CSV file

        Args:
            filename: Filename
            tracks: List of Track objects
        """
        filepath = self.output_dir / filename
        fieldnames = ["title", "artist", "album", "year", "genre", "duration", "file_path", "zvuk_id"]

        # Use UTF-8 with BOM for proper Cyrillic support in Excel
        # Use semicolon delimiter for better compatibility
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()

            for track in tracks:
                writer.writerow(track.to_dict())

        logger.info(f"Written {len(tracks)} tracks to {filepath}")
    
    def print_summary(self) -> None:
        """Print summary to console"""
        print("\n" + "=" * 60)
        print("LIBRARY COMPARISON SUMMARY")
        print("=" * 60)
        print(f"Only in local library:  {len(self.diff.only_local):>6} tracks")
        print(f"Only in zvuk.com:       {len(self.diff.only_zvuk):>6} tracks")
        print(f"Match (in both):        {len(self.diff.match):>6} tracks")
        print("=" * 60)
    
    def print_detailed(self, max_items: int = 10) -> None:
        """
        Print detailed results to console
        
        Args:
            max_items: Maximum items to show per category
        """
        self.print_summary()
        
        if self.diff.only_local:
            print("\n📁 ONLY IN LOCAL LIBRARY:")
            print("-" * 40)
            for track in self.diff.only_local[:max_items]:
                print(f"  • {track.artist} - {track.title}")
            if len(self.diff.only_local) > max_items:
                print(f"  ... and {len(self.diff.only_local) - max_items} more")
        
        if self.diff.only_zvuk:
            print("\n🎵 ONLY IN ZVUK.COM:")
            print("-" * 40)
            for track in self.diff.only_zvuk[:max_items]:
                print(f"  • {track.artist} - {track.title}")
            if len(self.diff.only_zvuk) > max_items:
                print(f"  ... and {len(self.diff.only_zvuk) - max_items} more")
        
        if self.diff.match:
            print("\n✅ MATCH (IN BOTH):")
            print("-" * 40)
            for track in self.diff.match[:max_items]:
                print(f"  • {track.artist} - {track.title}")
            if len(self.diff.match) > max_items:
                print(f"  ... and {len(self.diff.match) - max_items} more")
        
        print("\n" + "=" * 60)
        print(f"CSV files saved to: {self.output_dir.absolute()}")
        print("=" * 60 + "\n")
