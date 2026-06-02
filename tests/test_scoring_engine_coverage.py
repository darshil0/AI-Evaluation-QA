import csv
import os
import tempfile

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
    def make_engine(self):
        criteria = [
            RubricCriterion(key="accuracy", weight=0.4, type="rule", params={}),
            RubricCriterion(key="reasoning", weight=0.3, type="rule", params={}),
            RubricCriterion(key="tone", weight=0.15, type="rule", params={}),
            RubricCriterion(key="completeness", weight=0.15, type="rule", params={}),
        ]
        return ScoringEngine(Rubric(criteria=criteria))

    def test_from_config_builds_rubric(self):
        engine = ScoringEngine.from_config(
            {
                "scoring": {
                    "criteria": {
                        "accuracy": {"type": "rule", "weight": 0.5, "params": {}},
                        "judge_score": {"type": "judge", "weight": 0.5, "params": {"json_key": "score"}},
                    }
                }
            }
        )
        assert isinstance(engine, ScoringEngine)
        assert len(engine.rubric.criteria) == 2

    def test_validate_rubric_rejects_empty(self):
        with pytest.raises(ValueError):
            ScoringEngine(Rubric(criteria=[]))

    def test_score_accuracy_empty_response(self):
        engine = self.make_engine()
        assert engine.score_accuracy("", "prompt") == 1

    def test_score_accuracy_uncertain_response(self):
        engine = self.make_engine()
        assert engine.score_accuracy("I don't know the answer", "prompt") == 2

    def test_score_accuracy_detailed_response(self):
        engine = self.make_engine()
        response = (
            "This is a very detailed response with more than twenty words explaining "
            "the concept thoroughly and specifically with factual information because it "
            "provides comprehensive coverage."
        )
        assert engine.score_accuracy(response, "prompt") >= 4

    def test_score_reasoning_empty_response(self):
        engine = self.make_engine()
        assert engine.score_reasoning("", "prompt") == 1

    def test_score_reasoning_with_logical_connectors(self):
        engine = self.make_engine()
        response = "This happens because of X. Therefore, Y occurs. Thus, we can conclude Z."
        assert engine.score_reasoning(response, "prompt") >= 4

    def test_score_reasoning_no_connectors(self):
        engine = self.make_engine()
        assert engine.score_reasoning("This is a simple statement.", "prompt") <= 3

    def test_score_reasoning_with_structure(self):
        engine = self.make_engine()
        response = "First, we do this. Second, we do that. • Point one - Point two"
        assert engine.score_reasoning(response, "prompt") >= 3

    def test_score_tone_empty_response(self):
        engine = self.make_engine()
        assert engine.score_tone("", "prompt") == 1

    def test_score_tone_positive_indicators(self):
        engine = self.make_engine()
        response = "I understand your concern. Let me help you with that. I'm happy to assist."
        assert engine.score_tone(response, "prompt") >= 4

    def test_score_tone_negative_indicators(self):
        engine = self.make_engine()
        response = "Obviously you should have known this. It's just simple."
        assert engine.score_tone(response, "prompt") <= 3

    def test_score_tone_with_politeness(self):
        engine = self.make_engine()
        response = "Please let me know if you need help. Thank you for your patience."
        assert engine.score_tone(response, "prompt") >= 4

    def test_score_completeness_empty_response(self):
        engine = self.make_engine()
        assert engine.score_completeness("", "prompt") == 1

    def test_score_completeness_very_short(self):
        engine = self.make_engine()
        assert engine.score_completeness("Short answer", "prompt") == 2

    def test_score_completeness_medium_length(self):
        engine = self.make_engine()
        response = " ".join(["word"] * 50)
        assert engine.score_completeness(response, "prompt") == 4

    def test_score_completeness_very_long(self):
        engine = self.make_engine()
        response = " ".join(["word"] * 150)
        assert engine.score_completeness(response, "prompt") == 5

    def test_score_completeness_with_structure(self):
        engine = self.make_engine()
        response = "1) First point 2) Second point"
        assert engine.score_completeness(response, "prompt") >= 3

    def test_score_response_rejects_non_dict(self):
        engine = self.make_engine()
        with pytest.raises(TypeError):
            engine.score_response("not a dict", "response")

    def test_score_response_rejects_non_string_response(self):
        engine = self.make_engine()
        with pytest.raises(TypeError):
            engine.score_response({"prompt": "Q"}, response_text=123)

    def test_score_response_dict_output(self):
        engine = self.make_engine()
        result = engine.score_response({"prompt": "Q", "response": "Answer"})
        assert isinstance(result, dict)
        assert "overall_score" in result
        assert "defects" in result

    def test_score_response_report_output(self):
        engine = self.make_engine()
        report = engine.score_response({"prompt": "Q"}, response_text="Answer")
        assert isinstance(report, ScoreReport)
        assert report.components

    def test_score_rule_contains_terms(self):
        engine = self.make_engine()
        raw, notes = engine._score_rule(
            "Python testing and automation",
            {"rule": "contains_terms", "terms": ["Python", "automation"], "min_match": 2},
        )
        assert raw == 1.0
        assert "matched" in notes

    def test_score_rule_mentions_entity(self):
        engine = self.make_engine()
        raw, notes = engine._score_rule("Hello from Dallas", {"rule": "mentions_entity", "entity": "Dallas"})
        assert raw == 1.0
        assert "present" in notes

    def test_score_rule_length_within(self):
        engine = self.make_engine()
        raw, notes = engine._score_rule("one two three", {"rule": "length_within", "max_len": 5})
        assert raw == 1.0
        assert "length" in notes

    def test_score_rule_fallback(self):
        engine = self.make_engine()
        raw, notes = engine._score_rule("text", {"rule": "unknown"})
        assert raw is None
        assert "heuristic" in notes

    def test_score_judge_json_key_parsing(self):
        engine = self.make_engine()
        text = '```json\n{"score": 4}\n```'
        raw, notes = engine._score_judge(text, {"json_key": "score"})
        assert raw is not None
        assert "json key" in notes

    def test_score_judge_numeric_fallback(self):
        engine = self.make_engine()
        raw, notes = engine._score_judge("final score: 7", {})
        assert raw is not None
        assert "numeric" in notes

    def test_identify_defects_all_defects(self):
        engine = self.make_engine()
        response_data = {
            "response": "word " * 30,
            "accuracy": 1,
            "reasoning": 1,
            "tone": 1,
            "completeness": 1,
        }
        defects = engine.identify_defects(response_data)
        assert "D01" in defects
        assert "D02" in defects
        assert "D03" in defects
        assert "D04" in defects
        assert "D05" in defects

    def test_identify_defects_redundancy(self):
        engine = self.make_engine()
        response_data = {
            "response": "same same same same same " * 10,
            "accuracy": 5,
            "reasoning": 5,
            "tone": 5,
            "completeness": 5,
        }
        defects = engine.identify_defects(response_data)
        assert "D05" in defects

    def test_identify_defects_no_defects(self):
        engine = self.make_engine()
        response_data = {
            "response": "This is a well-written response with good variety of words and concepts.",
            "accuracy": 5,
            "reasoning": 5,
            "tone": 5,
            "completeness": 5,
        }
        assert engine.identify_defects(response_data) == []

    def test_identify_defects_empty_response(self):
        engine = self.make_engine()
        response_data = {
            "response": "",
            "accuracy": 5,
            "reasoning": 5,
            "tone": 5,
            "completeness": 5,
        }
        defects = engine.identify_defects(response_data)
        assert isinstance(defects, list)

    def test_report_to_dict_and_integrity(self):
        engine = self.make_engine()
        report = ScoreReport(
            prompt_id=1,
            prompt_text="Q",
            model="m",
            components=[ScoreComponent("accuracy", 1.0, 1.0, 0.4, "ok")],
            aggregated_score=1.0,
            metadata={"extra": "x"},
        )
        data = engine.report_to_dict(report)
        assert data["score_accuracy"] == 1.0
        assert engine.validate_report_integrity(report) is True
        assert engine.validate_report_integrity({}) is False

    def test_score_batch_multiple_responses(self):
        engine = self.make_engine()
        responses = [
            {"prompt": "Q1", "response": "Answer 1"},
            {"prompt": "Q2", "response": "Answer 2"},
            {"prompt": "Q3", "response": "Answer 3"},
        ]
        scored = engine.score_batch(responses)
        assert len(scored) == 3
        for item in scored:
            assert "overall_score" in item
            assert "defects" in item

    def test_score_batch_weighted_calculation(self):
        engine = self.make_engine()
        scored = engine.score_batch([{"prompt": "Test", "response": "Test response"}])
        assert 0.0 <= scored[0]["overall_score"] <= 5.0

    def test_load_results_missing_file(self):
        engine = self.make_engine()
        with pytest.raises(FileNotFoundError):
            engine.load_results("does_not_exist.csv")

    def test_save_scores_creates_directory(self):
        engine = self.make_engine()
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = os.path.join(temp_dir, "subdir", "scores.csv")
            scored = [{"accuracy": 5, "overall_score": 4.5, "defects": ""}]
            engine.save_scores(scored, filepath)
            assert os.path.exists(filepath)

    def test_save_scores_empty_list(self):
        engine = self.make_engine()
        engine.save_scores([], "test.csv")

    def test_save_scores_filepath_only(self):
        engine = self.make_engine()
        engine.scores = [{"accuracy": 5, "overall_score": 4.2, "defects": ""}]
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = os.path.join(temp_dir, "scores.csv")
            engine.save_scores(filepath)
            assert os.path.exists(filepath)

    def test_standalone_score_responses_function(self):
        responses = [
            {"prompt": "Q1", "response": "Answer 1"},
            {"prompt": "Q2", "response": "Answer 2"},
        ]
        scored = score_responses(responses, config=None)
        assert len(scored) == 2
        assert all("overall_score" in item for item in scored)

    def test_standalone_score_responses_with_config(self):
        responses = [{"prompt": "Test", "response": "Answer"}]
        config = {
            "scoring": {
                "criteria": {
                    "accuracy": {"type": "rule", "weight": 1.0, "params": {}}
                }
            }
        }
        scored = score_responses(responses, config=config)
        assert len(scored) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=evaluation.scoring_engine", "--cov-report=term-missing"])
