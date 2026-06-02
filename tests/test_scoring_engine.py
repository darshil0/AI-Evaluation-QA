import csv
import os
import tempfile

import pytest

from evaluation.scoring_engine import (
    Rubric,
    RubricCriterion,
    ScoreComponent,
    ScoreReport,
    ScoringEngine,
    score_responses,
)


class TestScoringEngineCoverage:
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

    def test_validate_rubric_warns_on_non_normalized_weights(self):
        engine = ScoringEngine(
            Rubric(
                criteria=[
                    RubricCriterion("accuracy", 2.0, "rule", {}),
                ]
            )
        )
        assert engine.rubric.criteria[0].weight == 2.0

    def test_score_response_rejects_non_dict_prompt_meta(self):
        engine = self.make_engine()
        with pytest.raises(TypeError):
            engine.score_response("not a dict", "response")

    def test_score_response_rejects_non_string_response(self):
        engine = self.make_engine()
        with pytest.raises(TypeError):
            engine.score_response({"prompt": "Q"}, response_text=123)

    def test_score_response_returns_dict_by_default(self):
        engine = self.make_engine()
        result = engine.score_response({"prompt": "Q", "response": "This is a response."})
        assert isinstance(result, dict)
        assert "overall_score" in result
        assert "defects" in result

    def test_score_response_returns_report_when_response_text_passed(self):
        engine = self.make_engine()
        report = engine.score_response({"prompt": "Q"}, response_text="This is a response.")
        assert isinstance(report, ScoreReport)
        assert report.components

    def test_rule_contains_terms(self):
        engine = self.make_engine()
        raw, notes = engine._score_rule(
            "Python testing and automation", {"rule": "contains_terms", "terms": ["Python", "automation"], "min_match": 2}
        )
        assert raw == 1.0
        assert "matched" in notes

    def test_rule_mentions_entity(self):
        engine = self.make_engine()
        raw, notes = engine._score_rule("Hello from Dallas", {"rule": "mentions_entity", "entity": "Dallas"})
        assert raw == 1.0
        assert "present" in notes

    def test_rule_length_within(self):
        engine = self.make_engine()
        raw, notes = engine._score_rule("one two three", {"rule": "length_within", "max_len": 5})
        assert raw == 1.0
        assert "length" in notes

    def test_rule_fallback(self):
        engine = self.make_engine()
        raw, notes = engine._score_rule("text", {"rule": "unknown"})
        assert raw is None
        assert "heuristic" in notes

    def test_judge_json_key_parsing(self):
        engine = self.make_engine()
        text = "```json\n{\"score\": 4}\n```"
        raw, notes = engine._score_judge(text, {"json_key": "score"})
        assert raw is not None
        assert "json key" in notes

    def test_judge_numeric_fallback(self):
        engine = self.make_engine()
        raw, notes = engine._score_judge("final score: 7", {})
        assert raw is not None
        assert "numeric" in notes

    def test_identify_defects_from_low_scores(self):
        engine = self.make_engine()
        defects = engine.identify_defects(
            {
                "response": "word " * 30,
                "accuracy": 1,
                "reasoning": 1,
                "tone": 1,
                "completeness": 1,
            }
        )
        assert {"D01", "D02", "D03", "D04"}.issubset(set(defects))

    def test_identify_defects_redundancy(self):
        engine = self.make_engine()
        defects = engine.identify_defects(
            {
                "response": "same same same same same " * 10,
                "accuracy": 5,
                "reasoning": 5,
                "tone": 5,
                "completeness": 5,
            }
        )
        assert "D05" in defects

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

    def test_load_results_missing_file(self):
        engine = self.make_engine()
        with pytest.raises(FileNotFoundError):
            engine.load_results("does_not_exist.csv")

    def test_save_scores_writes_csv(self):
        engine = self.make_engine()
        scored = [{"accuracy": 5, "overall_score": 4.2, "defects": ""}]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "out", "scores.csv")
            engine.save_scores(scored, path)
            assert os.path.exists(path)
            with open(path, "r", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            assert len(rows) == 1

    def test_save_scores_uses_internal_cache_when_filepath_only(self):
        engine = self.make_engine()
        engine.scores = [{"accuracy": 5, "overall_score": 4.2, "defects": ""}]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "scores.csv")
            engine.save_scores(path)
            assert os.path.exists(path)

    def test_score_responses_function(self):
        scored = score_responses(
            [{"prompt": "Q1", "response": "Answer 1"}, {"prompt": "Q2", "response": "Answer 2"}]
        )
        assert len(scored) == 2
        assert all("overall_score" in item for item in scored)
