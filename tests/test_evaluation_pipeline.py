"""
Unit and Integration Tests for AI Evaluation Pipeline

This module contains comprehensive tests for the evaluation framework,
including prompt execution, scoring, and report generation.
"""

import pytest
import json
import csv
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.prompt_runner import PromptRunner, execute_prompts
from evaluation.scoring_engine import ScoringEngine, score_responses
from evaluation.report_generator import ReportGenerator, generate_reports

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_prompts():
    """Sample prompts for testing."""
    return {
        "prompts": [
            {
                "id": "test_001",
                "category": "reasoning",
                "prompt": "Explain why the sky is blue.",
                "expected_elements": ["light scattering", "atmosphere", "wavelength"],
                "difficulty": "easy",
            },
            {
                "id": "test_002",
                "category": "factual",
                "prompt": "What is the capital of France?",
                "expected_elements": ["Paris"],
                "difficulty": "easy",
            },
        ]
    }


@pytest.fixture
def sample_responses():
    """Sample model responses for testing."""
    return [
        {
            "prompt_id": "test_001",
            "prompt": "Explain why the sky is blue.",
            "response": "The sky appears blue due to Rayleigh scattering. When sunlight enters the atmosphere, shorter wavelengths (blue) scatter more than longer wavelengths (red).",
            "model": "gpt-4",
            "timestamp": "2025-11-11T10:00:00",
        },
        {
            "prompt_id": "test_002",
            "prompt": "What is the capital of France?",
            "response": "The capital of France is Paris.",
            "model": "gpt-4",
            "timestamp": "2025-11-11T10:00:01",
        },
    ]


@pytest.fixture
def sample_scored_responses():
    """Sample scored responses for testing."""
    return [
        {
            "prompt_id": "test_001",
            "prompt": "Explain why the sky is blue.",
            "response": "The sky appears blue due to Rayleigh scattering.",
            "accuracy": 5,
            "reasoning": 4,
            "tone": 5,
            "completeness": 4,
            "defects": "",
            "overall_score": 4.5,
        },
        {
            "prompt_id": "test_002",
            "prompt": "What is the capital of France?",
            "response": "The capital of France is Paris.",
            "accuracy": 5,
            "reasoning": 5,
            "tone": 5,
            "completeness": 5,
            "defects": "",
            "overall_score": 5.0,
        },
    ]


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="This is a test response."))]
    return mock_response


# ============================================================================
# PROMPT RUNNER TESTS
# ============================================================================


class TestPromptRunner:
    """Tests for the PromptRunner class."""

    def test_init(self):
        """Test PromptRunner initialization."""
        runner = PromptRunner(model="gpt-4", timeout=30)
        assert runner.model == "gpt-4"
        assert runner.timeout == 30

    def test_init_default_values(self):
        """Test PromptRunner initialization with defaults."""
        runner = PromptRunner()
        assert runner.model is not None
        assert runner.timeout > 0

    @patch("openai.OpenAI")
    def test_execute_single_prompt(self, mock_openai_class, mock_openai_response):
        """Test executing a single prompt."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response

        runner = PromptRunner(model="gpt-4", config={"api_key": "test-key"})
        prompt = "What is 2+2?"
        response = runner.execute_prompt(prompt)

        assert response is not None
        assert isinstance(response, str)
        mock_client.chat.completions.create.assert_called_once()

    @patch("openai.OpenAI")
    def test_execute_multiple_prompts(
        self, mock_openai_class, mock_openai_response, sample_prompts
    ):
        """Test executing multiple prompts."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response

        runner = PromptRunner(model="gpt-4", config={"api_key": "test-key"})
        responses = runner.execute_prompts(sample_prompts["prompts"])

        assert len(responses) == len(sample_prompts["prompts"])
        assert all(isinstance(r, dict) for r in responses)

    def test_save_responses_csv(self, temp_dir, sample_responses):
        """Test saving responses to CSV."""
        runner = PromptRunner()
        output_file = temp_dir / "test_results.csv"

        runner.save_responses(sample_responses, str(output_file), file_format="csv")

        assert output_file.exists()
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == len(sample_responses)

    def test_save_responses_json(self, temp_dir, sample_responses):
        """Test saving responses to JSON."""
        runner = PromptRunner()
        output_file = temp_dir / "test_results.json"

        runner.save_responses(sample_responses, str(output_file), file_format="json")

        assert output_file.exists()
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert len(data) == len(sample_responses)

    @patch("openai.OpenAI")
    def test_error_handling_api_failure(self, mock_openai_class):
        """Test error handling when API fails."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        runner = PromptRunner(model="gpt-4", retry_attempts=1, config={"api_key": "test-key"})

        with pytest.raises(Exception):
            runner.execute_prompt("Test prompt")

    @patch("openai.OpenAI")
    def test_retry_logic(self, mock_openai_class, mock_openai_response):
        """Test retry logic on transient failures."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        # Fail twice, then succeed
        mock_client.chat.completions.create.side_effect = [
            Exception("Timeout"),
            Exception("Timeout"),
            mock_openai_response,
        ]

        runner = PromptRunner(model="gpt-4", retry_attempts=3, config={"api_key": "test-key"})
        response = runner.execute_prompt("Test prompt")

        assert response is not None
        assert mock_client.chat.completions.create.call_count == 3

    def test_timeout_configuration(self):
        """Test timeout configuration."""
        runner = PromptRunner(timeout=60)
        assert runner.timeout == 60


