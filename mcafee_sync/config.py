"""Configuration management for McAfee Sync."""

import os
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class Config:
    """Application configuration."""
    
    # Source/Destination
    source_path: str = "http://update.nai.com/products/commonupdater/"
    destination_path: str = "./downloads"
    
    # HTTP Settings
    proxy: Optional[Dict[str, str]] = None
    http_timeout: int = 30
    max_retries: int = 3
    
    # Worker Settings
    mode: str = "thread"  # single, thread, async
    workers: int = 0  # 0 = auto (cpu_count * 4)
    
    # Rate Limiting (bytes per second, 0 = unlimited)
    rate_limit: int = 0
    
    # Retention
    retention_days: float = 7.0
    log_retention_days: float = 30.0
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "text"  # text, json
    log_dir: str = "logs"
    
    # Behavior
    dry_run: bool = False
    resume: bool = True
    verify_ssl: bool = True
    chunk_size: int = 8192
    
    # Progress display
    show_progress: bool = True
    
    def __post_init__(self):
        """Validate and normalize configuration."""
        if self.workers == 0:
            self.workers = (os.cpu_count() or 4) * 4
        
        if self.mode not in ("single", "thread", "async"):
            raise ValueError(f"Invalid mode: {self.mode}")
        
        # Ensure proxy is dict if provided
        if isinstance(self.proxy, str):
            self.proxy = {"http": self.proxy, "https": self.proxy}
    
    @classmethod
    def from_file(cls, filepath: str) -> "Config":
        """Load configuration from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        def get_env(key, default=None, type_func=str):
            val = os.environ.get(f"MCAFEE_SYNC_{key}", default)
            if val is not None and type_func != str:
                val = type_func(val)
            return val
        
        return cls(
            source_path=get_env("SOURCE_PATH", cls.source_path),
            destination_path=get_env("DEST_PATH", cls.destination_path),
            mode=get_env("MODE", cls.mode),
            workers=get_env("WORKERS", cls.workers, int),
            rate_limit=get_env("RATE_LIMIT", cls.rate_limit, int),
            retention_days=get_env("RETENTION_DAYS", cls.retention_days, float),
            log_level=get_env("LOG_LEVEL", cls.log_level),
            dry_run=get_env("DRY_RUN", cls.dry_run, lambda x: x.lower() == "true"),
        )
    
    def to_file(self, filepath: str):
        """Save configuration to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.__dict__, f, indent=2)
