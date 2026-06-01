import pytest
import json
from evaluation.scoring_engine import ScoringEngine, Rubric, RubricCriterion, ScoreReport


def test_repro_normalization_ambiguity():
    """Verify that 1-5 scale scores are correctly normalized (not misinterpreted as 1-100)."""
    engine = ScoringEngine()
    # If a judge returns 3 (out of 5), it should be normalized to 0.6 (3 / 5.0)
    assert engine._normalize_value(3) == 0.6


def test_repro_brittle_json_parsing():
    """Verify that Markdown-wrapped JSON parses correctly."""
    rubric = Rubric(
        criteria=[
            RubricCriterion(key="acc", weight=1.0, type="judge", params={"json_key": "score"})
        ]
    )
    engine = ScoringEngine(rubric)
    # LLM response with Markdown block
    response = 'Analysis complete.\n```json\n{"score": 0.95}\n```'
    report = engine.score_response({"id": "1", "response": response})

    # Verify that the JSON key was parsed successfully
    assert "json key 'score' parsed" in report.get("score_acc_notes")


def test_repro_greedy_numeric_extraction():
    """Verify that the last number found is used as the score (avoiding greedy first-number extraction)."""
    rubric = Rubric(criteria=[RubricCriterion(key="acc", weight=1.0, type="judge", params={})])
    engine = ScoringEngine(rubric)
    # The first number is 10 (spurious/context), the second is 0.95 (the intended score)
    response = "I evaluated 10 criteria and the score is 0.95."
    report = engine.score_response({"id": "1", "response": response})

    # The final score should be 0.95, not 10 normalized to 0.1
    assert report.get("score_acc") == 0.95


def test_repro_return_type_inconsistency():
    """Reproduces the issue where return type changes based on arguments."""
    engine = ScoringEngine()

    # Case 1: Dict
    res_dict = engine.score_response({"id": "1", "response": "test"})
    assert isinstance(res_dict, dict)

    # Case 2: ScoreReport
    res_obj = engine.score_response({"id": "1"}, "test")
    assert isinstance(res_obj, ScoreReport)

    # This inconsistency can lead to runtime errors in callers
    with pytest.raises(TypeError):
        res_obj["overall_score"]  # Objects are not subscriptable


def test_repro_zero_weight_rubric():
    """Reproduces behavior when total weight is zero."""
    rubric = Rubric(
        criteria=[
            RubricCriterion(
                key="acc", weight=0.0, type="rule", params={"rule": "length_within", "max_len": 10}
            )
        ]
    )
    engine = ScoringEngine(rubric)
    report = engine.score_response({"id": "1", "response": "Short"})

    # weighted_sum = 1.0 * 0.0 = 0.0
    # total_weight = 0.0 -> uses fallback 1.0 in code
    # aggregated_score = 0.0 / 1.0 = 0.0
    # Even if the rule passed, the score is 0 because weight is 0.
    assert report.get("score_acc") == 1.0
    assert report.get("aggregated_score") == 0.0


def test_repro_unknown_rule_fallback():
    """Reproduces silent failure for unknown rules and keys."""
    rubric = Rubric(
        criteria=[
            RubricCriterion(
                key="unknown_key", weight=1.0, type="rule", params={"rule": "unknown_rule"}
            )
        ]
    )
    engine = ScoringEngine(rubric)
    report = engine.score_response({"id": "1", "response": "test"})

    # raw is None because unknown_rule is not handled
    # heuristic fails because unknown_key is not in RUBRIC_CATEGORIES
    # result is 0.0 without any warning or error raised to the user
    assert report.get("score_unknown_key") == 0.0
    assert "using heuristic for rule: unknown_rule" in report.get("score_unknown_key_notes")
