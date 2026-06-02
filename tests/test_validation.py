import json
import pytest
from jsonschema import ValidationError

from config.validation import validate_config, validate_prompt_file


class TestPromptValidation:
    def test_valid_prompt_file(self, tmp_path):
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
        prompt_file.write_text(json.dumps(valid_prompt), encoding="utf-8")

        result = validate_prompt_file(str(prompt_file))
        assert result == valid_prompt

    def test_missing_required_field(self, tmp_path):
        invalid_prompt = {
            "metadata": {"version": "1.0", "description": "Test"},
            "prompts": [
                {
                    "id": "TEST_001",
                    "version": "1.0",
                    "text": "Test prompt text",
                }
            ],
        }

        prompt_file = tmp_path / "invalid_prompts.json"
        prompt_file.write_text(json.dumps(invalid_prompt), encoding="utf-8")

        with pytest.raises(ValidationError):
            validate_prompt_file(str(prompt_file))

    def test_duplicate_prompt_ids(self, tmp_path):
        duplicate_prompt = {
            "metadata": {"version": "1.0", "description": "Test"},
            "prompts": [
                {"id": "TEST_001", "version": "1.0", "category": "test", "text": "First prompt"},
                {"id": "TEST_001", "version": "1.0", "category": "test", "text": "Second prompt"},
            ],
        }

        prompt_file = tmp_path / "duplicate_prompts.json"
        prompt_file.write_text(json.dumps(duplicate_prompt), encoding="utf-8")

        with pytest.raises(ValidationError, match="Duplicate prompt IDs"):
            validate_prompt_file(str(prompt_file))

    def test_invalid_difficulty(self, tmp_path):
        invalid_difficulty = {
            "metadata": {"version": "1.0", "description": "Test"},
            "prompts": [
                {
                    "id": "TEST_001",
                    "version": "1.0",
                    "category": "test",
                    "text": "Test prompt",
                    "difficulty": "invalid",
                }
            ],
        }

        prompt_file = tmp_path / "invalid_difficulty.json"
        prompt_file.write_text(json.dumps(invalid_difficulty), encoding="utf-8")

        with pytest.raises(ValidationError):
            validate_prompt_file(str(prompt_file))

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            validate_prompt_file("nonexistent_file.json")


class TestConfigValidation:
    def test_valid_config(self):
        valid_config = {
            "models": {"primary": {"provider": "openai", "model_name": "gpt-4"}},
            "api": {"max_retries": 3, "rate_limit_rpm": 60},
            "scoring": {"dimensions": {}},
        }
        validate_config(valid_config)

    def test_missing_required_key(self):
        invalid_config = {
            "models": {},
            "api": {},
        }

        with pytest.raises(ValueError, match="Missing required config key"):
            validate_config(invalid_config)

    def test_invalid_rate_limit(self):
        invalid_config = {
            "models": {"primary": {}},
            "api": {"rate_limit_rpm": -10},
            "scoring": {},
        }

        with pytest.raises(ValueError, match="rate_limit_rpm must be positive"):
            validate_config(invalid_config)import json
import pytest
from jsonschema import ValidationError

from config.validation import validate_config, validate_prompt_file


class TestPromptValidation:
    def test_valid_prompt_file(self, tmp_path):
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
        prompt_file.write_text(json.dumps(valid_prompt), encoding="utf-8")

        result = validate_prompt_file(str(prompt_file))
        assert result == valid_prompt

    def test_missing_required_field(self, tmp_path):
        invalid_prompt = {
            "metadata": {"version": "1.0", "description": "Test"},
            "prompts": [
                {
                    "id": "TEST_001",
                    "version": "1.0",
                    "text": "Test prompt text",
                }
            ],
        }

        prompt_file = tmp_path / "invalid_prompts.json"
        prompt_file.write_text(json.dumps(invalid_prompt), encoding="utf-8")

        with pytest.raises(ValidationError):
            validate_prompt_file(str(prompt_file))

    def test_duplicate_prompt_ids(self, tmp_path):
        duplicate_prompt = {
            "metadata": {"version": "1.0", "description": "Test"},
            "prompts": [
                {"id": "TEST_001", "version": "1.0", "category": "test", "text": "First prompt"},
                {"id": "TEST_001", "version": "1.0", "category": "test", "text": "Second prompt"},
            ],
        }

        prompt_file = tmp_path / "duplicate_prompts.json"
        prompt_file.write_text(json.dumps(duplicate_prompt), encoding="utf-8")

        with pytest.raises(ValidationError, match="Duplicate prompt IDs"):
            validate_prompt_file(str(prompt_file))

    def test_invalid_difficulty(self, tmp_path):
        invalid_difficulty = {
            "metadata": {"version": "1.0", "description": "Test"},
            "prompts": [
                {
                    "id": "TEST_001",
                    "version": "1.0",
                    "category": "test",
                    "text": "Test prompt",
                    "difficulty": "invalid",
                }
            ],
        }

        prompt_file = tmp_path / "invalid_difficulty.json"
        prompt_file.write_text(json.dumps(invalid_difficulty), encoding="utf-8")

        with pytest.raises(ValidationError):
            validate_prompt_file(str(prompt_file))

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            validate_prompt_file("nonexistent_file.json")


class TestConfigValidation:
    def test_valid_config(self):
        valid_config = {
            "models": {"primary": {"provider": "openai", "model_name": "gpt-4"}},
            "api": {"max_retries": 3, "rate_limit_rpm": 60},
            "scoring": {"dimensions": {}},
        }
        validate_config(valid_config)

    def test_missing_required_key(self):
        invalid_config = {
            "models": {},
            "api": {},
        }

        with pytest.raises(ValueError, match="Missing required config key"):
            validate_config(invalid_config)

    def test_invalid_rate_limit(self):
        invalid_config = {
            "models": {"primary": {}},
            "api": {"rate_limit_rpm": -10},
            "scoring": {},
        }

        with pytest.raises(ValueError, match="rate_limit_rpm must be positive"):
            validate_config(invalid_config)
