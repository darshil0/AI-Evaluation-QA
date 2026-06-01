"""Tests for validation modules."""

import pytest
import os
import json
import tempfile
import asyncio
import aiohttp
from pathlib import Path

from config.validator import ConfigurationValidator, validate_before_execution
from config.prompt_validator import PromptValidator, execute_prompts_with_tracking
from evaluation.cost_tracker import CostTracker
from evaluation.error_handler import EvaluationErrorHandler


class TestConfigValidator:
    """Test configuration validation."""

    def test_validate_env_variables_present(self):
        """Test validation when env vars are present."""
        os.environ["OPENAI_API_KEY"] = "test_key_123"
        os.environ["ANTHROPIC_API_KEY"] = "test_key_456"

        result = ConfigurationValidator.validate_env_variables(strict=False)
        assert result["valid"] is True
        assert len(result["missing"]) == 0

    def test_validate_env_variables_missing(self):
        """Test validation when env vars are missing."""
        os.environ.pop("OPENAI_API_KEY", None)
        os.environ.pop("ANTHROPIC_API_KEY", None)

        result = ConfigurationValidator.validate_env_variables(strict=False)
        assert result["valid"] is False
        assert len(result["missing"]) > 0

    def test_validate_env_variables_strict(self):
        """Test strict validation raises error."""
        os.environ.pop("OPENAI_API_KEY", None)

        with pytest.raises(ValueError):
            ConfigurationValidator.validate_env_variables(strict=True)


class TestPromptValidator:
    """Test prompt file validation."""

    def test_valid_prompt_file(self):
        """Test loading valid prompt file."""
        valid_data = {
            "metadata": {"version": "1.0", "description": "Test prompts"},
            "prompts": [
                {
                    "id": "test_001",
                    "text": "This is a test prompt with sufficient length",
                    "category": "reasoning",
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(valid_data, f)
            temp_file = f.name

        try:
            result = PromptValidator.load_and_validate(temp_file)
            assert result is not None
            assert len(result["prompts"]) == 1
        finally:
            os.unlink(temp_file)

    def test_invalid_prompt_schema(self):
        """Test loading invalid prompt file."""
        invalid_data = {
            "metadata": {
                "version": "1.0"
                # Missing required 'description'
            },
            "prompts": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            temp_file = f.name

        try:
            with pytest.raises(ValueError):
                PromptValidator.load_and_validate(temp_file)
        finally:
            os.unlink(temp_file)

    def test_duplicate_prompt_ids(self):
        """Test detection of duplicate prompt IDs."""
        data_with_duplicates = {
            "metadata": {"version": "1.0", "description": "Test prompts"},
            "prompts": [
                {
                    "id": "test_001",
                    "text": "First prompt with sufficient text length",
                    "category": "reasoning",
                },
                {
                    "id": "test_001",
                    "text": "Duplicate ID prompt with sufficient text length",
                    "category": "reasoning",
                },
            ],
        }

        _, warnings = PromptValidator.validate_semantic(data_with_duplicates)
        assert any("Duplicate prompt ID" in w for w in warnings)


class TestCostTracker:
    """Test cost tracking functionality."""

    def test_add_request_basic(self):
        """Test adding a basic request."""
        tracker = CostTracker(model_name="gpt-3.5-turbo")
        cost = tracker.add_request(
            model="gpt-3.5-turbo", input_tokens=100, output_tokens=50, prompt_id="test_001"
        )

        assert cost > 0
        assert tracker.total_cost > 0
        assert len(tracker.usage_log) == 1

    def test_budget_warning(self):
        """Test budget warning at 80%."""
        tracker = CostTracker(model_name="gpt-4", budget_limit=10.0)

        # Add requests to reach 80% of budget
        # GPT-4: 30/1M input, 60/1M output.
        # To get 8.0 USD: 100k input + 100k output = 3.0 + 6.0 = 9.0
        tracker.add_request(
            model="gpt-4", input_tokens=100000, output_tokens=100000, prompt_id="test_001"
        )

        assert len(tracker.alerts) > 0
        assert tracker.alerts[0]["type"] == "warning"

    def test_budget_exceeded(self):
        """Test error log when budget is exceeded."""
        tracker = CostTracker(model_name="gpt-4", budget_limit=1.0)

        tracker.add_request(
            model="gpt-4", input_tokens=500000, output_tokens=500000, prompt_id="test_001"
        )

        assert any(a["type"] == "error" for a in tracker.alerts)

    def test_unknown_model(self):
        """Test fallback for unknown model."""
        tracker = CostTracker()
        cost = tracker.add_request(
            model="unknown-model", input_tokens=100, output_tokens=50, prompt_id="test_001"
        )
        assert cost > 0

    def test_get_summary(self):
        """Test cost summary generation."""
        tracker = CostTracker(model_name="gpt-3.5-turbo")
        tracker.add_request(
            model="gpt-3.5-turbo", input_tokens=100, output_tokens=50, prompt_id="test_001"
        )
        tracker.add_request(
            model="gpt-3.5-turbo", input_tokens=200, output_tokens=100, prompt_id="test_002"
        )

        summary = tracker.get_summary()
        assert summary["total_requests"] == 2
        assert summary["total_cost"] > 0
        assert "gpt-3.5-turbo" in summary["by_model"]


class TestErrorHandler:
    """Test error handling functionality."""

    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self):
        """Test successful execution without retry."""
        handler = EvaluationErrorHandler(max_retries=2)

        async def mock_func(*args, **kwargs):
            return {"result": "success"}

        success, result, failed = await handler.execute_with_retry(mock_func, "test_001")

        assert success is True
        assert result["result"] == "success"
        assert failed is None

    @pytest.mark.asyncio
    async def test_execute_with_retry_max_retries(self):
        """Test retry logic with max attempts."""
        handler = EvaluationErrorHandler(max_retries=2, backoff_factor=0.01)

        async def failing_func(*args, **kwargs):
            raise ConnectionError("Connection failed")

        success, result, failed = await handler.execute_with_retry(failing_func, "test_001")

        assert success is False
        assert result is None
        assert failed is not None
        assert failed.retry_count == 2

    def test_error_severity_determination(self):
        """Test error severity classification."""
        assert EvaluationErrorHandler._determine_severity("AuthenticationError").value == "critical"

        assert EvaluationErrorHandler._determine_severity("TimeoutError").value == "high"

        assert EvaluationErrorHandler._determine_severity("ConnectionError").value == "medium"

        assert EvaluationErrorHandler._determine_severity("SomeOtherError").value == "low"
