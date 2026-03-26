"""
Library comparison module

Compares local MP3 library with zvuk.com collection
"""

import logging
import re
import unicodedata
from typing import Callable

from .models import Track, LibraryDiff


logger = logging.getLogger(__name__)

# Known artist aliases (canonical name -> aliases)
ARTIST_ALIASES = {
    'tatu': ['t.a.t.u', 't.a.t.u.', 'тату'],
    'linkin park': ['linkinpark'],
    'gunsn roses': ['guns n roses', 'guns n\' roses', 'guns and roses'],
    'acdc': ['ac/dc', 'ac dc'],
    'nirvana': ['nirvana us'],
    'metallica': ['metallica us'],
}

# Patterns to remove from track titles
TITLE_CLEANUP_PATTERNS = [
    # Track number prefixes: "01 -", "05.", "1x05."
    r'^\d+[x\.]?\d*\s*[-\.]\s*',
    # OST/Soundtrack prefixes: "OST -", "Soundtrack -"
    r'^(ost|soundtrack|саундтрек)\s*[-:]\s*',
    # Version suffixes in parentheses (but not Live/Acoustic/Remix)
    r'\s*\([^)]*?(ost|soundtrack|саундтрек|radio edit|album version|single version|remastered?|extended|instrumental|feat\.?|ft\.?)[^)]*?\)',
    # Suffixes: " - OST", " (Soundtrack)"
    r'\s*[-(](ost|soundtrack|саундтрек)[\s)]*',
]


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

        Args:
            text: Input text

        Returns:
            Normalized text
        """
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

        return clean
