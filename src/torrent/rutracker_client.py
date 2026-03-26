"""
RuTracker client using py-rutracker-client library

Requires RuTracker account credentials
"""

import logging
from typing import Optional

from py_rutracker import RuTrackerClient as SyncClient

from .models import TorrentSearchResult, TorrentSource


logger = logging.getLogger(__name__)


class RuTrackerClient:
    """Client for RuTracker.org"""

    def __init__(self, login: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize RuTracker client

        Args:
            login: RuTracker login
            password: RuTracker password
        """
        self.login = login
        self.password = password
        self.client: Optional[SyncClient] = None

        if login and password:
            self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with RuTracker"""
        try:
            self.client = SyncClient(self.login, self.password)
            logger.info("RuTracker authentication successful")
        except Exception as e:
            logger.error(f"RuTracker authentication failed: {e}")
            self.client = None

    def search(self, query: str, limit: int = 10, format: Optional[str] = None) -> list[TorrentSearchResult]:
        """
        Search for torrents

        Args:
            query: Search query
            limit: Maximum results
            format: Format filter (e.g., 'MP3', 'FLAC', 'ALAC')

        Returns:
            List of TorrentSearchResult
        """
        if not self.client:
            logger.warning("RuTracker client not authenticated")
            return []

        try:
            # Add format to query if specified
            search_query = query
            if format:
                search_query = f"{query} {format}"
            
            results = self.client.search_all_pages(search_query)
            torrents = []

            for result in results[:limit]:
                # Handle different attribute names
                seeds = getattr(result, 'seeds', None) or getattr(result, 'seeders', 0)
                leeches = getattr(result, 'leeches', None) or getattr(result, 'leechers', 0)
                
                # Skip if format doesn't match (check in title)
                if format and format.upper() not in result.title.upper():
                    continue

                torrent = TorrentSearchResult(
                    title=result.title,
                    source=TorrentSource.RUTRACKER,
                    torrent_id=str(result.topic_id),
                    size=getattr(result, 'size', ''),
                    seeds=seeds,
                    leeches=leeches,
                    uploader=getattr(result, 'author', ''),
                    upload_date=str(result.registered) if hasattr(result, 'registered') and result.registered else None,
                    category=getattr(result, 'category', ''),
                    url=f"https://rutracker.org/forum/viewtopic.php?t={result.topic_id}"
                )
                torrents.append(torrent)

            logger.info(f"RuTracker search '{search_query}' found {len(torrents)} results")
            return torrents

        except Exception as e:
            logger.error(f"RuTracker search error: {e}")
            return []

    def get_magnet_link(self, torrent_id: str) -> Optional[str]:
        """
        Get download link for torrent

        Args:
            torrent_id: Torrent ID

        Returns:
            Download URL or None
        """
        if not self.client:
            return None

        try:
            # Return RuTracker download URL (qBittorrent can handle this)
            return f"https://rutracker.org/forum/dl.php?t={torrent_id}"
        except Exception as e:
            logger.error(f"Failed to get download link: {e}")
            return None

    def download_torrent(self, torrent_id: str, save_path: str) -> Optional[str]:
        """
        Download .torrent file

        Args:
            torrent_id: Torrent ID
            save_path: Directory to save file

        Returns:
            Path to saved file or None
        """
        if not self.client:
            return None

        try:
            file_path = self.client.download(torrent_id, save_path=save_path)
            logger.info(f"Downloaded torrent {torrent_id} to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to download torrent: {e}")
            return None
