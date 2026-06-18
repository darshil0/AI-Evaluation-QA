"""Error handling and recovery for evaluation pipeline."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class FailedRequest:
    """Record of a failed request."""

    prompt_id: str
    error_type: str
    error_message: str
    timestamp: str
    retry_count: int
    severity: ErrorSeverity


class EvaluationErrorHandler:
    """Handles errors during evaluation with recovery strategies."""

    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.failed_requests: List[FailedRequest] = []
        self.error_stats = {"total_errors": 0, "by_type": {}, "by_severity": {}}

    async def execute_with_retry(
        self, func: Callable, prompt_id: str, *args, **kwargs
    ) -> Tuple[bool, Any, Optional[FailedRequest]]:
        """Execute a function with exponential backoff retry logic."""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                result = await func(*args, **kwargs)

                if attempt > 0:
                    logger.info(f"✓ Prompt {prompt_id} succeeded on retry #{attempt}")

                return True, result, None

            except asyncio.TimeoutError as e:
                last_exception = e
                error_type = "TimeoutError"
            except ConnectionError as e:
                last_exception = e
                error_type = "ConnectionError"
            except ValueError as e:
                last_exception = e
                error_type = "ValueError"
            except Exception as e:
                last_exception = e
                error_type = type(e).__name__

            self.error_stats["total_errors"] += 1
            self.error_stats["by_type"][error_type] = (
                self.error_stats["by_type"].get(error_type, 0) + 1
            )

            if attempt < self.max_retries:
                wait_time = self.backoff_factor**attempt
                logger.warning(
                    f"Prompt {prompt_id} failed (attempt {attempt + 1}/"
                    f"{self.max_retries + 1}): {error_type}. "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                severity = self._determine_severity(error_type)
                failed_req = FailedRequest(
                    prompt_id=prompt_id,
                    error_type=error_type,
                    error_message=str(last_exception),
                    timestamp=datetime.now().isoformat(),
                    retry_count=self.max_retries,
                    severity=severity,
                )
                self.failed_requests.append(failed_req)

                self.error_stats["by_severity"][severity.value] = (
                    self.error_stats["by_severity"].get(severity.value, 0) + 1
                )

                logger.error(
                    f"Prompt {prompt_id} failed after {self.max_retries + 1} "
                    f"attempts: {error_type}"
                )

                return False, None, failed_req

        return False, None, None

    @staticmethod
    def _determine_severity(error_type: str) -> ErrorSeverity:
        """Determine error severity based on error type."""
        critical_errors = ["AuthenticationError", "InvalidConfigError"]
        high_errors = ["TimeoutError", "RateLimitError"]

        if error_type in critical_errors:
            return ErrorSeverity.CRITICAL
        elif error_type in high_errors:
            return ErrorSeverity.HIGH
        elif error_type in ["ConnectionError", "ValueError"]:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    async def handle_async_error(self, error: Exception) -> None:
        """Handle errors in async context safely."""
        try:
            # Check if we are in an active event loop
            asyncio.get_running_loop()
            # If so, we can just log it or do other async things
            # In this simple implementation, we just log it
            logger.error(f"Async error handled: {error}")
        except RuntimeError:
            # Fallback to sync if not in event loop
            logger.error(f"Error handled (no event loop): {error}")

    def get_summary(self) -> Dict[str, Any]:
        """Get error handling summary."""
        return {
            "total_failed": len(self.failed_requests),
            "error_stats": self.error_stats,
            "failed_requests": [
                {
                    "prompt_id": fr.prompt_id,
                    "error_type": fr.error_type,
                    "error_message": fr.error_message,
                    "timestamp": fr.timestamp,
                    "retry_count": fr.retry_count,
                    "severity": fr.severity.value,
                }
                for fr in self.failed_requests
            ],
        }
