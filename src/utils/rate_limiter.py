import asyncio
import time
from collections import deque
import logging
import heapq

logger = logging.getLogger(__name__)

class MultiKeyRateLimiter:
    def __init__(self, keys, rate_limit_per_key):
        logger.info(f"Initializing MultiKeyRateLimiter with {len(keys)} keys")
        self.limiters = {key: RateLimiter(rate_limit_per_key) for key in keys}
        self.key_heap = [(0, key) for key in keys]
        heapq.heapify(self.key_heap)
        self.lock = asyncio.Lock()
        logger.info("MultiKeyRateLimiter initialized successfully")

    async def acquire(self):
        async with self.lock:
            while True:
                now = time.monotonic()
                next_available, key = self.key_heap[0]
                if now >= next_available:
                    next_time = self.limiters[key].update(now)
                    heapq.heapreplace(self.key_heap, (next_time, key))
                    return key
                await asyncio.sleep(next_available - now)

class RateLimiter:
    def __init__(self, rate_limit):
        self.rate_limit = rate_limit
        self.last_check = time.monotonic()
        self.allowance = rate_limit

    def update(self, current):
        time_passed = current - self.last_check
        self.last_check = current
        self.allowance += time_passed * self.rate_limit
        if self.allowance > self.rate_limit:
            self.allowance = self.rate_limit
        if self.allowance < 1:
            return current + (1 - self.allowance) / self.rate_limit
        self.allowance -= 1
        return current