"""Worker pools for concurrent execution."""

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Any, Optional
from queue import Queue
from threading import Thread
import time


class ThreadWorkerPool:
    """Thread-based worker pool for I/O bound tasks."""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def map(self, func: Callable, items: List[Any], 
            callback: Optional[Callable] = None) -> List[Any]:
        """
        Execute func on all items in parallel.
        Optional callback called after each completion.
        """
        futures = {self.executor.submit(func, item): item for item in items}
        results = []
        
        for future in as_completed(futures):
            item = futures[future]
            try:
                result = future.result()
                results.append((item, result, None))
                if callback:
                    callback(item, result, None)
            except Exception as e:
                results.append((item, None, e))
                if callback:
                    callback(item, None, e)
        
        return results
    
    def shutdown(self):
        """Clean shutdown of worker pool."""
        self.executor.shutdown(wait=True)


class AsyncWorkerPool:
    """Async/await based worker pool for high-concurrency I/O."""
    
    def __init__(self, max_workers: int = 100):
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)
    
    async def map(self, func: Callable, items: List[Any],
                  callback: Optional[Callable] = None) -> List[Any]:
        """
        Execute async func on all items with concurrency limit.
        """
        tasks = [self._run_with_limit(func, item, callback) for item in items]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _run_with_limit(self, func: Callable, item: Any,
                              callback: Optional[Callable]):
        """Run function with semaphore limit."""
        async with self.semaphore:
            try:
                result = await func(item)
                if callback:
                    callback(item, result, None)
                return (item, result, None)
            except Exception as e:
                if callback:
                    callback(item, None, e)
                return (item, None, e)


class SingleWorker:
    """Sequential execution for single-threaded mode."""
    
    def map(self, func: Callable, items: List[Any],
            callback: Optional[Callable] = None) -> List[Any]:
        """Execute func on all items sequentially."""
        results = []
        
        for item in items:
            try:
                result = func(item)
                results.append((item, result, None))
                if callback:
                    callback(item, result, None)
            except Exception as e:
                results.append((item, None, e))
                if callback:
                    callback(item, None, e)
        
        return results
    
    def shutdown(self):
        """No-op for single worker."""
        pass
