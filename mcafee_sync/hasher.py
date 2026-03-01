"""Hash verification for downloaded files."""

import hashlib
import os
from typing import Optional
import requests


class HashVerifier:
    """Verify file integrity using MD5 hashes."""
    
    def __init__(self, chunk_size: int = 8192):
        self.chunk_size = chunk_size
    
    def calculate_file_hash(self, filepath: str) -> str:
        """
        Calculate MD5 hash of a file using streaming.
        Memory-efficient for large files.
        """
        hasher = hashlib.md5()
        
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
        
        return hasher.hexdigest()
    
    def get_remote_hash(self, session: requests.Session, url: str,
                        timeout: int = 30, proxy: Optional[dict] = None) -> Optional[str]:
        """
        Get MD5 hash from remote server via ETag header.
        Returns None if ETag not available.
        """
        try:
            response = session.head(url, proxies=proxy, timeout=timeout)
            response.raise_for_status()
            
            etag = response.headers.get('ETag', '')
            if not etag:
                return None
            
            # ETag format: "abc123" or W/"abc123" or "abc123:version"
            # Extract hash part
            etag = etag.strip('W/').strip('"')
            if ':' in etag:
                etag = etag.split(':')[0]
            
            return etag if len(etag) == 32 else None
            
        except requests.RequestException:
            return None
    
    def verify(self, session: requests.Session, local_path: str, 
               remote_url: str, timeout: int = 30,
               proxy: Optional[dict] = None) -> Tuple[bool, str]:
        """
        Verify local file matches remote.
        Returns (is_valid, status_message).
        """
        if not os.path.exists(local_path):
            return False, "File not found locally"
        
        local_hash = self.calculate_file_hash(local_path)
        remote_hash = self.get_remote_hash(session, remote_url, timeout, proxy)
        
        if remote_hash is None:
            return True, "No remote hash available, assuming valid"
        
        if local_hash == remote_hash:
            return True, f"Hash match: {local_hash}"
        else:
            return False, f"Hash mismatch: local={local_hash}, remote={remote_hash}"


from typing import Tuple
