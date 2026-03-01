"""Main entry point for McAfee Sync."""

import sys
import time
import requests
import aiohttp
import asyncio
from typing import List

from .config import Config
from .cli import create_parser, config_from_args
from .utils import setup_logging, timecalc, ProgressTracker
from .crawler import DirectoryCrawler
from .downloader import DownloadTask, SyncDownloader, AsyncDownloader
from .workers import ThreadWorkerPool, AsyncWorkerPool, SingleWorker


def cleanup_old_files(config: Config, logger, rootdir: str, retention: float):
    """Remove files and directories older than retention days."""
    import os
    
    logger.info("Starting cleanup for: %s (retention: %.1f days)", rootdir, retention)
    
    files_deleted = 0
    dirs_deleted = 0
    
    for root, dirs, files in os.walk(rootdir, topdown=False):
        # Delete old files
        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                age_days = timecalc(os.stat(filepath))
                if age_days > retention:
                    if not config.dry_run:
                        os.remove(filepath)
                    logger.info("Deleted: %s (%.1f days old)%s", 
                              filepath, age_days,
                              " [DRY-RUN]" if config.dry_run else "")
                    files_deleted += 1
                else:
                    logger.debug("Kept: %s (%.1f days old)", filepath, age_days)
            except OSError as e:
                logger.error("Failed to delete %s: %s", filepath, e)
        
        # Remove empty directories
        for dirname in dirs:
            dirpath = os.path.join(root, dirname)
            try:
                if not os.listdir(dirpath):
                    if not config.dry_run:
                        os.rmdir(dirpath)
                    logger.info("Removed empty dir: %s%s",
                              dirpath,
                              " [DRY-RUN]" if config.dry_run else "")
                    dirs_deleted += 1
            except OSError:
                pass
    
    logger.info("Cleanup complete: %d files, %d directories removed", 
                files_deleted, dirs_deleted)
    return files_deleted, dirs_deleted


def run_single_mode(config: Config, logger, tasks: List[DownloadTask]) -> dict:
    """Run downloads in single-threaded mode."""
    session = requests.Session()
    downloader = SyncDownloader(session, config, logger)
    worker = SingleWorker()
    
    results = worker.map(downloader.download, tasks)
    
    session.close()
    
    success = sum(1 for _, _, err in results if err is None)
    return {'success': success, 'failed': len(results) - success}


def run_thread_mode(config: Config, logger, tasks: List[DownloadTask]) -> dict:
    """Run downloads in multi-threaded mode."""
    session = requests.Session()
    downloader = SyncDownloader(session, config, logger)
    pool = ThreadWorkerPool(max_workers=config.workers)
    
    def progress_callback(task, result, error):
        if config.show_progress:
            progress.update(1)
    
    if config.show_progress:
        progress = ProgressTracker(len(tasks))
    
    results = pool.map(downloader.download, tasks, progress_callback)
    
    pool.shutdown()
    session.close()
    
    if config.show_progress:
        progress.finish()
    
    success = sum(1 for _, _, err in results if err is None)
    return {'success': success, 'failed': len(results) - success}


async def run_async_mode(config: Config, logger, tasks: List[DownloadTask]) -> dict:
    """Run downloads in async mode."""
    connector = aiohttp.TCPConnector(limit=config.workers)
    timeout = aiohttp.ClientTimeout(total=config.http_timeout)
    
    async with aiohttp.ClientSession(
        connector=connector, 
        timeout=timeout
    ) as session:
        downloader = AsyncDownloader(session, config, logger)
        pool = AsyncWorkerPool(max_workers=config.workers)
        
        results = await pool.map(downloader.download, tasks)
    
    success = sum(1 for _, _, err in results if err is None)
    return {'success': success, 'failed': len(results) - success}


def main(args=None):
    """Main entry point."""
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    # Build configuration
    config = config_from_args(parsed_args)
    
    # Save config if requested
    if parsed_args.save_config:
        config.to_file(parsed_args.save_config)
        print(f"Configuration saved to {parsed_args.save_config}")
        return 0
    
    # Setup logging
    logger = setup_logging(config)
    logger.info("=" * 50)
    logger.info("McAfee Sync v2.0.0 - Starting sync")
    logger.info("Source: %s", config.source_path)
    logger.info("Destination: %s", config.destination_path)
    logger.info("Mode: %s (workers: %d)", config.mode, config.workers)
    
    start_time = time.time()
    
    try:
        # Phase 1: Crawl directory structure
        logger.info("Phase 1: Discovering files...")
        session = requests.Session()
        crawler = DirectoryCrawler(
            session, 
            config.http_timeout, 
            config.proxy
        )
        urls = crawler.crawl(config.source_path)
        session.close()
        
        logger.info("Discovered %d files", len(urls))
        
        if not urls:
            logger.warning("No files found to download")
            return 0
        
        # Create download tasks
        tasks = [
            DownloadTask(url, config.destination_path, config.source_path)
            for url in urls
        ]
        
        # Phase 2: Download files
        logger.info("Phase 2: Downloading files...")
        
        if config.mode == 'single':
            stats = run_single_mode(config, logger, tasks)
        elif config.mode == 'thread':
            stats = run_thread_mode(config, logger, tasks)
        elif config.mode == 'async':
            stats = asyncio.run(run_async_mode(config, logger, tasks))
        else:
            logger.error("Unknown mode: %s", config.mode)
            return 1
        
        logger.info("Downloads complete: %d success, %d failed", 
                   stats['success'], stats['failed'])
        
        # Phase 3: Cleanup old files
        if config.retention_days < float('inf'):
            logger.info("Phase 3: Cleaning up old files...")
            cleanup_old_files(
                config, logger, 
                config.destination_path, 
                config.retention_days
            )
            
            # Cleanup old logs
            log_dir = config.log_dir
            if log_dir != config.destination_path:
                cleanup_old_files(
                    config, logger,
                    log_dir,
                    config.log_retention_days
                )
        
        elapsed = time.time() - start_time
        logger.info("=" * 50)
        logger.info("Sync completed in %.2f seconds", elapsed)
        logger.info("Files: %d success, %d failed", 
                   stats['success'], stats['failed'])
        
        return 0 if stats['failed'] == 0 else 1
        
    except KeyboardInterrupt:
        logger.info("Sync interrupted by user")
        return 130
    except Exception as e:
        logger.exception("Sync failed: %s", e)
        return 1


if __name__ == '__main__':
    sys.exit(main())
