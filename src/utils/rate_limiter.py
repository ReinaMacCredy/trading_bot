import asyncio
import time
import logging
from asyncio import Semaphore
from collections import deque

logger = logging.getLogger('rate_limiter')

class RateLimiter:
    """Rate limiter for API calls to prevent throttling"""
    
    def __init__(self, max_requests=10, per_seconds=60):
        """
        Initialize a rate limiter
        
        Args:
            max_requests: Maximum number of requests allowed in the time window
            per_seconds: Time window in seconds
        """
        self.semaphore = Semaphore(max_requests)
        self.requests = deque(maxlen=max_requests)
        self.per_seconds = per_seconds
        logger.debug(f"Rate limiter initialized: {max_requests} requests per {per_seconds} seconds")
    
    async def acquire(self):
        """
        Acquire permission to make a request
        
        Returns:
            A context manager that releases the semaphore when done
        """
        # Clean up old requests
        now = time.time()
        while self.requests and now - self.requests[0] > self.per_seconds:
            self.requests.popleft()
        
        # If we've hit the limit, wait until we have capacity
        if len(self.requests) >= self.semaphore._value:
            wait_time = self.per_seconds - (now - self.requests[0])
            if wait_time > 0:
                logger.debug(f"Rate limit hit, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
        
        # Acquire semaphore and record request time
        await self.semaphore.acquire()
        self.requests.append(time.time())
        
        class ReleaseContext:
            def __init__(self, semaphore):
                self.semaphore = semaphore
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                self.semaphore.release()
        
        return ReleaseContext(self.semaphore)
    
    def release(self):
        """Release a request slot"""
        self.semaphore.release()


class SyncRateLimiter:
    """Synchronous version of the rate limiter for non-async code"""
    
    def __init__(self, max_requests=10, per_seconds=60):
        """
        Initialize a rate limiter
        
        Args:
            max_requests: Maximum number of requests allowed in the time window
            per_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.per_seconds = per_seconds
        self.requests = deque(maxlen=max_requests)
        logger.debug(f"Sync rate limiter initialized: {max_requests} requests per {per_seconds} seconds")
    
    def acquire(self):
        """
        Acquire permission to make a request (blocking)
        """
        # Clean up old requests
        now = time.time()
        while self.requests and now - self.requests[0] > self.per_seconds:
            self.requests.popleft()
        
        # If we've hit the limit, wait until we have capacity
        if len(self.requests) >= self.max_requests:
            wait_time = self.per_seconds - (now - self.requests[0])
            if wait_time > 0:
                logger.debug(f"Rate limit hit, waiting {wait_time:.2f}s")
                time.sleep(wait_time)
        
        # Record request time
        self.requests.append(time.time()) 