"""
Unit tests for cost tracker (unified).
"""

import pytest

from evaluation.cost_tracker import CostTracker


class TestCostTracker:
    """Test cost tracker."""

    def test_calculate_cost_basic(self):
        """Test basic cost calculation."""
        tracker = CostTracker()

        cost = tracker.calculate_cost("gpt-4", 1000, 500)

        assert cost > 0
        assert tracker.total_cost == cost
        assert len(tracker.usage_log) == 1

    def test_calculate_cost_accumulation(self):
        """Test cost accumulation across calls."""
        tracker = CostTracker()

        cost1 = tracker.calculate_cost("gpt-4", 1000, 500)
        cost2 = tracker.calculate_cost("gpt-4", 2000, 1000)

        assert tracker.total_cost == pytest.approx(cost1 + cost2)
        assert len(tracker.usage_log) == 2

    def test_budget_alert(self):
        """Test budget alert triggering."""
        tracker = CostTracker(budget_limit=0.01)

        # This should trigger budget alert
        tracker.calculate_cost("gpt-4", 1000000, 1000000)

        assert tracker.total_cost > tracker.budget_limit
        assert any(a["type"] == "error" for a in tracker.alerts)

    def test_normalize_model_name(self):
        """Test model name normalization."""
        tracker = CostTracker()

        assert tracker._normalize_model_name("gpt-4-turbo-preview") == "gpt-4-turbo"
        assert tracker._normalize_model_name("claude-3-sonnet-20240229") == "claude-sonnet-4"
        assert tracker._normalize_model_name("gpt-3.5-turbo-0125") == "gpt-3.5-turbo"

    def test_get_summary(self):
        """Test summary generation."""
        tracker = CostTracker(budget_limit=10.0)

        tracker.calculate_cost("gpt-4", 1000, 500)
        tracker.calculate_cost("gpt-4", 2000, 1000)

        summary = tracker.get_summary()

        assert summary["total_calls"] == 2
        assert summary["total_input_tokens"] == 3000
        assert summary["total_output_tokens"] == 1500
        assert summary["total_cost"] > 0
        assert summary["budget_limit"] == 10.0

    def test_track_request(self):
        """Test text-based request tracking."""
        tracker = CostTracker(model_name="gpt-4")
        result = tracker.track_request("Hello", "World!")

        assert result["input_tokens"] > 0
        assert result["output_tokens"] > 0
        assert result["cost"] > 0
        assert tracker.total_cost == result["cost"]
