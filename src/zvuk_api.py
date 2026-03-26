"""
Модуль работы с API zvuk.com (GraphQL)

Основан на https://github.com/Aiving/sberzvuk-api
"""

import logging
from typing import Optional

import requests

from .config import Config
from .models import Track


logger = logging.getLogger(__name__)


class ZvukAPIClient:
    """Клиент для работы с GraphQL API zvuk.com"""
    
    BASE_URL = "https://zvuk.com/api/v1/graphql"
    
    # GraphQL запросы
    QUERY_GET_COLLECTION = """
    query getCollection($cursor: String, $limit: Int = 100) {
        collection(cursor: $cursor, limit: $limit) {
            page {
                total
                next
                prev
            }
            items {
                id
                title
                searchTitle
                duration
                availability
                artistTemplate
                explicit
                hasFlac
                artists {
                    id
                    title
                }
                release {
                    id
                    title
                    image {
                        src
                    }
                }
                genres {
                    id
                    name
                    shortName
                }
                collectionItemData {
                    itemStatus
                }
            }
        }
    }
    """
    
    QUERY_GET_TRACKS = """
    query getTracks($ids: [ID!]!) {
        getTracks(ids: $ids) {
            id
            title
            searchTitle
            duration
            availability
            artistTemplate
            explicit
            hasFlac
            artists {
                id
                title
            }
            release {
                id
                title
                image {
                    src
                }
            }
            genres {
                id
                name
                shortName
            }
        }
    }
    """
    
    def __init__(self, config: Config):
        """
        Инициализация API клиента
        
        Args:
            config: Конфигурация приложения
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-Auth-Token": config.zvuk_api_token
        })
        logger.info("API клиент zvuk.com инициализирован")
    
    @staticmethod
    def get_anonymous_token() -> str:
        """
        Получение анонимного токена
        
        Returns:
            Токен для доступа к API
        """
        response = requests.get("https://zvuk.com/api/tiny/profile")
        response.raise_for_status()
        data = response.json()
        token = data.get("result", {}).get("token")
        if not token:
            raise ValueError("Не удалось получить анонимный токен")
        logger.info("Получен анонимный токен")
        return token
    
    def get_library(self) -> list[Track]:
        """
        Получение коллекции пользователя (библиотеки)
        
        Returns:
            Список треков из коллекции пользователя
        """
        logger.info("Получение коллекции пользователя из zvuk.com")
        tracks = []
        cursor = None
        
        while True:
            variables = {"limit": 100}
            if cursor:
                variables["cursor"] = cursor
            
            response_data = self._execute_query(
                "getCollection",
                self.QUERY_GET_COLLECTION,
                variables
            )
            
            collection = response_data.get("data", {}).get("collection", {})
            items = collection.get("items", [])
            
            for item in items:
                track = self._parse_track_item(item)
                if track:
                    tracks.append(track)
            
            # Проверка наличия следующей страницы
            page = collection.get("page", {})
            next_cursor = page.get("next")
            
            if not next_cursor or not items:
                break
            
            cursor = next_cursor
        
        logger.info(f"Получено {len(tracks)} треков из коллекции zvuk.com")
        return tracks
    
    def get_tracks_by_ids(self, track_ids: list[int]) -> list[Track]:
        """
        Получение информации о треках по ID
        
        Args:
            track_ids: Список идентификаторов треков
            
        Returns:
            Список объектов Track
        """
        if not track_ids:
            return []
        
        response_data = self._execute_query(
            "getTracks",
            self.QUERY_GET_TRACKS,
            {"ids": track_ids}
        )
        
        tracks_data = response_data.get("data", {}).get("getTracks", [])
        return [self._parse_track_item(item) for item in tracks_data if self._parse_track_item(item)]
    
    def _execute_query(
        self,
        operation_name: str,
        query: str,
        variables: dict
    ) -> dict:
        """
        Выполнение GraphQL запроса
        
        Args:
            operation_name: Имя операции
            query: Текст запроса
            variables: Переменные запроса
            
        Returns:
            Ответ от API
        """
        payload = {
            "operationName": operation_name,
            "variables": variables,
            "query": query
        }
        
        try:
            response = self.session.post(self.BASE_URL, json=payload)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP ошибка при выполнении запроса {operation_name}: {e}")
            if e.response is not None:
                logger.error(f"Ответ сервера: {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к API: {e}")
            raise
    
    def _parse_track_item(self, item: dict) -> Optional[Track]:
        """
        Парсинг отдельного трека из ответа API
        
        Args:
            item: Данные трека от API
            
        Returns:
            Track или None если не удалось распарсить
        """
        try:
            artists = item.get("artists", [])
            artist_names = ", ".join(a.get("title", "") for a in artists if a.get("title"))
            
            release = item.get("release", {}) or {}
            genres = item.get("genres", [])
            genre_names = ", ".join(g.get("name", "") for g in genres if g.get("name"))
            
            return Track(
                title=item.get("title", "Unknown"),
                artist=artist_names or "Unknown Artist",
                album=release.get("title"),
                duration=item.get("duration"),
                genre=genre_names or None,
                zvuk_id=str(item.get("id")) if item.get("id") else None
            )
            
        except Exception as e:
            logger.warning(f"Ошибка парсинга трека: {e}, данные: {item}")
            return None
    
    def test_connection(self) -> bool:
        """
        Проверка подключения к API
        
        Returns:
            True если подключение успешно
        """
        try:
            # Простой запрос для проверки токена
            self.get_tracks_by_ids([1])
            logger.info("Подключение к API zvuk.com успешно")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к API: {e}")
            return False
