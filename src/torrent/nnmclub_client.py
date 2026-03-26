"""
nnmclub.to torrent client

No authentication required
"""

import logging
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup


from .models import TorrentSearchResult, TorrentSource


logger = logging.getLogger(__name__)


class NNMClubClient:
    """Client for nnmclub.to"""
    
    BASE_URL = "https://nnmclub.to"
    
    def __init__(self):
        """Initialize NNMClub client"""
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def search(self, query: str, limit: int = 10) -> list[TorrentSearchResult]:
        """
        Search for torrents
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of TorrentSearchResult
        """
        torrents = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Search URL
                search_url = f"{self.BASE_URL}/forum/tracker.php?search={query}"
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                async with session.get(search_url, headers=headers) as response:
                    if response.status != 200:
                        logger.warning(f"NNMClub search failed: {response.status}")
                        return []
                    
                    html = await response.text('windows-1251')  # NNMClub uses windows-1251 encoding
                    torrents = self._parse_search_results(html, limit)
            
            logger.info(f"NNMClub search '{query}' found {len(torrents)} results")
            return torrents
            
        except Exception as e:
            logger.error(f"NNMClub search error: {e}")
            return []
    
    def _parse_search_results(self, html: str, limit: int) -> list[TorrentSearchResult]:
        """Parse search results HTML"""
        torrents = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find table with results
        table = soup.find('table', class_='forumline')
        if not table:
            return []
        
        rows = table.find_all('tr', class_='row1')[:limit]
        
        for row in rows:
            try:
                # Find title link
                title_link = row.find('a', class_='genmed')
                if not title_link:
                    continue
                
                title = title_link.text.strip()
                
                # Extract torrent ID from URL
                href = title_link.get('href', '')
                torrent_id = href.split('=')[1] if 't=' in href else ''
                
                # Get size from row
                size_match = re.search(r'(\d+\.\d+\s*[KMGT]B)', row.text)
                size = size_match.group(0) if size_match else ""
                
                # Seeds and leeches
                seeds_match = re.search(r'\[(\d+)\]', row.text)
                seeds = int(seeds_match.group(1)) if seeds_match else None
                
                torrent = TorrentSearchResult(
                    title=title,
                    source=TorrentSource.NNMCLUB,
                    torrent_id=torrent_id,
                    size=size,
                    seeds=seeds,
                    url=f"{self.BASE_URL}/forum/{href}" if href else None
                )
                torrents.append(torrent)
                
            except Exception as e:
                logger.debug(f"Failed to parse NNMClub row: {e}")
                continue
        
        return torrents
    
    async def get_magnet_link(self, torrent_id: str) -> Optional[str]:
        """
        Get magnet link for torrent
        
        Args:
            torrent_id: Torrent ID
            
        Returns:
            Magnet link or None
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}/forum/viewtopic.php?t={torrent_id}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        return None
                    
                    html = await response.text('windows-1251')
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find download link
                    download_link = soup.find('a', href=lambda x: x and 'download.php' in x)
                    if download_link:
                        # NNMClub doesn't have direct magnet, return download URL
                        return f"{self.BASE_URL}/forum/{download_link.get('href')}"
                        
        except Exception as e:
            logger.error(f"Failed to get NNMClub magnet link: {e}")
        
        return None
