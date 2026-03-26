"""
Torrent search aggregator engine

Searches multiple sources and aggregates results
"""

import asyncio
import logging
from typing import Optional

from .models import TorrentSearchResult, SearchQuery, TorrentSource
from .rutracker_client import RuTrackerClient
from .thirteensx_client import ThirteenXClient
from .nnmclub_client import NNMClubClient


logger = logging.getLogger(__name__)


class TorrentSearchEngine:
    """Aggregator for torrent search across multiple sources"""
    
    def __init__(
        self,
        rutracker_login: Optional[str] = None,
        rutracker_password: Optional[str] = None,
        sources: Optional[list[TorrentSource]] = None,
        format_filter: Optional[str] = None
    ):
        """
        Initialize search engine
        
        Args:
            rutracker_login: RuTracker login
            rutracker_password: RuTracker password
            sources: List of sources to search (default: all)
            format_filter: Format filter for RuTracker (e.g., 'MP3', 'FLAC')
        """
        self.rutracker_client = RuTrackerClient(rutracker_login, rutracker_password)
        self.thirteensx_client = ThirteenXClient()
        self.nnmclub_client = NNMClubClient()
        
        self.sources = sources or [
            TorrentSource.RUTRACKER,
            TorrentSource.THIRTEEN_X,
            TorrentSource.NNMCLUB
        ]
        self.format_filter = format_filter
        
        logger.info(f"TorrentSearchEngine initialized with sources: {[s.value for s in self.sources]}")
        if format_filter:
            logger.info(f"Format filter: {format_filter}")
    
    def search(self, query: str, limit_per_source: int = 5) -> list[TorrentSearchResult]:
        """
        Search for torrents across all sources
        
        Args:
            query: Search query
            limit_per_source: Max results per source
            
        Returns:
            List of TorrentSearchResult (sorted by seeds)
        """
        all_results = []
        
        # Search RuTracker (sync) with format filter
        if TorrentSource.RUTRACKER in self.sources:
            logger.info(f"Searching RuTracker: {query}")
            results = self.rutracker_client.search(query, limit_per_source, format=self.format_filter)
            all_results.extend(results)
        
        # Search async sources
        async_results = asyncio.run(self._search_async(query, limit_per_source))
        all_results.extend(async_results)
        
        # Sort by seeds (descending)
        all_results.sort(key=lambda x: x.seeds or 0, reverse=True)
        
        logger.info(f"Total search results: {len(all_results)}")
        return all_results
    
    async def _search_async(self, query: str, limit: int) -> list[TorrentSearchResult]:
        """Search async sources (1337x, nnmclub)"""
        all_results = []
        
        if TorrentSource.THIRTEEN_X in self.sources:
            logger.info(f"Searching 1337x: {query}")
            results = await self.thirteensx_client.search(query, limit)
            all_results.extend(results)
        
        if TorrentSource.NNMCLUB in self.sources:
            logger.info(f"Searching NNMClub: {query}")
            results = await self.nnmclub_client.search(query, limit)
            all_results.extend(results)
        
        return all_results
    
    def search_track(self, artist: str, title: str, album: Optional[str] = None, 
                     year: Optional[int] = None, limit: int = 5) -> list[TorrentSearchResult]:
        """
        Search for a specific track
        
        Args:
            artist: Artist name
            title: Track title
            album: Album name (optional)
            year: Year (optional)
            limit: Max results
            
        Returns:
            List of TorrentSearchResult
        """
        search_query = SearchQuery(artist=artist, title=title, album=album, year=year)
        queries = search_query.generate_queries()
        
        all_results = []
        seen_titles = set()
        
        for query in queries[:3]:  # Try first 3 query variations
            results = self.search(query, limit_per_source=limit)
            
            for result in results:
                # Avoid duplicates
                if result.title.lower() not in seen_titles:
                    seen_titles.add(result.title.lower())
                    all_results.append(result)
            
            if len(all_results) >= limit:
                break
        
        return all_results[:limit]
    
    async def get_magnet_link(self, result: TorrentSearchResult) -> Optional[str]:
        """
        Get magnet link for search result
        
        Args:
            result: TorrentSearchResult
            
        Returns:
            Magnet link or None
        """
        if result.source == TorrentSource.RUTRACKER:
            return self.rutracker_client.get_magnet_link(result.torrent_id)
        elif result.source == TorrentSource.THIRTEEN_X:
            return await self.thirteensx_client.get_magnet_link(result.torrent_id)
        elif result.source == TorrentSource.NNMCLUB:
            return await self.nnmclub_client.get_magnet_link(result.torrent_id)
        
        return None
    
    def get_all_magnet_links(self, results: list[TorrentSearchResult]) -> dict[str, Optional[str]]:
        """
        Get magnet links for multiple results
        
        Args:
            results: List of TorrentSearchResult
            
        Returns:
            Dict mapping torrent_id to magnet_link
        """
        magnet_links = {}
        
        # Sync (RuTracker)
        for result in results:
            if result.source == TorrentSource.RUTRACKER:
                magnet_links[result.torrent_id] = self.rutracker_client.get_magnet_link(result.torrent_id)
        
        # Async (1337x, NNMClub)
        async def fetch_async():
            for result in results:
                if result.source == TorrentSource.THIRTEEN_X:
                    magnet_links[result.torrent_id] = await self.thirteensx_client.get_magnet_link(result.torrent_id)
                elif result.source == TorrentSource.NNMCLUB:
                    magnet_links[result.torrent_id] = await self.nnmclub_client.get_magnet_link(result.torrent_id)
        
        asyncio.run(fetch_async())
        
        return magnet_links
