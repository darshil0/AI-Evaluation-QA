"""
Unit tests for data sanitizer.
"""

import pytest

from evaluation.sanitizer import DataSanitizer


class TestDataSanitizer:
    """Test data sanitization."""

    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        input_str = "  Hello   World  "
        result = DataSanitizer.sanitize_string(input_str)
        assert result == "Hello World"

    def test_sanitize_string_removes_null_bytes(self):
        """Test null byte removal."""
        input_str = "Hello\x00World"
        result = DataSanitizer.sanitize_string(input_str)
        assert "\x00" not in result
        assert result == "HelloWorld"

    def test_sanitize_string_truncates(self):
        """Test string truncation."""
        long_string = "a" * 20000
        result = DataSanitizer.sanitize_string(long_string, max_length=100)
        assert len(result) == 100

    def test_sanitize_string_type_error(self):
        """Test type error for non-string input."""
        with pytest.raises(TypeError):
            DataSanitizer.sanitize_string(123)

    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        result = DataSanitizer.sanitize_filename("test_file.txt")
        assert result == "test_file.txt"

    def test_sanitize_filename_removes_path_separators(self):
        """Test path separator removal."""
        malicious = "../../etc/passwd"
        result = DataSanitizer.sanitize_filename(malicious)
        assert "/" not in result
        assert ".." not in result
        assert result == "etcpasswd"

    def test_sanitize_filename_empty_result(self):
        """Test handling of filename that becomes empty."""
        result = DataSanitizer.sanitize_filename("///")
        assert result == "unnamed_file"

    def test_sanitize_json_recursive(self):
        """Test recursive JSON sanitization."""
        data = {
            "key  with  spaces": "value  with  spaces",
            "nested": {"inner": "  text  "},
            "list": ["  item1  ", "  item2  "],
        }

        result = DataSanitizer.sanitize_json(data)

        assert result["key with spaces"] == "value with spaces"
        assert result["nested"]["inner"] == "text"
        assert result["list"] == ["item1", "item2"]

    def test_validate_api_key_valid(self):
        """Test API key validation for valid keys."""
        valid_key = "sk-" + "a" * 40
        assert DataSanitizer.validate_api_key(valid_key) is True

    def test_validate_api_key_invalid(self):
        """Test API key validation for invalid keys."""
        assert DataSanitizer.validate_api_key("short") is False
        assert DataSanitizer.validate_api_key("") is False
        assert DataSanitizer.validate_api_key(None) is False
        assert DataSanitizer.validate_api_key(123) is False

    def test_validate_api_key_generic(self):
        """Test generic API key validation."""
        assert DataSanitizer.validate_api_key("a" * 35) is True

    def test_sanitize_json_non_dict_list(self):
        """Test sanitizing simple values."""
        assert DataSanitizer.sanitize_json(123) == 123
        assert DataSanitizer.sanitize_json(True) is True
