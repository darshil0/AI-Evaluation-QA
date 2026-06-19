"""
Unit tests for rate limiter.
"""

import pytest
import asyncio
from datetime import datetime
from evaluation.rate_limiter import RateLimiter


@pytest.mark.asyncio
class TestRateLimiter:
    """Test rate limiter functionality."""

    async def test_basic_rate_limiting(self):
        """Test basic rate limiting works."""
        limiter = RateLimiter(calls_per_minute=5)

        # Should allow 5 calls immediately
        for _ in range(5):
            async with limiter:
                pass

        # Check stats
        stats = limiter.get_stats()
        assert stats["calls_last_minute"] == 5
        assert stats["calls_per_minute_limit"] == 5

    async def test_rate_limit_blocks_excess(self):
        """Test that rate limiter blocks excess calls."""
        limiter = RateLimiter(calls_per_minute=2)

        start_time = datetime.now()

        # Make 3 calls (3rd should be delayed)
        for i in range(3):
            async with limiter:
                if i == 2:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    # Third call should be delayed
                    assert elapsed > 0.1

    async def test_concurrent_access(self):
        """Test rate limiter handles concurrent access."""
        limiter = RateLimiter(calls_per_minute=10)

        async def make_call(call_id):
            async with limiter:
                return call_id

        # Make 10 concurrent calls
        results = await asyncio.gather(*[make_call(i) for i in range(10)])

        assert len(results) == 10
        assert limiter.get_stats()["calls_last_minute"] == 10
