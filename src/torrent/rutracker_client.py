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

    def get_download_url(self, torrent_id: str) -> str:
        """
        Get RuTracker download URL
        
        Args:
            torrent_id: Torrent ID (topic_id)
            
        Returns:
            Download URL
        """
        return f"{self.BASE_URL}/forum/dl.php?t={torrent_id}"
    
    def download_torrent_file(self, torrent_id: str, save_path: str = None) -> Optional[str]:
        """
        Download .torrent file from RuTracker
        
        Args:
            torrent_id: Torrent ID (topic_id)
            save_path: Directory to save file (default: system temp)
            
        Returns:
            Path to downloaded .torrent file or None
        """
        try:
            import tempfile
            import os
            
            # Create temp directory if needed
            if not save_path:
                save_path = tempfile.gettempdir()
            
            filepath = os.path.join(save_path, f"rutracker_{torrent_id}.torrent")
            
            # Download torrent file using authenticated session
            download_url = self.get_download_url(torrent_id)
            
            response = self.session.get(download_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': f'{self.BASE_URL}/forum/viewtopic.php?t={torrent_id}'
            })
            
            if response.status_code != 200 or len(response.content) < 100:
                logger.error(f"Failed to download torrent: HTTP {response.status_code}, size: {len(response.content)}")
                logger.debug(f"Response: {response.content[:200]}")
                return None
            
            # Save torrent file
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded torrent {torrent_id} to {filepath}")
            return filepath
                
        except Exception as e:
            logger.error(f"Failed to download torrent: {e}")
            return None
    
    def get_magnet_link(self, torrent_id: str, title: str = "") -> Optional[str]:
        """
        Get magnet link or download URL for torrent
        
        For RuTracker, we return the download URL which qBittorrent can handle
        
        Args:
            torrent_id: Torrent ID (topic_id)
            title: Torrent title (optional)
            
        Returns:
            Magnet/download link or None
        """
        try:
            # qBittorrent can download from RuTracker URL directly
            download_url = self.get_download_url(torrent_id)
            
            logger.info(f"Generated download URL for torrent {torrent_id}")
            return download_url
                
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
