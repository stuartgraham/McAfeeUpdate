"""Command-line interface for McAfee Sync."""

import argparse
import sys
from typing import Optional

from .config import Config
from .utils import parse_size


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog='mcafee-sync',
        description='Synchronize HTTP directory structures with local storage',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --source http://example.com/files --dest ./downloads
  %(prog)s --mode=async --workers=50 --rate-limit=10MB/s
  %(prog)s --dry-run --mode=single  # Preview what would be downloaded
  
Environment Variables:
  MCAFEE_SYNC_SOURCE_PATH     Source URL
  MCAFEE_SYNC_DEST_PATH       Destination directory
  MCAFEE_SYNC_MODE            Execution mode (single/thread/async)
  MCAFEE_SYNC_WORKERS         Number of workers
  MCAFEE_SYNC_RATE_LIMIT      Bandwidth limit (e.g., 10MB/s)
        """
    )
    
    # Source/Destination
    parser.add_argument(
        '-s', '--source',
        default=None,
        help='Source URL to synchronize from'
    )
    parser.add_argument(
        '-d', '--dest', '--destination',
        dest='destination_path',
        default=None,
        help='Destination directory for downloads'
    )
    
    # Execution mode
    parser.add_argument(
        '-m', '--mode',
        choices=['single', 'thread', 'async'],
        default=None,
        help='Execution mode (default: thread)'
    )
    parser.add_argument(
        '-w', '--workers',
        type=int,
        default=None,
        help='Number of workers (default: CPU count * 4)'
    )
    
    # Rate limiting
    parser.add_argument(
        '--rate-limit',
        default=None,
        help='Bandwidth limit (e.g., 1MB/s, 500KB/s, 0=unlimited)'
    )
    
    # Retention
    parser.add_argument(
        '--retention-days',
        type=float,
        default=None,
        help='Days to keep files (default: 7)'
    )
    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Skip cleanup of old files'
    )
    
    # Behavior
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be downloaded without downloading'
    )
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='Do not resume partial downloads'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=8192,
        help='Download chunk size in bytes (default: 8192)'
    )
    
    # Network
    parser.add_argument(
        '--proxy',
        default=None,
        help='HTTP proxy URL'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='HTTP timeout in seconds (default: 30)'
    )
    parser.add_argument(
        '--retries',
        type=int,
        default=3,
        help='Number of retry attempts (default: 3)'
    )
    
    # Logging
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=None,
        help='Log level (default: INFO)'
    )
    parser.add_argument(
        '--log-format',
        choices=['text', 'json'],
        default=None,
        help='Log format (default: text)'
    )
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress bar'
    )
    
    # Config file
    parser.add_argument(
        '-c', '--config',
        default=None,
        help='Path to configuration JSON file'
    )
    parser.add_argument(
        '--save-config',
        default=None,
        help='Save current settings to JSON file'
    )
    
    # Info
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 2.0.0'
    )
    
    return parser


def config_from_args(args: argparse.Namespace) -> Config:
    """Build Config from CLI arguments."""
    
    # Start with defaults
    config = Config()
    
    # Override with config file if provided
    if args.config:
        config = Config.from_file(args.config)
    
    # Override with environment variables
    env_config = Config.from_env()
    for key, value in env_config.__dict__.items():
        if value != getattr(Config(), key):
            setattr(config, key, value)
    
    # Override with CLI arguments
    if args.source:
        config.source_path = args.source
    if args.destination_path:
        config.destination_path = args.destination_path
    if args.mode:
        config.mode = args.mode
    if args.workers is not None:
        config.workers = args.workers
    if args.rate_limit:
        config.rate_limit = parse_size(args.rate_limit.replace('/s', ''))
    if args.retention_days is not None:
        config.retention_days = args.retention_days
    if args.no_cleanup:
        config.retention_days = float('inf')
    if args.dry_run:
        config.dry_run = True
    if args.no_resume:
        config.resume = False
    if args.chunk_size:
        config.chunk_size = args.chunk_size
    if args.proxy:
        config.proxy = {"http": args.proxy, "https": args.proxy}
    if args.timeout:
        config.http_timeout = args.timeout
    if args.retries:
        config.max_retries = args.retries
    if args.log_level:
        config.log_level = args.log_level
    if args.log_format:
        config.log_format = args.log_format
    if args.no_progress:
        config.show_progress = False
    
    return config
