"""
Exponential backoff retry logic for API calls.
"""

import asyncio
import functools
import inspect
import logging
import time
from typing import Any, Callable, Tuple, Type, TypeVar

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

T = TypeVar("T")


def exponential_backoff_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retriable_errors: Tuple[Type[Exception], ...] = RETRIABLE_ERRORS,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
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

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_retries + 1):  # pragma: no cover
                try:
                    return await func(*args, **kwargs)  # pragma: no cover

                except retriable_errors as e:
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

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_retries + 1):  # pragma: no cover
                try:
                    return func(*args, **kwargs)

                except retriable_errors as e:
                    if attempt == max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) reached for {func.__name__}"
                        )  # pragma: no cover
                        raise

                    delay = min(base_delay * (exponential_base**attempt), max_delay)

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed "
                        f"for {func.__name__}: {str(e)}"
                    )
                    logger.info(f"Retrying in {delay:.2f} seconds...")

                    time.sleep(delay)

        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
