import asyncio
import time
from collections import deque
import logging

logger = logging.getLogger(__name__)

class MultiKeyRateLimiter:
    def __init__(self, keys, rate_limit_per_key):
        if not isinstance(keys, list):
            keys = list(keys)
        logger.info(f"Initializing MultiKeyRateLimiter with {len(keys)} keys")
        self.limiters = {key: RateLimiter(rate_limit_per_key) for key in keys}
        self.key_queue = deque(keys)
        logger.info("MultiKeyRateLimiter initialized successfully")

    async def acquire(self):
        while True:
            key = self.key_queue[0]
            if await self.limiters[key].try_acquire():
                self.key_queue.rotate(-1)
                return key
            await asyncio.sleep(0.01)

class RateLimiter:
    def __init__(self, rate_limit):
        self.rate_limit = rate_limit
        self.tokens = rate_limit
        self.updated_at = time.monotonic()

    async def try_acquire(self):
        now = time.monotonic()
        time_passed = now - self.updated_at
        self.tokens += time_passed * self.rate_limit
        if self.tokens > self.rate_limit:
            self.tokens = self.rate_limit
        self.updated_at = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False