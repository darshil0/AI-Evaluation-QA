import json
import os
import tempfile

import pytest

from config.validator import ConfigurationValidator
from config.prompt_validator import PromptValidator
from evaluation.cost_tracker import CostTracker
from evaluation.error_handler import EvaluationErrorHandler


class TestConfigValidator:
    def test_validate_env_variables_present(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test_key_123")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key_456")

        result = ConfigurationValidator.validate_env_variables(strict=False)
        assert result["valid"] is True
        assert result["missing"] == []

    def test_validate_env_variables_missing(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        result = ConfigurationValidator.validate_env_variables(strict=False)
        assert result["valid"] is False
        assert len(result["missing"]) > 0

    def test_validate_env_variables_strict(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(ValueError):
            ConfigurationValidator.validate_env_variables(strict=True)


class TestPromptValidator:
    def test_valid_prompt_file(self):
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

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(valid_data, f)
            temp_file = f.name

        try:
            result = PromptValidator.load_and_validate(temp_file)
            assert result is not None
            assert len(result["prompts"]) == 1
        finally:
            os.unlink(temp_file)

    def test_invalid_prompt_schema(self):
        invalid_data = {
            "metadata": {"version": "1.0"},
            "prompts": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(invalid_data, f)
            temp_file = f.name

        try:
            with pytest.raises(ValueError):
                PromptValidator.load_and_validate(temp_file)
        finally:
            os.unlink(temp_file)

    def test_duplicate_prompt_ids(self):
        data_with_duplicates = {
            "metadata": {"version": "1.0", "description": "Test prompts"},
            "prompts": [
                {"id": "test_001", "text": "First prompt with sufficient text length", "category": "reasoning"},
                {"id": "test_001", "text": "Duplicate ID prompt with sufficient text length", "category": "reasoning"},
            ],
        }

        _, warnings = PromptValidator.validate_semantic(data_with_duplicates)
        assert any("Duplicate prompt ID" in w for w in warnings)


class TestCostTracker:
    def test_add_request_basic(self):
        tracker = CostTracker(model_name="gpt-3.5-turbo")
        cost = tracker.add_request(
            model="gpt-3.5-turbo", input_tokens=100, output_tokens=50, prompt_id="test_001"
        )

        assert cost > 0
        assert tracker.total_cost > 0
        assert len(tracker.usage_log) == 1

    def test_budget_warning(self):
        tracker = CostTracker(model_name="gpt-4", budget_limit=10.0)

        tracker.add_request(
            model="gpt-4", input_tokens=100000, output_tokens=100000, prompt_id="test_001"
        )

        assert len(tracker.alerts) > 0
        assert tracker.alerts[0]["type"] == "warning"

    def test_budget_exceeded(self):
        tracker = CostTracker(model_name="gpt-4", budget_limit=1.0)

        tracker.add_request(
            model="gpt-4", input_tokens=500000, output_tokens=500000, prompt_id="test_001"
        )

        assert any(a["type"] == "error" for a in tracker.alerts)

    def test_unknown_model(self):
        tracker = CostTracker()
        cost = tracker.add_request(
            model="unknown-model", input_tokens=100, output_tokens=50, prompt_id="test_001"
        )
        assert cost > 0

    def test_get_summary(self):
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
    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self):
        handler = EvaluationErrorHandler(max_retries=2)

        async def mock_func(*args, **kwargs):
            return {"result": "success"}

        success, result, failed = await handler.execute_with_retry(mock_func, "test_001")

        assert success is True
        assert result["result"] == "success"
        assert failed is None

    @pytest.mark.asyncio
    async def test_execute_with_retry_max_retries(self):
        handler = EvaluationErrorHandler(max_retries=2, backoff_factor=0.01)

        async def failing_func(*args, **kwargs):
            raise ConnectionError("Connection failed")

        success, result, failed = await handler.execute_with_retry(failing_func, "test_001")

        assert success is False
        assert result is None
        assert failed is not None
        assert failed.retry_count == 2

    def test_error_severity_determination(self):
        assert EvaluationErrorHandler._determine_severity("AuthenticationError").value == "critical"
        assert EvaluationErrorHandler._determine_severity("TimeoutError").value == "high"
        assert EvaluationErrorHandler._determine_severity("ConnectionError").value == "medium"
        assert EvaluationErrorHandler._determine_severity("SomeOtherError").value == "low"
