"""HTTP directory crawler for discovering files."""

import requests
from bs4 import BeautifulSoup
from typing import List, Tuple, Optional
from urllib.parse import urljoin


class DirectoryCrawler:
    """Crawl HTTP directory structures recursively."""
    
    def __init__(self, session: requests.Session, timeout: int = 30, 
                 proxy: Optional[dict] = None):
        self.session = session
        self.timeout = timeout
        self.proxy = proxy
    
    def crawl(self, base_url: str) -> List[str]:
        """
        Recursively crawl directory structure starting from base_url.
        Returns list of file URLs (not directories).
        """
        discovered_files = []
        urls_to_process = [base_url]
        processed_urls = set()
        
        while urls_to_process:
            current_url = urls_to_process.pop(0)
            
            if current_url in processed_urls:
                continue
            processed_urls.add(current_url)
            
            # Fetch and parse directory listing
            links = self._fetch_directory(current_url)
            
            for link in links:
                full_url = urljoin(current_url, link)
                
                # If it's a directory, add to queue
                if link.endswith('/'):
                    if full_url not in processed_urls:
                        urls_to_process.append(full_url)
                else:
                    # It's a file
                    discovered_files.append(full_url)
        
        return discovered_files
    
    def _fetch_directory(self, url: str) -> List[str]:
        """Fetch directory listing and extract links."""
        try:
            response = self.session.get(
                url, 
                proxies=self.proxy, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._extract_links(soup)
            
        except requests.RequestException as e:
            raise CrawlerError(f"Failed to fetch {url}: {e}")
    
    def _extract_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract relevant links from HTML, filtering out junk."""
        links = []
        
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            
            # Skip navigation and query links
            if '?' in href or href in ('../', '..', '/'):
                continue
            
            # Skip sorting links (typically have query params we already filtered)
            if href.startswith('?'):
                continue
            
            links.append(href)
        
        return links


class CrawlerError(Exception):
    """Error during directory crawling."""
    pass
