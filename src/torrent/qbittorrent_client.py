"""
qBittorrent Web API client

For managing torrent downloads
"""

import logging
from typing import Optional

import requests
from qbittorrentapi import Client, APIConnectionError


logger = logging.getLogger(__name__)


class QBittorrentClient:
    """Client for qBittorrent Web UI API"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_https: bool = False
    ):
        """
        Initialize qBittorrent client
        
        Args:
            host: qBittorrent host
            port: qBittorrent Web UI port
            username: Web UI username
            password: Web UI password
            use_https: Use HTTPS connection
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_https = use_https
        self.client: Optional[Client] = None
        
        self._connect()
    
    def _connect(self) -> None:
        """Connect to qBittorrent Web UI"""
        try:
            scheme = "https" if self.use_https else "http"
            self.client = Client(
                host=f"{scheme}://{self.host}:{self.port}",
                username=self.username,
                password=self.password
            )
            
            # Test connection
            self.client.app_version()
            logger.info(f"Connected to qBittorrent at {self.host}:{self.port}")
            
        except APIConnectionError as e:
            logger.error(f"Failed to connect to qBittorrent: {e}")
            self.client = None
        except Exception as e:
            logger.error(f"qBittorrent connection error: {e}")
            self.client = None
    
    def add_torrent(self, torrent_url: str, save_path: Optional[str] = None) -> bool:
        """
        Add torrent from URL (magnet or http)
        
        Args:
            torrent_url: Magnet link or torrent URL
            save_path: Download path (optional)
            
        Returns:
            True if successful
        """
        if not self.client:
            logger.error("qBittorrent client not connected")
            return False
        
        try:
            kwargs = {}
            if save_path:
                kwargs['save_path'] = save_path
            
            self.client.torrents_add(urls=torrent_url, **kwargs)
            logger.info(f"Added torrent: {torrent_url[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add torrent: {e}")
            return False
    
    def add_torrent_file(self, torrent_file_path: str, save_path: Optional[str] = None) -> bool:
        """
        Add torrent from .torrent file
        
        Args:
            torrent_file_path: Path to .torrent file
            save_path: Download path (optional)
            
        Returns:
            True if successful
        """
        if not self.client:
            logger.error("qBittorrent client not connected")
            return False
        
        try:
            kwargs = {}
            if save_path:
                kwargs['save_path'] = save_path
            
            with open(torrent_file_path, 'rb') as f:
                self.client.torrents_add(torrent_files={'torrents': f}, **kwargs)
            
            logger.info(f"Added torrent file: {torrent_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add torrent file: {e}")
            return False
    
    def get_torrents(self, filter_status: Optional[str] = None) -> list:
        """
        Get list of torrents
        
        Args:
            filter_status: Filter by status (all, downloading, seeding, paused, etc.)
            
        Returns:
            List of torrent info dicts
        """
        if not self.client:
            return []
        
        try:
            kwargs = {}
            if filter_status:
                kwargs['filter'] = filter_status
            
            torrents = self.client.torrents_info(**kwargs)
            return list(torrents)
            
        except Exception as e:
            logger.error(f"Failed to get torrents: {e}")
            return []
    
    def pause_torrent(self, torrent_hash: str) -> bool:
        """Pause torrent"""
        if not self.client:
            return False
        
        try:
            self.client.torrents_pause(torrent_hashes=torrent_hash)
            logger.info(f"Paused torrent: {torrent_hash}")
            return True
        except Exception as e:
            logger.error(f"Failed to pause torrent: {e}")
            return False
    
    def resume_torrent(self, torrent_hash: str) -> bool:
        """Resume torrent"""
        if not self.client:
            return False
        
        try:
            self.client.torrents_resume(torrent_hashes=torrent_hash)
            logger.info(f"Resumed torrent: {torrent_hash}")
            return True
        except Exception as e:
            logger.error(f"Failed to resume torrent: {e}")
            return False
    
    def delete_torrent(self, torrent_hash: str, delete_files: bool = False) -> bool:
        """
        Delete torrent
        
        Args:
            torrent_hash: Torrent hash
            delete_files: Also delete downloaded files
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        try:
            self.client.torrents_delete(
                torrent_hashes=torrent_hash,
                delete_files=delete_files
            )
            logger.info(f"Deleted torrent: {torrent_hash}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete torrent: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to qBittorrent"""
        return self.client is not None
