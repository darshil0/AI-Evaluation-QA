"""
Additional tests for 100% coverage of prompt_runner.py

These tests cover edge cases and error paths that weren't covered in the main test suite.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from evaluation.prompt_runner import PromptRunner, execute_prompts


class TestPromptRunnerEdgeCases:
    """Edge case tests to achieve 100% coverage."""

    def test_execute_prompt_with_api_error(self):
        """Test execute_prompt when API raises an error."""
        runner = PromptRunner(model="gpt-4", retry_attempts=1, config={"api_key": "test-key"})

        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_openai.return_value = mock_client

            with pytest.raises(Exception) as exc_info:
                runner.execute_prompt("Test prompt")

            assert "API Error" in str(exc_info.value)

    def test_execute_prompt_missing_api_key(self):
        """Test execute_prompt when OPENAI_API_KEY is not set."""
        runner = PromptRunner(model="gpt-4")

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception) as exc_info:
                runner.execute_prompt("Test prompt")

            assert "api_key client option must be set" in str(exc_info.value)

    def test_execute_prompts_empty_list(self):
        """Test execute_prompts with empty list."""
        runner = PromptRunner()
        result = runner.execute_prompts([])
        assert result == []

    def test_execute_prompts_invalid_structure(self):
        """Test execute_prompts with invalid prompt structure."""
        runner = PromptRunner()

        with pytest.raises(ValueError) as exc_info:
            runner.execute_prompts([{"invalid": "structure"}])

        assert "prompt" in str(exc_info.value).lower() or "text" in str(exc_info.value).lower()

    def test_execute_prompts_with_text_field(self):
        """Test execute_prompts using 'text' field instead of 'prompt'."""
        runner = PromptRunner(model="gpt-4", config={"api_key": "test-key"})

        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test response"
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            prompts = [{"id": "p1", "text": "Question using text field"}]
            results = runner.execute_prompts(prompts)

            assert len(results) == 1
            assert results[0]["response"] == "Test response"

    def test_execute_prompts_with_retry_failure(self):
        """Test execute_prompts when retries are exhausted."""
        runner = PromptRunner(model="gpt-4", retry_attempts=2, config={"api_key": "test-key"})

        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("Persistent error")
            mock_openai.return_value = mock_client

            prompts = [{"id": "p1", "prompt": "Test"}]

            # runner.execute_prompts catches internal exceptions of individual prompts
            results = runner.execute_prompts(prompts)

            assert results[0]["status"] == "error"
            assert runner.failure_count > 0

    def test_save_responses_json_format(self):
        """Test save_responses with JSON format."""
        import json
        import tempfile

        runner = PromptRunner()
        results = [
            {"prompt_id": "p1", "response": "Answer 1"},
            {"prompt_id": "p2", "response": "Answer 2"},
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_file = f.name

        try:
            runner.save_responses(results, temp_file, file_format="json")

            with open(temp_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            assert len(loaded) == 2
            assert loaded[0]["prompt_id"] == "p1"
        finally:
            os.unlink(temp_file)

    def test_save_responses_invalid_format(self):
        """Test save_responses with invalid format."""
        runner = PromptRunner()
        results = [{"test": "data"}]

        with pytest.raises(ValueError) as exc_info:
            runner.save_responses(results, "test.txt", file_format="invalid")

        assert "Unsupported format" in str(exc_info.value)

    def test_save_results_legacy_method(self):
        """Test save_results (legacy method) calls save_responses."""
        import tempfile

        runner = PromptRunner()
        results = [{"prompt_id": "p1", "response": "Test"}]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_file = f.name

        try:
            runner.save_results(results, temp_file)
            assert os.path.exists(temp_file)
        finally:
            os.unlink(temp_file)

    def test_print_summary(self):
        """Test print_summary method."""
        runner = PromptRunner()
        runner.failure_count = 5

        # Should not raise any exceptions
        runner.print_summary()

    def test_print_summary_no_failures(self):
        """Test print_summary with no failures."""
        runner = PromptRunner()
        runner.failure_count = 0

        # Should not raise any exceptions
        runner.print_summary()

    def test_standalone_execute_prompts_function(self):
        """Test standalone execute_prompts function."""
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            prompts = [{"id": "p1", "prompt": "Test"}]
            results = execute_prompts(prompts, config={"api_key": "test-key"})

            assert len(results) == 1
            assert results[0]["response"] == "Response"

    def test_standalone_execute_prompts_with_config(self):
        """Test standalone execute_prompts function with config."""
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            config = {"model": "gpt-3.5-turbo", "api_key": "test-key"}
            prompts = [{"id": "p1", "prompt": "Test"}]
            results = execute_prompts(prompts, config=config)

            assert len(results) == 1

    def test_execute_prompt_async_compatibility(self):
        """Test that async methods still exist for backward compatibility."""
        runner = PromptRunner(config={"models": {"primary": {"provider": "openai"}}})

        # Verify async method exists
        assert hasattr(runner, "execute_prompt_async")
        assert hasattr(runner, "run_prompts")

    def test_initialization_with_all_parameters(self):
        """Test initialization with all parameters specified."""
        runner = PromptRunner(
            config={"test": "config"}, model="gpt-4-turbo", timeout=60, retry_attempts=5
        )

        assert runner.model == "gpt-4-turbo"
        assert runner.timeout == 60
        assert runner.retry_attempts == 5
        assert runner.config == {"test": "config"}

    def test_initialization_defaults(self):
        """Test initialization with default parameters."""
        runner = PromptRunner()

        assert runner.model == "gpt-4"
        assert runner.timeout == 30
        assert runner.retry_attempts == 3
        assert runner.config == {}
        assert runner.failure_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=evaluation.prompt_runner", "--cov-report=term-missing"])
