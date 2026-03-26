"""
Tests for library comparator module
"""

import pytest
from src.models import Track, LibraryDiff
from src.comparator import LibraryComparator


class TestTrack:
    """Tests for Track model"""
    
    def test_track_creation(self):
        track = Track(title="Test", artist="Artist")
        assert track.title == "Test"
        assert track.artist == "Artist"
    
    def test_track_equality(self):
        track1 = Track(title="Test", artist="Artist")
        track2 = Track(title="test", artist="artist")
        assert track1 == track2
    
    def test_track_hash(self):
        track1 = Track(title="Test", artist="Artist")
        track2 = Track(title="test", artist="artist")
        assert hash(track1) == hash(track2)
    
    def test_track_to_dict(self):
        track = Track(title="Test", artist="Artist", album="Album")
        data = track.to_dict()
        assert data["title"] == "Test"
        assert data["artist"] == "Artist"
        assert data["album"] == "Album"


class TestLibraryComparator:
    """Tests for LibraryComparator"""
    
    def test_compare_empty_libraries(self):
        diff = LibraryComparator([], []).compare()
        assert len(diff.only_local) == 0
        assert len(diff.only_zvuk) == 0
        assert len(diff.match) == 0
    
    def test_compare_identical_libraries(self):
        track = Track(title="Test", artist="Artist")
        diff = LibraryComparator([track], [track]).compare()
        assert len(diff.only_local) == 0
        assert len(diff.only_zvuk) == 0
        assert len(diff.match) == 1
    
    def test_compare_different_libraries(self):
        local_track = Track(title="Local", artist="Artist")
        zvuk_track = Track(title="Zvuk", artist="Artist")
        
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.only_local) == 1
        assert len(diff.only_zvuk) == 1
        assert len(diff.match) == 0
    
    def test_compare_case_insensitive(self):
        local_track = Track(title="Test", artist="Artist")
        zvuk_track = Track(title="TEST", artist="ARTIST")
        
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 1
    
    def test_compare_partial_match(self):
        local_tracks = [
            Track(title="Song 1", artist="Artist"),
            Track(title="Song 2", artist="Artist"),
        ]
        zvuk_tracks = [
            Track(title="Song 1", artist="Artist"),
            Track(title="Song 3", artist="Artist"),
        ]
        
        diff = LibraryComparator(local_tracks, zvuk_tracks).compare()
        assert len(diff.match) == 1
        assert len(diff.only_local) == 1
        assert len(diff.only_zvuk) == 1
