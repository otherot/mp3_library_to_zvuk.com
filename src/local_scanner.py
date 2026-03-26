"""
Модуль сканирования локальной MP3-библиотеки

Сканирует указанную директорию и извлекает метаданные из MP3-файлов
"""

import logging
from pathlib import Path
from typing import Generator

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON

from .models import Track


logger = logging.getLogger(__name__)


class LocalLibraryScanner:
    """Сканер локальной MP3-библиотеки"""
    
    SUPPORTED_EXTENSIONS = {".mp3"}
    
    def __init__(self, library_path: Path):
        """
        Инициализация сканера
        
        Args:
            library_path: Путь к директории с библиотекой
        """
        self.library_path = library_path
        logger.info(f"Инициализация сканера для пути: {library_path}")
    
    def scan(self) -> list[Track]:
        """
        Сканирование библиотеки
        
        Returns:
            Список треков с метаданными
        """
        logger.info("Начало сканирования библиотеки")
        tracks = list(self._find_all_tracks())
        logger.info(f"Найдено {len(tracks)} треков")
        return tracks
    
    def _find_all_tracks(self) -> Generator[Track, None, None]:
        """Генератор для поиска всех MP3-файлов"""
        for ext in self.SUPPORTED_EXTENSIONS:
            pattern = f"**/*{ext}"
            logger.debug(f"Поиск файлов по паттерну: {pattern}")
            
            for file_path in self.library_path.glob(pattern):
                track = self._parse_file(file_path)
                if track:
                    yield track
    
    def _parse_file(self, file_path: Path) -> Track | None:
        """
        Извлечение метаданных из файла
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Track с метаданными или None если не удалось прочитать
        """
        try:
            audio = MP3(file_path, ID3=ID3)
            
            # Извлекаем метаданные из ID3-тегов
            title = self._get_tag(audio, TIT2)
            artist = self._get_tag(audio, TPE1)
            album = self._get_tag(audio, TALB)
            year = self._get_year(audio)
            genre = self._get_tag(audio, TCON)
            duration = int(audio.info.length) if audio.info else None
            
            # Если нет тегов, используем имя файла
            if not title:
                title = file_path.stem
            
            return Track(
                title=title or "Unknown",
                artist=artist or "Unknown Artist",
                album=album,
                year=year,
                genre=genre,
                duration=duration,
                file_path=file_path
            )
            
        except Exception as e:
            logger.warning(f"Ошибка чтения файла {file_path}: {e}")
            # Возвращаем минимальный трек на основе имени файла
            return Track(
                title=file_path.stem,
                artist="Unknown Artist",
                file_path=file_path
            )
    
    def _get_tag(self, audio: MP3, tag_class) -> str | None:
        """Получение значения тега"""
        try:
            if audio.tags:
                tag = audio.tags.get(tag_class.__name__)
                if tag:
                    return str(tag)
        except Exception:
            pass
        return None
    
    def _get_year(self, audio: MP3) -> int | None:
        """Получение года из тега"""
        try:
            if audio.tags:
                tag = audio.tags.get("TDRC")
                if tag:
                    year_str = str(tag)
                    # Год может быть в формате YYYY или YYYY-MM-DD
                    return int(year_str[:4])
        except Exception:
            pass
        return None
