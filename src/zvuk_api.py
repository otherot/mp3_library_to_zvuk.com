"""
Module for working with zvuk.com GraphQL API

Based on https://github.com/Aiving/sberzvuk-api
"""

import logging
from typing import Optional

import requests

from .config import Config
from .models import Track


logger = logging.getLogger(__name__)


class ZvukAPIClient:
    """Client for working with zvuk.com GraphQL API"""
    
    BASE_URL = "https://zvuk.com/api/v1/graphql"
    
    # GraphQL queries
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
        Initialize API client
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-Auth-Token": config.zvuk_api_token
        })
        logger.info("Zvuk.com API client initialized")
    
    @staticmethod
    def get_anonymous_token() -> str:
        """
        Get anonymous token
        
        Returns:
            Token for API access
        """
        response = requests.get("https://zvuk.com/api/tiny/profile")
        response.raise_for_status()
        data = response.json()
        token = data.get("result", {}).get("token")
        if not token:
            raise ValueError("Failed to get anonymous token")
        logger.info("Anonymous token received")
        return token
    
    def get_library(self) -> list[Track]:
        """
        Get user collection (library)
        
        Returns:
            List of tracks from user's zvuk.com collection
        """
        logger.info("Fetching user collection from zvuk.com")
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
            
            # Check for next page
            page = collection.get("page", {})
            next_cursor = page.get("next")
            
            if not next_cursor or not items:
                break
            
            cursor = next_cursor
        
        logger.info(f"Received {len(tracks)} tracks from zvuk.com collection")
        return tracks
    
    def get_tracks_by_ids(self, track_ids: list[int]) -> list[Track]:
        """
        Get track information by IDs
        
        Args:
            track_ids: List of track IDs
            
        Returns:
            List of Track objects
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
        Execute GraphQL query
        
        Args:
            operation_name: Operation name
            query: Query text
            variables: Query variables
            
        Returns:
            API response
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
            logger.error(f"HTTP error executing {operation_name}: {e}")
            if e.response is not None:
                logger.error(f"Server response: {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error to API: {e}")
            raise
    
    def _parse_track_item(self, item: dict) -> Optional[Track]:
        """
        Parse individual track from API response
        
        Args:
            item: Track data from API
            
        Returns:
            Track or None if failed to parse
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
            logger.warning(f"Error parsing track: {e}, data: {item}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test API connection
        
        Returns:
            True if connection successful
        """
        try:
            # Simple request to test token
            self.get_tracks_by_ids([1])
            logger.info("Connection to zvuk.com API successful")
            return True
        except Exception as e:
            logger.error(f"Connection error to API: {e}")
            return False
