"""
Library comparison module

Compares local MP3 library with zvuk.com collection
"""

import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Callable

from .models import Track, LibraryDiff


logger = logging.getLogger(__name__)

# Load normalization config
_CONFIG_PATH = Path(__file__).parent / "config" / "normalization.json"
with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
    _NORMALIZATION_CONFIG = json.load(f)

ARTIST_ALIASES = _NORMALIZATION_CONFIG["artist_aliases"]
NUMBER_WORDS = _NORMALIZATION_CONFIG["number_words"]
NAME_VARIANTS = _NORMALIZATION_CONFIG["name_variants"]
TITLE_CLEANUP_PATTERNS = _NORMALIZATION_CONFIG["title_cleanup_patterns"]


class LibraryComparator:
    """Comparator for comparing two libraries"""
    
    def __init__(
        self,
        local_tracks: list[Track],
        zvuk_tracks: list[Track],
        progress_callback: Callable[[int, int], None] | None = None
    ):
        """
        Initialize comparator
        
        Args:
            local_tracks: List of local tracks
            zvuk_tracks: List of tracks from zvuk.com
            progress_callback: Callback for progress display (current, total)
        """
        self.local_tracks = local_tracks
        self.zvuk_tracks = zvuk_tracks
        self.progress_callback = progress_callback
        logger.info(f"Initializing comparator: {len(local_tracks)} local, {len(zvuk_tracks)} zvuk")
    
    def compare(self) -> LibraryDiff:
        """
        Compare libraries

        Returns:
            LibraryDiff with comparison results
        """
        logger.info("Starting library comparison")

        # Create sets for fast lookup
        # Using (title, artist) as key
        local_set = self._create_track_set(self.local_tracks)
        zvuk_set = self._create_track_set(self.zvuk_tracks)

        # Also create sets with individual artists for multi-artist tracks
        local_multi = self._create_multi_artist_set(self.local_tracks)
        zvuk_multi = self._create_multi_artist_set(self.zvuk_tracks)

        local_keys = set(local_set.keys())
        zvuk_keys = set(zvuk_set.keys())

        # Find matches including multi-artist cases
        match_keys = local_keys & zvuk_keys

        # Also find matches where one has single artist and other has multiple
        local_individual = set(local_multi.keys())
        zvuk_individual = set(zvuk_multi.keys())
        multi_match_keys = local_individual & zvuk_individual

        # Add multi-artist matches that weren't already found
        new_matches = multi_match_keys - match_keys

        # Map individual keys back to full keys for multi-artist matches
        for ind_key in new_matches:
            title, artist = ind_key
            # Find corresponding full tracks
            local_track = local_multi.get(ind_key)
            zvuk_track = zvuk_multi.get(ind_key)
            if local_track and zvuk_track:
                # Create full keys
                local_full_key = self._normalize_track_key(local_track)
                zvuk_full_key = self._normalize_track_key(zvuk_track)
                # Add to match_keys using the local version
                match_keys.add(local_full_key)

        # Find differences
        only_local_keys = local_keys - zvuk_keys
        only_zvuk_keys = zvuk_keys - local_keys

        logger.info(f"Found matches: {len(match_keys)}")
        logger.info(f"Only local: {len(only_local_keys)}")
        logger.info(f"Only zvuk: {len(only_zvuk_keys)}")

        diff = LibraryDiff(
            only_local=[local_set[key] for key in sorted(only_local_keys)],
            only_zvuk=[zvuk_set[key] for key in sorted(only_zvuk_keys)],
            match=[local_set[key] for key in sorted(match_keys)]
        )

        logger.info("Comparison completed")
        return diff
    
    def _create_track_set(self, tracks: list[Track]) -> dict[tuple[str, str], Track]:
        """
        Create track set for fast lookup

        Args:
            tracks: List of tracks

        Returns:
            Dictionary {(title, artist): Track}
        """
        track_dict = {}
        total = len(tracks)

        for i, track in enumerate(tracks):
            # Normalize key
            key = self._normalize_track_key(track)

            # Save track (if duplicate - last wins)
            track_dict[key] = track

            if self.progress_callback:
                self.progress_callback(i + 1, total)

        return track_dict

    def _create_multi_artist_set(self, tracks: list[Track]) -> dict[tuple[str, str], Track]:
        """
        Create track set with individual artists for multi-artist tracks

        Args:
            tracks: List of tracks

        Returns:
            Dictionary {(title, individual_artist): Track}
        """
        track_dict = {}

        for track in tracks:
            # Normalize title
            title = track.title.lower().strip()
            title = " ".join(title.split())
            title = self._cleanup_title(title)
            title = re.sub(r'[\.\-\s]+$', '', title)
            title = self._normalize_unicode(title)

            # Normalize artist
            artist = track.artist.lower().strip()
            artist = " ".join(artist.split())
            artist = re.sub(r'[\.\-\s]+$', '', artist)
            artist = self._normalize_unicode(artist)

            # Split by common multi-artist separators
            separators = [',', ' feat. ', ' feat ', ' ft. ', ' ft ', ' vs. ', ' vs ', ' & ', ' x ', ' + ']
            artists = [artist]
            for sep in separators:
                if sep in artist:
                    artists = artist.split(sep)
                    break

            # Create entry for each individual artist
            for individual in artists:
                individual = individual.strip()
                individual = self._normalize_artist_name(individual)
                key = (title, individual)
                track_dict[key] = track

        return track_dict
    
    def _normalize_track_key(self, track: Track) -> tuple[str, str]:
        """
        Normalize track key for comparison

        Args:
            track: Track

        Returns:
            Tuple (normalized_title, normalized_artist)
        """
        # Normalize title
        title = track.title.lower().strip()
        # Remove extra spaces
        title = " ".join(title.split())
        # Remove track number prefixes, OST markers, remix info
        title = self._cleanup_title(title)
        # Remove trailing punctuation (dots, dashes, etc.)
        title = re.sub(r'[\.\-\s]+$', '', title)
        # Normalize unicode characters (ë -> e, etc.)
        title = self._normalize_unicode(title)

        # Normalize artist
        artist = track.artist.lower().strip()
        artist = " ".join(artist.split())
        # Remove trailing punctuation
        artist = re.sub(r'[\.\-\s]+$', '', artist)
        # Normalize unicode characters
        artist = self._normalize_unicode(artist)
        # Remove all non-alphanumeric characters for matching
        artist = self._normalize_artist_name(artist)

        return (title, artist)

    def _cleanup_title(self, title: str) -> str:
        """
        Clean up track title by removing common prefixes and suffixes

        Args:
            title: Original track title

        Returns:
            Cleaned title
        """
        for pattern in TITLE_CLEANUP_PATTERNS:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)

        # Clean up extra spaces after removals
        title = " ".join(title.split())

        return title

    def _normalize_unicode(self, text: str) -> str:
        """
        Normalize unicode characters to ASCII equivalents

        Only applies to Latin characters to preserve Cyrillic letters like 'й'

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Only normalize if text contains Latin characters with diacritics
        # Preserve Cyrillic letters intact
        import string
        has_latin = any(c in string.ascii_letters for c in text)
        has_cyrillic = any('\u0400' <= c <= '\u04FF' for c in text)

        # Don't normalize pure Cyrillic text (preserves 'й', 'ё', etc.)
        if has_cyrillic and not has_latin:
            return text

        # Normalize unicode characters (ë -> e, ü -> u, etc.)
        normalized = unicodedata.normalize('NFKD', text)
        # Remove diacritics
        return ''.join(c for c in normalized if not unicodedata.combining(c))

    def _normalize_artist_name(self, artist: str) -> str:
        """
        Normalize artist name for better matching

        Args:
            artist: Normalized artist name

        Returns:
            Canonical artist name
        """
        # Remove all non-alphanumeric characters
        clean = re.sub(r'[^a-zа-я0-9]', '', artist)

        # Check for known aliases
        for canonical, aliases in ARTIST_ALIASES.items():
            if clean == canonical or clean in aliases:
                return canonical

        # Apply automatic normalizations
        clean = self._auto_normalize_artist(clean)

        return clean

    def _auto_normalize_artist(self, artist: str) -> str:
        """
        Apply automatic normalization rules to artist name

        Args:
            artist: Cleaned artist name (alphanumeric only)

        Returns:
            Normalized artist name
        """
        # Remove leading "the" (thebeatles -> beatles)
        if artist.startswith('the'):
            artist = artist[3:]

        # Convert numbers to words (30secondstomars -> thirtysecondstomars)
        # Sort by length descending to replace longer matches first
        for num, word in sorted(NUMBER_WORDS.items(), key=lambda x: -len(x[0])):
            artist = artist.replace(num, word)

        # Handle common name variations (цой -> викторцой)
        artist = self._handle_name_variants(artist)

        return artist

    def _handle_name_variants(self, artist: str) -> str:
        """
        Handle artist name variants like "Цой" vs "Виктор Цой"

        Args:
            artist: Artist name

        Returns:
            Normalized artist name
        """
        for canonical, variants in NAME_VARIANTS.items():
            # Check if artist matches canonical or any variant
            if artist == canonical or artist in variants:
                return canonical
            # Check if artist contains canonical/variant or vice versa
            if canonical in artist or any(v in artist for v in variants):
                return canonical
            # Check if artist is contained in canonical/variant
            if artist in canonical or any(artist in v for v in variants):
                return canonical

        return artist
