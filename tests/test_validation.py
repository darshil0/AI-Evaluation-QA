"""
Unit tests for input validation.
"""

import pytest
import json
from pathlib import Path
from jsonschema import ValidationError
from config.validation import validate_prompt_file, validate_config


class TestPromptValidation:
    """Test prompt file validation."""

    def test_valid_prompt_file(self, tmp_path):
        """Test validation of valid prompt file."""
        valid_prompt = {
            "metadata": {"version": "1.0", "description": "Test prompts"},
            "prompts": [
                {
                    "id": "TEST_001",
                    "version": "1.0",
                    "category": "reasoning",
                    "text": "Test prompt text that is long enough",
                    "difficulty": "easy",
                    "tags": ["test"],
                }
            ],
        }

        prompt_file = tmp_path / "test_prompts.json"
        prompt_file.write_text(json.dumps(valid_prompt))

        result = validate_prompt_file(str(prompt_file))
        assert result == valid_prompt

    def test_missing_required_field(self, tmp_path):
        """Test validation fails when required field is missing."""
        invalid_prompt = {
            "metadata": {"version": "1.0", "description": "Test"},
            "prompts": [
                {
                    "id": "TEST_001",
                    "version": "1.0",
                    # Missing 'category' field
                    "text": "Test prompt text",
                }
            ],
        }

        prompt_file = tmp_path / "invalid_prompts.json"
        prompt_file.write_text(json.dumps(invalid_prompt))

        with pytest.raises(ValidationError):
            validate_prompt_file(str(prompt_file))

    def test_duplicate_prompt_ids(self, tmp_path):
        """Test validation fails with duplicate IDs."""
        duplicate_prompt = {
            "metadata": {"version": "1.0", "description": "Test"},
            "prompts": [
                {"id": "TEST_001", "version": "1.0", "category": "test", "text": "First prompt"},
                {
                    "id": "TEST_001",  # Duplicate ID
                    "version": "1.0",
                    "category": "test",
                    "text": "Second prompt",
                },
            ],
        }

        prompt_file = tmp_path / "duplicate_prompts.json"
        prompt_file.write_text(json.dumps(duplicate_prompt))

        with pytest.raises(ValidationError, match="Duplicate prompt IDs"):
            validate_prompt_file(str(prompt_file))

    def test_invalid_difficulty(self, tmp_path):
        """Test validation fails with invalid difficulty."""
        invalid_difficulty = {
            "metadata": {"version": "1.0", "description": "Test"},
            "prompts": [
                {
                    "id": "TEST_001",
                    "version": "1.0",
                    "category": "test",
                    "text": "Test prompt",
                    "difficulty": "invalid",  # Not in enum
                }
            ],
        }

        prompt_file = tmp_path / "invalid_difficulty.json"
        prompt_file.write_text(json.dumps(invalid_difficulty))

        with pytest.raises(ValidationError):
            validate_prompt_file(str(prompt_file))

    def test_file_not_found(self):
        """Test validation fails when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            validate_prompt_file("nonexistent_file.json")


class TestConfigValidation:
    """Test configuration validation."""

    def test_valid_config(self):
        """Test validation of valid configuration."""
        valid_config = {
            "models": {"primary": {"provider": "openai", "model_name": "gpt-4"}},
            "api": {"max_retries": 3, "rate_limit_rpm": 60},
            "scoring": {"dimensions": {}},
        }

        # Should not raise
        validate_config(valid_config)

    def test_missing_required_key(self):
        """Test validation fails when required key is missing."""
        invalid_config = {
            "models": {},
            "api": {},
            # Missing 'scoring'
        }

        with pytest.raises(ValueError, match="Missing required config key"):
            validate_config(invalid_config)

    def test_invalid_rate_limit(self):
        """Test validation fails with invalid rate limit."""
        invalid_config = {
            "models": {"primary": {}},
            "api": {"rate_limit_rpm": -10},  # Invalid
            "scoring": {},
        }

        with pytest.raises(ValueError, match="rate_limit_rpm must be positive"):
            validate_config(invalid_config)
