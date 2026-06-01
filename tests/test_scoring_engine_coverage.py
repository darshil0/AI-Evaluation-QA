"""
Additional tests for 100% coverage of scoring_engine.py

These tests cover edge cases and all code paths for complete coverage.
"""

import pytest
from evaluation.scoring_engine import (
    ScoringEngine,
    Rubric,
    RubricCriterion,
    ScoreComponent,
    ScoreReport,
    score_responses,
)


class TestScoringEngineEdgeCases:
    """Edge case tests to achieve 100% coverage."""

    def test_score_accuracy_empty_response(self):
        """Test score_accuracy with empty response."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        score = engine.score_accuracy("", "prompt")
        assert score == 1

    def test_score_accuracy_uncertain_response(self):
        """Test score_accuracy with uncertain language."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        score = engine.score_accuracy("I don't know the answer", "prompt")
        assert score == 2

    def test_score_accuracy_detailed_response(self):
        """Test score_accuracy with detailed response."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        response = "This is a very detailed response with more than twenty words explaining the concept thoroughly and specifically with factual information because it provides comprehensive coverage."
        score = engine.score_accuracy(response, "prompt")
        assert score >= 4

    def test_score_reasoning_empty_response(self):
        """Test score_reasoning with empty response."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        score = engine.score_reasoning("", "prompt")
        assert score == 1

    def test_score_reasoning_with_logical_connectors(self):
        """Test score_reasoning with multiple logical connectors."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        response = "This happens because of X. Therefore, Y occurs. Thus, we can conclude Z."
        score = engine.score_reasoning(response, "prompt")
        assert score >= 4

    def test_score_reasoning_no_connectors(self):
        """Test score_reasoning without logical connectors."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        response = "This is a simple statement."
        score = engine.score_reasoning(response, "prompt")
        assert score <= 3

    def test_score_reasoning_with_structure(self):
        """Test score_reasoning with structured content."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        response = "First, we do this. Second, we do that. • Point one - Point two"
        score = engine.score_reasoning(response, "prompt")
        assert score >= 3

    def test_score_tone_empty_response(self):
        """Test score_tone with empty response."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        score = engine.score_tone("", "prompt")
        assert score == 1

    def test_score_tone_positive_indicators(self):
        """Test score_tone with positive language."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        response = "I understand your concern. Let me help you with that. I'm happy to assist."
        score = engine.score_tone(response, "prompt")
        assert score >= 4

    def test_score_tone_negative_indicators(self):
        """Test score_tone with negative language."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        response = "Obviously you should have known this. It's just simple."
        score = engine.score_tone(response, "prompt")
        assert score <= 3

    def test_score_tone_with_politeness(self):
        """Test score_tone with polite language."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        response = "Please let me know if you need help. Thank you for your patience."
        score = engine.score_tone(response, "prompt")
        assert score >= 4

    def test_score_completeness_empty_response(self):
        """Test score_completeness with empty response."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        score = engine.score_completeness("", "prompt")
        assert score == 1

    def test_score_completeness_very_short(self):
        """Test score_completeness with very short response."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        score = engine.score_completeness("Short answer", "prompt")
        assert score == 2

    def test_score_completeness_medium_length(self):
        """Test score_completeness with medium length response."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        response = " ".join(["word"] * 50)
        score = engine.score_completeness(response, "prompt")
        assert score == 4

    def test_score_completeness_very_long(self):
        """Test score_completeness with very long response."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        response = " ".join(["word"] * 150)
        score = engine.score_completeness(response, "prompt")
        assert score == 5

    def test_score_completeness_with_structure(self):
        """Test score_completeness with structured content."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        response = "1) First point 2) Second point"
        score = engine.score_completeness(response, "prompt")
        assert score >= 3

    def test_identify_defects_all_defects(self):
        """Test identify_defects with all defect types."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        response_data = {
            "response": "word " * 30,  # For redundancy check
            "accuracy": 1,
            "reasoning": 1,
            "tone": 1,
            "completeness": 1,
        }

        defects = engine.identify_defects(response_data)
        assert "D01" in defects  # Logical defect
        assert "D02" in defects  # Factual defect
        assert "D03" in defects  # Tone defect
        assert "D04" in defects  # Incomplete
        assert "D05" in defects  # Redundancy

    def test_identify_defects_redundancy(self):
        """Test identify_defects for redundancy detection."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        # Create a response with low unique word ratio
        response_data = {
            "response": "same same same same same " * 10,
            "accuracy": 5,
            "reasoning": 5,
            "tone": 5,
            "completeness": 5,
        }

        defects = engine.identify_defects(response_data)
        assert "D05" in defects  # Redundancy defect

    def test_identify_defects_no_defects(self):
        """Test identify_defects with perfect scores."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        response_data = {
            "response": "This is a well-written response with good variety of words and concepts.",
            "accuracy": 5,
            "reasoning": 5,
            "tone": 5,
            "completeness": 5,
        }

        defects = engine.identify_defects(response_data)
        assert len(defects) == 0

    def test_identify_defects_empty_response(self):
        """Test identify_defects with empty response."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        response_data = {
            "response": "",
            "accuracy": 5,
            "reasoning": 5,
            "tone": 5,
            "completeness": 5,
        }

        defects = engine.identify_defects(response_data)
        # Should not crash with empty response
        assert isinstance(defects, list)

    def test_score_batch_multiple_responses(self):
        """Test score_batch with multiple responses."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        responses = [
            {"prompt": "Q1", "response": "Answer 1"},
            {"prompt": "Q2", "response": "Answer 2"},
            {"prompt": "Q3", "response": "Answer 3"},
        ]

        scored = engine.score_batch(responses)
        assert len(scored) == 3
        for item in scored:
            # Check for standardized keys
            assert "accuracy" in item or "score_accuracy" in item
            assert "overall_score" in item
            assert "defects" in item

    def test_score_batch_weighted_calculation(self):
        """Test score_batch calculates weighted scores correctly."""
        criteria = [
            RubricCriterion(key="accuracy", weight=0.4, type="rule", params={}),
            RubricCriterion(key="reasoning", weight=0.3, type="rule", params={}),
            RubricCriterion(key="tone", weight=0.15, type="rule", params={}),
            RubricCriterion(key="completeness", weight=0.15, type="rule", params={}),
        ]
        engine = ScoringEngine(Rubric(criteria=criteria))

        responses = [{"prompt": "Test", "response": "Test response"}]
        scored = engine.score_batch(responses)

        # Verify weighted calculation using standardized keys
        expected = (
            scored[0].get("accuracy", 0.0) * 0.40
            + scored[0].get("reasoning", 0.0) * 0.30
            + scored[0].get("tone", 0.0) * 0.15
            + scored[0].get("completeness", 0.0) * 0.15
        )
        assert abs(scored[0]["overall_score"] - expected) < 0.01

    def test_save_scores_creates_directory(self):
        """Test save_scores creates directory if it doesn't exist."""
        import tempfile
        import os
        import shutil

        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        temp_dir = tempfile.mkdtemp()
        try:
            filepath = os.path.join(temp_dir, "subdir", "scores.csv")
            scored = [
                {
                    "accuracy": 5,
                    "reasoning": 4,
                    "tone": 5,
                    "completeness": 4,
                    "overall_score": 4.5,
                    "defects": "",
                }
            ]

            engine.save_scores(scored, filepath)
            assert os.path.exists(filepath)
        finally:
            shutil.rmtree(temp_dir)

    def test_save_scores_empty_list(self):
        """Test save_scores with empty list."""
        criteria = [RubricCriterion(key="accuracy", weight=1.0, type="rule", params={})]
        engine = ScoringEngine(Rubric(criteria=criteria))

        # Should not crash, just log warning
        engine.save_scores([], "test.csv")

    def test_standalone_score_responses_function(self):
        """Test standalone score_responses function."""
        responses = [
            {"prompt": "Q1", "response": "Answer 1"},
            {"prompt": "Q2", "response": "Answer 2"},
        ]

        scored = score_responses(responses, config=None)
        assert len(scored) == 2
        assert all("overall_score" in item for item in scored)

    def test_standalone_score_responses_with_config(self):
        """Test standalone score_responses function with config."""
        responses = [{"prompt": "Test", "response": "Answer"}]
        config = {"test": "config"}

        scored = score_responses(responses, config=config)
        assert len(scored) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=evaluation.scoring_engine", "--cov-report=term-missing"])
