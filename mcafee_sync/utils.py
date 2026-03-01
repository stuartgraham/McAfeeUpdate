"""Utility functions for McAfee Sync."""

import os
import sys
import time
import logging
import json
from typing import Optional
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""
    
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "worker_id"):
            log_data["worker_id"] = record.worker_id
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def setup_logging(config) -> logging.Logger:
    """Setup logging with file and console handlers."""
    
    # Create logs directory
    os.makedirs(config.log_dir, exist_ok=True)
    
    logger = logging.getLogger("mcafee_sync")
    logger.setLevel(getattr(logging, config.log_level.upper()))
    logger.handlers = []  # Clear existing handlers
    
    # File handler
    log_file = os.path.join(
        config.log_dir,
        f"sync_{time.strftime('%Y%m%d_%H%M%S')}.log"
    )
    file_handler = logging.FileHandler(log_file)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Formatters
    if config.log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def timecalc(timestamp) -> float:
    """Calculate days since file creation."""
    createsecs = timestamp.st_ctime
    currentsecs = time.time()
    deltasecs = currentsecs - createsecs
    return round(deltasecs / 86400, 3)


def ensure_dir(path: str) -> bool:
    """Ensure directory exists, return True if created."""
    if not os.path.exists(path):
        os.makedirs(path)
        return True
    return False


def safe_path_join(*parts: str) -> str:
    """Safely join path components."""
    return os.path.normpath(os.path.join(*parts))


def parse_size(size_str: str) -> int:
    """Parse size string like '10MB' to bytes."""
    units = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
    size_str = size_str.upper().strip()
    
    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            return int(float(size_str[:-len(unit)]) * multiplier)
    
    return int(size_str)


class RateLimiter:
    """Simple token bucket rate limiter."""
    
    def __init__(self, rate_bytes_per_sec: int):
        self.rate = rate_bytes_per_sec
        self.tokens = rate_bytes_per_sec
        self.last_update = time.time()
    
    def acquire(self, tokens: int):
        """Acquire tokens, blocking if necessary."""
        if self.rate == 0:
            return
        
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
        self.last_update = now
        
        if tokens > self.tokens:
            sleep_time = (tokens - self.tokens) / self.rate
            time.sleep(sleep_time)
            self.tokens = 0
        else:
            self.tokens -= tokens


class ProgressTracker:
    """Track and display download progress."""
    
    def __init__(self, total: int, show: bool = True):
        self.total = total
        self.current = 0
        self.show = show
        self.start_time = time.time()
    
    def update(self, increment: int = 1):
        """Update progress."""
        self.current += increment
        if self.show:
            self._display()
    
    def _display(self):
        """Display progress bar."""
        if self.total == 0:
            return
        
        percent = (self.current / self.total) * 100
        elapsed = time.time() - self.start_time
        rate = self.current / elapsed if elapsed > 0 else 0
        
        bar_length = 40
        filled = int(bar_length * self.current / self.total)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        sys.stdout.write(
            f'\r|{bar}| {percent:.1f}% ({self.current}/{self.total}) '
            f'{rate:.1f} items/sec'
        )
        sys.stdout.flush()
    
    def finish(self):
        """Complete the progress display."""
        if self.show:
            self._display()
            sys.stdout.write('\n')
