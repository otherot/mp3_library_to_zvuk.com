"""
Модуль сравнения библиотек

Сравнивает локальную MP3-библиотеку с коллекцией zvuk.com
"""

import logging
from typing import Callable

from .models import Track, LibraryDiff


logger = logging.getLogger(__name__)


class LibraryComparator:
    """Компаратор для сравнения двух библиотек"""
    
    def __init__(
        self,
        local_tracks: list[Track],
        zvuk_tracks: list[Track],
        progress_callback: Callable[[int, int], None] | None = None
    ):
        """
        Инициализация компаратора
        
        Args:
            local_tracks: Список локальных треков
            zvuk_tracks: Список треков из zvuk.com
            progress_callback: Callback для отображения прогресса (current, total)
        """
        self.local_tracks = local_tracks
        self.zvuk_tracks = zvuk_tracks
        self.progress_callback = progress_callback
        logger.info(f"Инициализация компаратора: {len(local_tracks)} локальных, {len(zvuk_tracks)} zvuk")
    
    def compare(self) -> LibraryDiff:
        """
        Сравнение библиотек
        
        Returns:
            LibraryDiff с результатами сравнения
        """
        logger.info("Начало сравнения библиотек")
        
        # Создаём множества для быстрого поиска
        # Используем (title, artist) как ключ
        local_set = self._create_track_set(self.local_tracks)
        zvuk_set = self._create_track_set(self.zvuk_tracks)
        
        local_keys = set(local_set.keys())
        zvuk_keys = set(zvuk_set.keys())
        
        # Находим различия
        only_local_keys = local_keys - zvuk_keys
        only_zvuk_keys = zvuk_keys - local_keys
        match_keys = local_keys & zvuk_keys
        
        logger.info(f"Найдено совпадений: {len(match_keys)}")
        logger.info(f"Только локально: {len(only_local_keys)}")
        logger.info(f"Только zvuk: {len(only_zvuk_keys)}")
        
        diff = LibraryDiff(
            only_local=[local_set[key] for key in sorted(only_local_keys)],
            only_zvuk=[zvuk_set[key] for key in sorted(only_zvuk_keys)],
            match=[local_set[key] for key in sorted(match_keys)]
        )
        
        logger.info("Сравнение завершено")
        return diff
    
    def _create_track_set(self, tracks: list[Track]) -> dict[tuple[str, str], Track]:
        """
        Создание множества треков для быстрого поиска
        
        Args:
            tracks: Список треков
            
        Returns:
            Словарь {(title, artist): Track}
        """
        track_dict = {}
        total = len(tracks)
        
        for i, track in enumerate(tracks):
            # Нормализация ключа
            key = self._normalize_track_key(track)
            
            # Сохраняем трек (если дубликат - последний wins)
            track_dict[key] = track
            
            if self.progress_callback:
                self.progress_callback(i + 1, total)
        
        return track_dict
    
    def _normalize_track_key(self, track: Track) -> tuple[str, str]:
        """
        Нормализация ключа трека для сравнения
        
        Args:
            track: Трек
            
        Returns:
            Кортеж (normalized_title, normalized_artist)
        """
        # Нормализация названия
        title = track.title.lower().strip()
        # Удаляем лишние пробелы, специальные символы
        title = " ".join(title.split())
        
        # Нормализация исполнителя
        artist = track.artist.lower().strip()
        artist = " ".join(artist.split())
        
        return (title, artist)
