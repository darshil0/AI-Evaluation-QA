"""
Rate limiting utilities for API calls.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    Prevents race conditions in concurrent API requests.
    """

    def __init__(self, calls_per_minute: int = 60):
        """
        Initialize rate limiter.

        Args:
            calls_per_minute: Maximum number of calls allowed per minute
        """
        self.calls_per_minute = calls_per_minute
        self.call_times: List[datetime] = []
        self.lock = asyncio.Lock()
        logger.info(f"Rate limiter initialized: {calls_per_minute} calls/min")

    async def acquire(self):
        """Acquire rate limit token with backpressure."""
        async with self.lock:
            now = datetime.now()

            # Remove calls older than 1 minute
            cutoff = now - timedelta(minutes=1)
            self.call_times = [t for t in self.call_times if t > cutoff]

            # Wait if we've hit the limit
            if len(self.call_times) >= self.calls_per_minute:
                oldest_call = self.call_times[0]
                sleep_time = 61 - (now - oldest_call).total_seconds()

                if sleep_time > 0:
                    logger.warning(f"Rate limit reached. Waiting {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
                    return await self.acquire()

            self.call_times.append(now)

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, *args):
        pass

    def get_stats(self) -> dict:
        """Get current rate limiter statistics."""
        now = datetime.now()
        recent_calls = [t for t in self.call_times if now - t < timedelta(minutes=1)]

        return {
            "calls_last_minute": len(recent_calls),
            "calls_per_minute_limit": self.calls_per_minute,
            "utilization_percent": (len(recent_calls) / self.calls_per_minute) * 100,
        }
