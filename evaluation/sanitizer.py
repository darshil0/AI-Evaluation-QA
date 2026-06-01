"""
Data sanitization utilities for security.
"""

import re
from typing import Any, Dict, List, Union
import logging

logger = logging.getLogger(__name__)


class DataSanitizer:
    """Sanitize data before storage to prevent injection attacks."""

    MAX_STRING_LENGTH = 10000
    MAX_FILENAME_LENGTH = 255

    @staticmethod
    def sanitize_string(value: str, max_length: int = MAX_STRING_LENGTH) -> str:
        """
        Sanitize string input.

        Args:
            value: String to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string

        Raises:
            TypeError: If value is not a string
        """
        if not isinstance(value, str):
            raise TypeError(f"Expected string, got {type(value).__name__}")

        # Truncate to max length
        if len(value) > max_length:
            logger.warning(f"String truncated from {len(value)} to {max_length} chars")
            value = value[:max_length]

        # Remove null bytes
        value = value.replace("\x00", "")

        # Normalize whitespace
        value = " ".join(value.split())

        return value

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal attacks.

        Args:
            filename: Filename to sanitize

        Returns:
            Safe filename

        Example:
            >>> DataSanitizer.sanitize_filename("../../etc/passwd")
            'etcpasswd'
        """
        # Remove directory separators and special chars
        safe_chars = re.sub(r"[^\w\s\-\.]", "", filename)

        # Remove leading/trailing dots and spaces
        safe_chars = safe_chars.strip(". ")

        # Limit length
        safe_chars = safe_chars[: DataSanitizer.MAX_FILENAME_LENGTH]

        if not safe_chars:
            safe_chars = "unnamed_file"

        return safe_chars

    @staticmethod
    def sanitize_json(data: Union[Dict, List, str, int, float, bool, None]) -> Any:
        """
        Recursively sanitize JSON data.

        Args:
            data: Data structure to sanitize

        Returns:
            Sanitized data structure
        """
        if isinstance(data, dict):
            return {
                DataSanitizer.sanitize_string(str(k), 200): DataSanitizer.sanitize_json(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [DataSanitizer.sanitize_json(item) for item in data]
        elif isinstance(data, str):
            return DataSanitizer.sanitize_string(data)
        else:
            # Numbers, booleans, None pass through
            return data

    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """
        Validate API key format (basic check).

        Args:
            api_key: API key to validate

        Returns:
            True if format appears valid
        """
        if not api_key or not isinstance(api_key, str):
            return False

        # Basic checks
        if len(api_key) < 20:
            return False

        if api_key.startswith(("sk-", "claude-")):
            return True

        return len(api_key) > 30
