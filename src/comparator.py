"""
Library comparison module

Compares local MP3 library with zvuk.com collection
"""

import logging
from typing import Callable

from .models import Track, LibraryDiff


logger = logging.getLogger(__name__)


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
        
        local_keys = set(local_set.keys())
        zvuk_keys = set(zvuk_set.keys())
        
        # Find differences
        only_local_keys = local_keys - zvuk_keys
        only_zvuk_keys = zvuk_keys - local_keys
        match_keys = local_keys & zvuk_keys
        
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
        # Remove extra spaces, special characters
        title = " ".join(title.split())
        
        # Normalize artist
        artist = track.artist.lower().strip()
        artist = " ".join(artist.split())
        
        return (title, artist)
