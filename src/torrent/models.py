"""
Models for torrent search functionality
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class TorrentSource(Enum):
    """Torrent source providers"""
    RUTRACKER = "rutracker"
    THIRTEEN_X = "1337x"
    NNMCLUB = "nnmclub"


@dataclass
class TorrentSearchResult:
    """Model for torrent search result"""
    title: str
    source: TorrentSource
    torrent_id: str
    magnet_link: Optional[str] = None
    size: Optional[str] = None
    seeds: Optional[int] = None
    leeches: Optional[int] = None
    uploader: Optional[str] = None
    upload_date: Optional[str] = None
    category: Optional[str] = None
    url: Optional[str] = None
    
    def __hash__(self):
        return hash((self.title.lower(), self.source.value))
    
    def __eq__(self, other):
        if not isinstance(other, TorrentSearchResult):
            return False
        return (
            self.title.lower() == other.title.lower() and
            self.source == other.source
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "title": self.title,
            "source": self.source.value,
            "torrent_id": self.torrent_id,
            "magnet_link": self.magnet_link or "",
            "size": self.size or "",
            "seeds": self.seeds or "",
            "leeches": self.leeches or "",
            "uploader": self.uploader or "",
            "upload_date": self.upload_date or "",
            "category": self.category or "",
            "url": self.url or ""
        }


@dataclass
class SearchQuery:
    """Model for search query generation"""
    artist: str
    title: str
    album: Optional[str] = None
    year: Optional[int] = None
    
    def generate_queries(self) -> list[str]:
        """Generate multiple search query variations"""
        queries = []
        
        # Basic: Artist - Title
        queries.append(f"{self.artist} - {self.title}")
        
        # With album
        if self.album:
            queries.append(f"{self.artist} - {self.title} [{self.album}]")
            queries.append(f"{self.artist} - {self.album} - {self.title}")
        
        # With year
        if self.year:
            queries.append(f"{self.artist} - {self.title} ({self.year})")
        
        # Just artist and title
        queries.append(f"{self.artist} {self.title}")
        
        # FLAC/lossless quality queries
        queries.append(f"{self.artist} - {self.title} FLAC")
        queries.append(f"{self.artist} - {self.title} lossless")
        
        return queries
