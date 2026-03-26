"""
Модели данных для сравнения библиотек
"""

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class Track:
    """Модель музыкального трека"""
    title: str
    artist: str
    album: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    duration: Optional[int] = None  # в секундах
    file_path: Optional[Path] = None  # для локальных треков
    zvuk_id: Optional[str] = None  # для треков из zvuk.com
    
    def __hash__(self):
        return hash((self.title.lower(), self.artist.lower()))
    
    def __eq__(self, other):
        if not isinstance(other, Track):
            return False
        return (
            self.title.lower() == other.title.lower() and
            self.artist.lower() == other.artist.lower()
        )
    
    def to_dict(self) -> dict:
        """Конвертация в словарь"""
        return {
            "title": self.title,
            "artist": self.artist,
            "album": self.album or "",
            "year": self.year or "",
            "genre": self.genre or "",
            "duration": self.duration or "",
            "file_path": str(self.file_path) if self.file_path else "",
            "zvuk_id": self.zvuk_id or ""
        }


@dataclass
class LibraryDiff:
    """Результат сравнения библиотек"""
    only_local: list[Track] = field(default_factory=list)
    only_zvuk: list[Track] = field(default_factory=list)
    match: list[Track] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Конвертация в словарь"""
        return {
            "only_local": [t.to_dict() for t in self.only_local],
            "only_zvuk": [t.to_dict() for t in self.only_zvuk],
            "match": [t.to_dict() for t in self.match]
        }
