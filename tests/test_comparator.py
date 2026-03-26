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


class TestNormalization:
    """Tests for track normalization features"""

    def test_trailing_punctuation_removal(self):
        """Test removal of trailing punctuation from titles"""
        local_track = Track(title="Song.", artist="Artist")
        zvuk_track = Track(title="Song", artist="Artist")
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 1

    def test_unicode_normalization(self):
        """Test unicode character normalization"""
        local_track = Track(title="Müller", artist="Artist")
        zvuk_track = Track(title="Muller", artist="Artist")
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 1

    def test_track_number_prefix_removal(self):
        """Test removal of track number prefixes"""
        local_track = Track(title="01 - Song", artist="Artist")
        zvuk_track = Track(title="Song", artist="Artist")
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 1

    def test_track_number_dot_prefix_removal(self):
        """Test removal of track number with dot prefix"""
        local_track = Track(title="05. Song", artist="Artist")
        zvuk_track = Track(title="Song", artist="Artist")
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 1

    def test_ost_marker_removal(self):
        """Test removal of OST markers from titles"""
        local_track = Track(title="Song (OST Movie)", artist="Artist")
        zvuk_track = Track(title="Song", artist="Artist")
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 1

    def test_remaster_marker_removal(self):
        """Test removal of remaster markers"""
        local_track = Track(title="Song (Remastered)", artist="Artist")
        zvuk_track = Track(title="Song", artist="Artist")
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 1

    def test_remix_preserved(self):
        """Test that remix markers are NOT removed (different tracks)"""
        local_track = Track(title="Song (Remix)", artist="Artist")
        zvuk_track = Track(title="Song", artist="Artist")
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 0
        assert len(diff.only_local) == 1

    def test_live_preserved(self):
        """Test that live markers are NOT removed (different tracks)"""
        local_track = Track(title="Song (Live)", artist="Artist")
        zvuk_track = Track(title="Song", artist="Artist")
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 0

    def test_acoustic_preserved(self):
        """Test that acoustic markers are NOT removed (different tracks)"""
        local_track = Track(title="Song (Acoustic)", artist="Artist")
        zvuk_track = Track(title="Song", artist="Artist")
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 0

    def test_artist_alias_tatu(self):
        """Test t.A.T.u. alias matching"""
        local_track = Track(title="Song", artist="Тату")
        zvuk_track = Track(title="Song", artist="t.A.T.u.")
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 1

    def test_artist_alias_acdc(self):
        """Test AC/DC alias matching"""
        local_track = Track(title="Song", artist="AC/DC")
        zvuk_track = Track(title="Song", artist="ACDC")
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 1

    def test_the_prefix_removal(self):
        """Test automatic 'The' prefix removal"""
        local_track = Track(title="Song", artist="The Beatles")
        zvuk_track = Track(title="Song", artist="Beatles")
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 1

    def test_number_to_word_conversion(self):
        """Test number to word conversion in artist names"""
        local_track = Track(title="Song", artist="30 Seconds to Mars")
        zvuk_track = Track(title="Song", artist="THIRTY SECONDS TO MARS")
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 1

    def test_name_variants_tsoy(self):
        """Test name variants (Цой = Виктор Цой)"""
        local_track = Track(title="Song", artist="Цой")
        zvuk_track = Track(title="Song", artist="Виктор Цой")
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 1

    def test_multi_artist_comma(self):
        """Test multi-artist matching with comma separator"""
        local_track = Track(title="Song", artist="Artist1, Artist2")
        zvuk_track = Track(title="Song", artist="Artist1")
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 1

    def test_multi_artist_feat(self):
        """Test multi-artist matching with feat. separator"""
        local_track = Track(title="Song", artist="Artist1 feat. Artist2")
        zvuk_track = Track(title="Song", artist="Artist1")
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 1

    def test_multi_artist_ampersand(self):
        """Test multi-artist matching with & separator"""
        local_track = Track(title="Song", artist="Artist1 & Artist2")
        zvuk_track = Track(title="Song", artist="Artist2")
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 1

    def test_multi_artist_reverse(self):
        """Test multi-artist matching when artists are reversed"""
        local_track = Track(title="Song", artist="Artist1, Artist2")
        zvuk_track = Track(title="Song", artist="Artist2, Artist1")
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 1

    def test_combined_normalizations(self):
        """Test multiple normalizations applied together"""
        local_track = Track(title="01 - Song (Remastered)", artist="The Artist")
        zvuk_track = Track(title="Song", artist="ARTIST")
        diff = LibraryComparator([local_track], [zvuk_track]).compare()
        assert len(diff.match) == 1