# ============================================================================
# SCORING ENGINE TESTS
# ============================================================================


class TestScoringEngine:
    """Tests for the ScoringEngine class."""

    def test_init(self):
        """Test ScoringEngine initialization."""
        engine = ScoringEngine()
        assert engine is not None

    def test_score_accuracy(self):
        """Test accuracy scoring."""
        engine = ScoringEngine()

        # Correct response
        score = engine.score_accuracy(
            "Paris is the capital of France. This is specifically correct because of history.",
            "What is the capital of France?",
        )
        assert 4 <= score <= 5

        # Incorrect response
        score = engine.score_accuracy("I don't know.", "What is the capital of France?")
        assert 1 <= score <= 2

    def test_score_reasoning(self):
        """Test reasoning scoring."""
        engine = ScoringEngine()

        # Good reasoning
        response = "Water boils at 100°C because at this temperature, the vapor pressure equals atmospheric pressure. Therefore it boils. 1) heat 2) boil."
        score = engine.score_reasoning(response, "Why does water boil at 100°C?")
        assert 4 <= score <= 5

        # Poor reasoning
        response = "Water boils because it gets hot."
        score = engine.score_reasoning(response, "Why does water boil at 100°C?")
        assert 1 <= score <= 3

    def test_score_tone(self):
        """Test tone scoring."""
        engine = ScoringEngine()

        # Appropriate tone
        response = "I understand your concern. Let me help you with that."
        score = engine.score_tone(response, "I need help with my account.")
        assert 4 <= score <= 5

        # Inappropriate tone
        response = "You should have read the manual. This is obvious."
        score = engine.score_tone(response, "I need help with my account.")
        assert 1 <= score <= 2

    def test_score_completeness(self):
        """Test completeness scoring."""
        engine = ScoringEngine()

        # Complete response
        response = "To reset your password: 1) Go to settings, 2) Click forgot password, 3) Check your email, 4) Create a new password."
        score = engine.score_completeness(response, "How do I reset my password?")
        assert 4 <= score <= 5

        # Incomplete response
        response = "Go to settings."
        score = engine.score_completeness(response, "How do I reset my password?")
        assert 1 <= score <= 3

    def test_score_response_all_dimensions(self, sample_responses):
        """Test scoring a response across all dimensions."""
        engine = ScoringEngine()

        response = sample_responses[0]
        report = engine.score_response(response)
        scored = engine.report_to_dict(report)

        assert "score_accuracy" in scored
        assert "score_reasoning" in scored
        assert "score_tone" in scored
        assert "score_completeness" in scored
        assert "overall_score" in scored
        assert 0 <= scored["overall_score"] <= 5

    def test_identify_defects(self):
        """Test defect identification."""
        engine = ScoringEngine()

        # Response with logical defect
        response_data = {
            "response": "All birds can fly, therefore penguins can fly.",
            "score_accuracy": 0.1,
            "score_reasoning": 0.1,
        }
        defects = engine.identify_defects(response_data)
        assert "D01" in defects  # Logical defect

    def test_score_batch_responses(self, sample_responses):
        """Test scoring multiple responses."""
        engine = ScoringEngine()
        scored = engine.score_batch(sample_responses)

        assert len(scored) == len(sample_responses)
        assert all("overall_score" in s for s in scored)

    def test_save_scored_responses(self, temp_dir, sample_scored_responses):
        """Test saving scored responses."""
        engine = ScoringEngine()
        output_file = temp_dir / "scored_results.csv"

        engine.save_scores(sample_scored_responses, str(output_file))

        assert output_file.exists()
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == len(sample_scored_responses)
            assert "overall_score" in rows[0]


# ============================================================================
# REPORT GENERATOR TESTS
# ============================================================================


