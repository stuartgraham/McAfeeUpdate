"""File downloader with sync and async modes."""

import os
import time
import requests
import aiohttp
import aiofiles
from typing import Optional, Tuple
from urllib.parse import urlparse

from .hasher import HashVerifier
from .utils import RateLimiter, ensure_dir, safe_path_join


class DownloadTask:
    """Represents a file to download."""
    
    def __init__(self, url: str, destination_root: str, source_root: str):
        self.url = url
        self.destination_root = destination_root
        self.source_root = source_root
        self.local_path = self._compute_local_path()
        self.size = 0
        self.downloaded = 0
    
    def _compute_local_path(self) -> str:
        """Compute local file path from URL."""
        # Remove source root from URL to get relative path
        rel_path = self.url.replace(self.source_root, "").lstrip('/')
        return safe_path_join(self.destination_root, rel_path)
    
    def ensure_directory(self) -> bool:
        """Ensure parent directory exists, return True if created."""
        parent = os.path.dirname(self.local_path)
        return ensure_dir(parent)


class SyncDownloader:
    """Synchronous file downloader with retry logic."""
    
    def __init__(self, session: requests.Session, config, logger):
        self.session = session
        self.config = config
        self.logger = logger
        self.hasher = HashVerifier(config.chunk_size)
        self.rate_limiter = RateLimiter(config.rate_limit)
    
    def download(self, task: DownloadTask) -> Tuple[bool, str]:
        """
        Download a single file with verification.
        Returns (success, message).
        """
        # Check if already downloaded and valid
        if os.path.exists(task.local_path) and self.config.resume:
            is_valid, msg = self._verify(task)
            if is_valid:
                self.logger.debug("Skipping %s - already valid", task.url)
                return True, f"Skipped (valid): {msg}"
            else:
                self.logger.info("Re-downloading %s - %s", task.url, msg)
        
        if self.config.dry_run:
            self.logger.info("[DRY-RUN] Would download %s", task.url)
            return True, "Dry run"
        
        # Ensure directory exists
        created = task.ensure_directory()
        if created:
            self.logger.debug("Created directory for %s", task.local_path)
        
        # Download with retries
        for attempt in range(self.config.max_retries):
            try:
                return self._download_file(task)
            except Exception as e:
                self.logger.warning(
                    "Download failed (attempt %d/%d): %s - %s",
                    attempt + 1, self.config.max_retries, task.url, e
                )
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        return False, f"Failed after {self.config.max_retries} attempts"
    
    def _download_file(self, task: DownloadTask) -> Tuple[bool, str]:
        """Download file to disk."""
        response = self.session.get(
            task.url,
            stream=True,
            proxies=self.config.proxy,
            timeout=self.config.http_timeout
        )
        response.raise_for_status()
        
        # Get content length if available
        task.size = int(response.headers.get('content-length', 0))
        
        # Download in chunks
        with open(task.local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=self.config.chunk_size):
                if chunk:
                    f.write(chunk)
                    task.downloaded += len(chunk)
                    
                    # Rate limiting
                    self.rate_limiter.acquire(len(chunk))
        
        response.close()
        
        # Verify download
        is_valid, msg = self._verify(task)
        if is_valid:
            self.logger.info("Downloaded: %s", task.url)
            return True, msg
        else:
            os.remove(task.local_path)
            return False, f"Verification failed: {msg}"
    
    def _verify(self, task: DownloadTask) -> Tuple[bool, str]:
        """Verify downloaded file."""
        return self.hasher.verify(
            self.session, task.local_path, task.url,
            self.config.http_timeout, self.config.proxy
        )


class AsyncDownloader:
    """Asynchronous file downloader for high concurrency."""
    
    def __init__(self, session: aiohttp.ClientSession, config, logger):
        self.session = session
        self.config = config
        self.logger = logger
        self.rate_limiter = RateLimiter(config.rate_limit)
    
    async def download(self, task: DownloadTask) -> Tuple[bool, str]:
        """Download a single file asynchronously."""
        # Check if already downloaded and valid
        if os.path.exists(task.local_path) and self.config.resume:
            is_valid, msg = await self._verify(task)
            if is_valid:
                self.logger.debug("Skipping %s - already valid", task.url)
                return True, f"Skipped (valid): {msg}"
            else:
                self.logger.info("Re-downloading %s - %s", task.url, msg)
        
        if self.config.dry_run:
            self.logger.info("[DRY-RUN] Would download %s", task.url)
            return True, "Dry run"
        
        # Ensure directory exists
        created = task.ensure_directory()
        if created:
            self.logger.debug("Created directory for %s", task.local_path)
        
        # Download with retries
        for attempt in range(self.config.max_retries):
            try:
                return await self._download_file(task)
            except Exception as e:
                self.logger.warning(
                    "Download failed (attempt %d/%d): %s - %s",
                    attempt + 1, self.config.max_retries, task.url, e
                )
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        return False, f"Failed after {self.config.max_retries} attempts"
    
    async def _download_file(self, task: DownloadTask) -> Tuple[bool, str]:
        """Download file asynchronously."""
        import asyncio
        
        async with self.session.get(task.url) as response:
            response.raise_for_status()
            
            async with aiofiles.open(task.local_path, 'wb') as f:
                async for chunk in response.content.iter_chunked(self.config.chunk_size):
                    await f.write(chunk)
                    task.downloaded += len(chunk)
                    
                    # Rate limiting (convert to sync for simplicity)
                    self.rate_limiter.acquire(len(chunk))
        
        # Verify download (using sync hasher since file ops are sync)
        hasher = HashVerifier(self.config.chunk_size)
        local_hash = hasher.calculate_file_hash(task.local_path)
        
        # Get remote hash via HEAD request
        try:
            async with self.session.head(task.url) as resp:
                etag = resp.headers.get('ETag', '')
                if etag:
                    remote_hash = etag.strip('W/').strip('"').split(':')[0]
                    if len(remote_hash) == 32 and local_hash == remote_hash:
                        self.logger.info("Downloaded: %s", task.url)
                        return True, f"Hash match: {local_hash}"
                    else:
                        os.remove(task.local_path)
                        return False, f"Hash mismatch"
        except:
            pass
        
        self.logger.info("Downloaded: %s", task.url)
        return True, "Download complete"
    
    async def _verify(self, task: DownloadTask) -> Tuple[bool, str]:
        """Verify file asynchronously."""
        hasher = HashVerifier(self.config.chunk_size)
        local_hash = hasher.calculate_file_hash(task.local_path)
        
        try:
            async with self.session.head(task.url) as resp:
                etag = resp.headers.get('ETag', '')
                if etag:
                    remote_hash = etag.strip('W/').strip('"').split(':')[0]
                    if len(remote_hash) == 32:
                        if local_hash == remote_hash:
                            return True, f"Hash match: {local_hash}"
                        else:
                            return False, f"Hash mismatch"
        except:
            pass
        
        return True, "No remote hash available"
