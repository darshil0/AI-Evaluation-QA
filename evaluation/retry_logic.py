"""
Exponential backoff retry logic for API calls.
"""

import asyncio
import functools
import logging
import time
from typing import Callable, Tuple, Type

logger = logging.getLogger(__name__)

# Define retriable errors (to be imported from actual SDKs)
RETRIABLE_ERRORS = (
    ConnectionError,
    TimeoutError,
    # Add actual SDK errors when available:
    # openai.error.RateLimitError,
    # openai.error.APIError,
    # anthropic.RateLimitError,
)


def exponential_backoff_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retriable_errors: Tuple[Type[Exception], ...] = RETRIABLE_ERRORS,
):
    """
    Decorator for exponential backoff retry logic.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        retriable_errors: Tuple of exception types that trigger retry

    Example:
        @exponential_backoff_retry(max_retries=3)
        async def call_api():
            return await api.complete(prompt)
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)

                except retriable_errors as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(f"Max retries ({max_retries}) reached for {func.__name__}")
                        raise

                    delay = min(base_delay * (exponential_base**attempt), max_delay)

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed "
                        f"for {func.__name__}: {str(e)}"
                    )
                    logger.info(f"Retrying in {delay:.2f} seconds...")

                    await asyncio.sleep(delay)

            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except retriable_errors as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(f"Max retries ({max_retries}) reached for {func.__name__}")
                        raise

                    delay = min(base_delay * (exponential_base**attempt), max_delay)

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed "
                        f"for {func.__name__}: {str(e)}"
                    )
                    logger.info(f"Retrying in {delay:.2f} seconds...")

                    time.sleep(delay)

            raise last_exception

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