class TestReportGenerator:
    """Tests for the ReportGenerator class."""

    def test_init(self):
        """Test ReportGenerator initialization."""
        generator = ReportGenerator()
        assert generator is not None

    def test_load_scored_data(self, temp_dir, sample_scored_responses):
        """Test loading scored data from CSV."""
        # Create CSV file
        csv_file = temp_dir / "scored.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=sample_scored_responses[0].keys())
            writer.writeheader()
            writer.writerows(sample_scored_responses)

        generator = ReportGenerator()
        data = generator.load_data(str(csv_file))

        assert len(data) == len(sample_scored_responses)

    def test_calculate_statistics(self, sample_scored_responses):
        """Test calculating summary statistics."""
        generator = ReportGenerator()
        stats = generator.calculate_statistics(sample_scored_responses)

        assert "mean_accuracy" in stats
        assert "mean_reasoning" in stats
        assert "mean_tone" in stats
        assert "mean_completeness" in stats
        assert "mean_overall" in stats
        assert stats["total_evaluations"] == len(sample_scored_responses)

    def test_generate_accuracy_chart(self, temp_dir, sample_scored_responses):
        """Test generating accuracy chart."""
        generator = ReportGenerator()
        output_file = temp_dir / "accuracy_chart.png"

        generator.generate_accuracy_chart(sample_scored_responses, str(output_file))

        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_generate_defect_summary(self, temp_dir):
        """Test generating defect summary."""
        generator = ReportGenerator()

        data = [{"defects": "D01,D02"}, {"defects": "D01"}, {"defects": ""}]

        summary = generator.generate_defect_summary(data)

        assert "D01" in summary
        assert summary["D01"] == 2
        assert summary["D02"] == 1

    def test_generate_html_report(self, temp_dir, sample_scored_responses):
        """Test generating HTML report."""
        generator = ReportGenerator()
        output_file = temp_dir / "report.html"

        generator.generate_html_report(sample_scored_responses, str(output_file))

        assert output_file.exists()
        content = output_file.read_text()
        assert "<html>" in content
        assert "Evaluation Summary" in content

    def test_generate_all_reports(self, temp_dir, sample_scored_responses):
        """Test generating all reports."""
        generator = ReportGenerator()

        generator.generate_all_reports(sample_scored_responses, output_dir=str(temp_dir))

        # Check that files were created
        assert (temp_dir / "accuracy_trends.png").exists()
        assert (temp_dir / "defect_summary.csv").exists()
        assert (temp_dir / "evaluation_summary.html").exists()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration:
    """Integration tests for the complete pipeline."""

    @patch("openai.OpenAI")
    def test_full_pipeline(self, mock_openai_class, mock_openai_response, temp_dir, sample_prompts):
        """Test the complete evaluation pipeline."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response

        # Step 1: Execute prompts
        runner = PromptRunner(model="gpt-4", config={"api_key": "test-key"})
        responses = runner.execute_prompts(sample_prompts["prompts"])
        responses_file = temp_dir / "responses.csv"
        runner.save_responses(responses, str(responses_file))

        # Step 2: Score responses
        engine = ScoringEngine()
        scored = engine.score_batch(responses)
        scored_file = temp_dir / "scored.csv"
        engine.save_scores(scored, str(scored_file))

        # Step 3: Generate reports
        generator = ReportGenerator()
        generator.generate_all_reports(scored, output_dir=str(temp_dir))

        # Verify all files exist
        assert responses_file.exists()
        assert scored_file.exists()
        assert (temp_dir / "evaluation_summary.html").exists()

    def test_error_propagation(self):
        """Test that errors propagate correctly through the pipeline."""
        runner = PromptRunner(model="invalid-model", config={"api_key": "test-key"})

        with pytest.raises(Exception):
            runner.execute_prompt("Test prompt")


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_prompt_list(self):
        """Test handling of empty prompt list."""
        runner = PromptRunner()
        responses = runner.execute_prompts([])
        assert responses == []

    def test_malformed_prompt(self):
        """Test handling of malformed prompts."""
        runner = PromptRunner(config={"api_key": "test-key"})

        with pytest.raises(ValueError):
            runner.execute_prompts([{"invalid": "structure"}])

    def test_missing_api_key(self):
        """Test handling of missing API key."""
        # The constructor doesn't check for API key anymore, execute_prompt does.
        runner = PromptRunner()
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable not set"):
                runner.execute_prompt("Test prompt")

    def test_unicode_handling(self):
        """Test handling of unicode characters."""
        engine = ScoringEngine()
        response = "こんにちは世界"  # Hello World in Japanese
        score = engine.score_accuracy(response, "Say hello in Japanese")
        assert 1 <= score <= 5

    def test_very_long_response(self):
        """Test handling of very long responses."""
        engine = ScoringEngine()
        response = "A" * 10000  # Very long response
        score = engine.score_completeness(response, "Test prompt")
        assert 1 <= score <= 5


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


class TestPerformance:
    """Performance-related tests."""

    @pytest.mark.slow
    def test_batch_processing_performance(self, sample_prompts):
        """Test performance of batch processing."""
        import time

        runner = PromptRunner(config={"api_key": "test-key"})

        # Create 100 prompts
        large_batch = sample_prompts["prompts"] * 50

        start = time.time()
        with patch("openai.OpenAI") as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content="Response"))]
            )
            runner.execute_prompts(large_batch)

        elapsed = time.time() - start

        # Should complete in reasonable time (< 5 seconds with mocking)
        assert elapsed < 5


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
