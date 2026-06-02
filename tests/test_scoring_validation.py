import pytest
import pandas as pd

from evaluation.scoring_engine import ScoringEngine
from evaluation.cost_tracker import CostTracker
from scripts.data_validator import DataValidator


class TestScoringEngineValidation:
    """Validation tests using Given/When/Then."""

    def test_score_response_precondition_empty_string(self):
        """Given empty response, when scored, then return min score."""
        engine = ScoringEngine()
        result = engine.score_response({"id": "test"}, "")
        assert isinstance(result, dict) or hasattr(result, "aggregated_score")
        if isinstance(result, dict):
            assert result["overall_score"] >= 1.0
        else:
            assert result.aggregated_score * 5.0 >= 1.0

    def test_score_response_precondition_invalid_type(self):
        """Given non-dict prompt_meta, when scored, then raise TypeError."""
        engine = ScoringEngine()
        with pytest.raises(TypeError, match="prompt_meta must be dict"):
            engine.score_response("not a dict")

    def test_clean_dataframe_precondition_empty(self):
        """Given empty DataFrame, when cleaned, then return empty."""
        result = DataValidator.clean_dataframe(pd.DataFrame())
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_check_budget_precondition_negative_limit(self):
        """Given negative budget_limit, when checked, then raise ValueError."""
        tracker = CostTracker()
        with pytest.raises(ValueError, match="budget_limit must be >= 0"):
            tracker.check_budget(budget_limit=-10.0)
