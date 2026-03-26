"""
Tests for torrent search module
"""

import pytest
from src.torrent.models import TorrentSearchResult, SearchQuery, TorrentSource


class TestTorrentSearchResult:
    """Tests for TorrentSearchResult model"""
    
    def test_creation(self):
        result = TorrentSearchResult(
            title="Test Track",
            source=TorrentSource.RUTRACKER,
            torrent_id="12345"
        )
        assert result.title == "Test Track"
        assert result.source == TorrentSource.RUTRACKER
        assert result.torrent_id == "12345"
    
    def test_equality(self):
        result1 = TorrentSearchResult(
            title="Test Track",
            source=TorrentSource.RUTRACKER,
            torrent_id="12345"
        )
        result2 = TorrentSearchResult(
            title="test track",
            source=TorrentSource.RUTRACKER,
            torrent_id="67890"
        )
        assert result1 == result2
    
    def test_hash(self):
        result1 = TorrentSearchResult(
            title="Test Track",
            source=TorrentSource.RUTRACKER,
            torrent_id="12345"
        )
        result2 = TorrentSearchResult(
            title="test track",
            source=TorrentSource.RUTRACKER,
            torrent_id="67890"
        )
        assert hash(result1) == hash(result2)
    
    def test_to_dict(self):
        result = TorrentSearchResult(
            title="Test Track",
            source=TorrentSource.THIRTEEN_X,
            torrent_id="12345",
            seeds=100,
            size="100 MB"
        )
        data = result.to_dict()
        assert data["title"] == "Test Track"
        assert data["source"] == "1337x"
        assert data["seeds"] == 100
        assert data["size"] == "100 MB"


class TestSearchQuery:
    """Tests for SearchQuery model"""
    
    def test_creation(self):
        query = SearchQuery(artist="AC/DC", title="Highway to Hell")
        assert query.artist == "AC/DC"
        assert query.title == "Highway to Hell"
        assert query.album is None
        assert query.year is None
    
    def test_generate_queries_basic(self):
        query = SearchQuery(artist="AC/DC", title="Highway to Hell")
        queries = query.generate_queries()
        
        assert "AC/DC - Highway to Hell" in queries
        assert "AC/DC Highway to Hell" in queries
        assert "AC/DC - Highway to Hell FLAC" in queries
    
    def test_generate_queries_with_album(self):
        query = SearchQuery(
            artist="AC/DC",
            title="Highway to Hell",
            album="Highway to Hell"
        )
        queries = query.generate_queries()
        
        assert "AC/DC - Highway to Hell [Highway to Hell]" in queries
        assert "AC/DC - Highway to Hell - Highway to Hell" in queries
    
    def test_generate_queries_with_year(self):
        query = SearchQuery(
            artist="AC/DC",
            title="Highway to Hell",
            year=1979
        )
        queries = query.generate_queries()
        
        assert "AC/DC - Highway to Hell (1979)" in queries
    
    def test_generate_queries_count(self):
        query = SearchQuery(
            artist="AC/DC",
            title="Highway to Hell",
            album="Highway to Hell",
            year=1979
        )
        queries = query.generate_queries()
        
        # Should have at least 7 query variations
        assert len(queries) >= 7


class TestTorrentSource:
    """Tests for TorrentSource enum"""
    
    def test_values(self):
        assert TorrentSource.RUTRACKER.value == "rutracker"
        assert TorrentSource.THIRTEEN_X.value == "1337x"
        assert TorrentSource.NNMCLUB.value == "nnmclub"
