"""
1337x.to torrent client

No authentication required
"""

import logging
import re
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup


from .models import TorrentSearchResult, TorrentSource


logger = logging.getLogger(__name__)


class ThirteenXClient:
    """Client for 1337x.to"""
    
    BASE_URL = "https://www.1337x.to"
    
    def __init__(self):
        """Initialize 1337x client"""
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
                search_url = f"{self.BASE_URL}/search/{query}/1/"
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                async with session.get(search_url, headers=headers) as response:
                    if response.status != 200:
                        logger.warning(f"1337x search failed: {response.status}")
                        return []
                    
                    html = await response.text()
                    torrents = self._parse_search_results(html, limit)
            
            logger.info(f"1337x search '{query}' found {len(torrents)} results")
            return torrents
            
        except Exception as e:
            logger.error(f"1337x search error: {e}")
            return []
    
    def _parse_search_results(self, html: str, limit: int) -> list[TorrentSearchResult]:
        """Parse search results HTML"""
        torrents = []
        soup = BeautifulSoup(html, 'html.parser')
        
        table = soup.find('table', class_='table-list')
        if not table:
            return []
        
        rows = table.find('tbody').find_all('tr')[:limit]
        
        for row in rows:
            try:
                title_cell = row.find('td', class_='coll-1 name')
                if not title_cell:
                    continue
                
                title_link = title_cell.find('a')
                title = title_link.text.strip() if title_link else ""
                
                # Extract torrent ID from URL
                href = title_link.get('href', '') if title_link else ''
                torrent_id = href.split('/')[2] if '/torrent/' in href else ''
                
                # Get size, seeds, leeches
                size_cell = row.find_all('td', class_='coll-4')
                size = size_cell[0].text.strip() if size_cell else ""
                
                seeds_cell = row.find_all('td', class_='coll-2')
                seeds = int(seeds_cell[0].text.strip().replace(',', '')) if seeds_cell and seeds_cell[0].text.strip().isdigit() else None
                
                leeches_cell = row.find_all('td', class_='coll-3')
                leeches = int(leeches_cell[0].text.strip().replace(',', '')) if leeches_cell and leeches_cell[0].text.strip().isdigit() else None
                
                # Uploader
                uploader_cell = row.find('td', class_='coll-2')
                uploader = uploader_cell.find('a').text.strip() if uploader_cell and uploader_cell.find('a') else ""
                
                torrent = TorrentSearchResult(
                    title=title,
                    source=TorrentSource.THIRTEEN_X,
                    torrent_id=torrent_id,
                    size=size,
                    seeds=seeds,
                    leeches=leeches,
                    uploader=uploader,
                    url=f"{self.BASE_URL}{href}" if href else None
                )
                torrents.append(torrent)
                
            except Exception as e:
                logger.debug(f"Failed to parse 1337x row: {e}")
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
                url = f"{self.BASE_URL}/torrent/{torrent_id}/"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        return None
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find magnet link
                    magnet_link = soup.find('a', href=lambda x: x and x.startswith('magnet:'))
                    if magnet_link:
                        return magnet_link.get('href')
                        
        except Exception as e:
            logger.error(f"Failed to get 1337x magnet link: {e}")
        
        return None
