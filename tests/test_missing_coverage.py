import asyncio
import json
from unittest.mock import patch

import aiohttp
import pandas as pd
import pytest

from evaluation.cost_tracker import CostTracker
from evaluation.error_handler import EvaluationErrorHandler
from evaluation.evaluation_pipeline import EvaluationPipeline
from evaluation.prompt_runner import PromptRunner
from evaluation.report_generator import ReportGenerator
from evaluation.scoring_engine import ScoringEngine
from scripts.data_validator import DataValidator
from scripts.prompt_loader import PromptLoader


@pytest.mark.asyncio
async def test_prompt_runner_anthropic_provider():
    config = {
        "models": {"primary": {"provider": "anthropic", "model_name": "claude-3-opus-20240229"}}
    }
    runner = PromptRunner(config=config)
    with patch("evaluation.clients.anthropic_client.AnthropicClient.execute_prompt") as mock_exec:
        mock_exec.return_value = {"status": "success", "response": "hi"}
        async with aiohttp.ClientSession() as session:
            result = await runner.execute_prompt_async({"text": "hello"}, session)
            assert result["response"] == "hi"


@pytest.mark.asyncio
async def test_prompt_runner_unsupported_provider():
    config = {"models": {"primary": {"provider": "unknown"}}}
    runner = PromptRunner(config=config)
    async with aiohttp.ClientSession() as session:
        with pytest.raises(ValueError, match="Unsupported provider: unknown"):
            await runner.execute_prompt_async({"text": "hello"}, session)


def test_scoring_engine_print_summary(capsys):
    engine = ScoringEngine()
    engine.scores = [
        {"overall_score": 4.5, "defects": "D01"},
        {"overall_score": 3.0, "defects": ""},
    ]
    engine.print_summary()
    captured = capsys.readouterr()
    assert "SCORING SUMMARY" in captured.out
    assert "Overall Average Score: 3.75" in captured.out


def test_scoring_engine_print_summary_empty(capsys):
    engine = ScoringEngine()
    engine.scores = []
    engine.print_summary()
    captured = capsys.readouterr()
    assert "No scores to summarize" in captured.out


def test_scoring_engine_save_scores_legacy(tmp_path):
    engine = ScoringEngine()
    engine.scores = [{"a": 1}]
    filepath = tmp_path / "test.csv"
    engine.save_scores(str(filepath))
    assert filepath.exists()


def test_scoring_engine_save_scores_invalid():
    engine = ScoringEngine()
    with pytest.raises(ValueError, match="filepath must be provided"):
        engine.save_scores([{"a": 1}])


@pytest.mark.asyncio
async def test_evaluation_pipeline_run_from_loop():
    pipeline = EvaluationPipeline()
    # Mocking _run_async to be a coroutine
    with patch.object(pipeline, "_run_async", side_effect=lambda x: asyncio.sleep(0)):
        with pytest.raises(
            RuntimeError, match=r"run\(\) cannot be called from an active event loop"
        ):
            pipeline.run("fake_file.json")


def test_report_generator_load_data_error(tmp_path):
    generator = ReportGenerator(str(tmp_path))
    malformed_csv = tmp_path / "bad.csv"
    malformed_csv.write_text("a,b\n1")
    with patch("csv.DictReader", side_effect=Exception("csv error")):
        data = generator.load_data(str(malformed_csv))
        assert data == []


@pytest.mark.asyncio
async def test_evaluation_pipeline_process_results_no_results():
    pipeline = EvaluationPipeline()
    result = await pipeline.process_results_async([])
    assert result is None


@pytest.mark.asyncio
async def test_evaluation_pipeline_behavioral_happy_path(tmp_path):
    config = {
        "output": {
            "directory": str(tmp_path),
            "checkpoint_directory": str(tmp_path / "checkpoints"),
        },
        "model": "gpt-4",
    }
    pipeline = EvaluationPipeline(config)
    results = [
        {"id": "p1", "text": "hello", "response": "world", "status": "success", "model": "gpt-4"}
    ]
    with (
        patch.object(pipeline.prompt_loader, "load_and_validate") as mock_load,
        patch.object(pipeline.prompt_runner, "run_prompts", return_value=results),
        patch.object(pipeline.report_generator, "generate_reports_async") as mock_gen,
    ):
        mock_load.return_value = {"prompts": [{"id": "p1", "text": "hello"}]}

        df = await pipeline._run_async("fake.json")

        assert df is not None
        assert len(df) == 1
        assert "overall_score" in df.columns
        mock_gen.assert_called_once()


def test_scoring_engine_behavioral_boundaries():
    engine = ScoringEngine()
    report = engine.score_response({"text": "short", "id": "1"}, response_text="no")
    assert report.aggregated_score >= 0
    report = engine.score_response({"text": "long", "id": "2"}, response_text="word " * 1000)
    assert report.aggregated_score >= 0
    with pytest.raises(TypeError):
        engine.score_response("not-a-dict")  # type: ignore


def test_report_generator_behavioral_malformed_data(tmp_path):
    generator = ReportGenerator(str(tmp_path))
    data = [{"prompt_id": "1", "overall_score": 4.0}]
    reports = generator.generate_reports(data)
    assert "html_report" in reports
    assert "executive_summary" in reports
    assert (tmp_path / "evaluation_summary.html").exists()


@pytest.mark.asyncio
async def test_error_handler_value_error():
    handler = EvaluationErrorHandler(max_retries=1)

    async def fail_func():
        raise ValueError("test value error")

    success, result, failed_req = await handler.execute_with_retry(fail_func, "p1")
    assert not success
    assert failed_req is not None
    assert failed_req.error_type == "ValueError"


@pytest.mark.asyncio
async def test_error_handler_generic_exception():
    handler = EvaluationErrorHandler(max_retries=1)

    async def fail_func():
        raise Exception("generic error")

    success, result, failed_req = await handler.execute_with_retry(fail_func, "p1")
    assert not success
    assert failed_req is not None
    assert failed_req.error_type == "Exception"


@pytest.mark.asyncio
async def test_error_handler_retry_success():
    handler = EvaluationErrorHandler(max_retries=2)
    attempts = 0

    async def retry_func():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ConnectionError("fail first")
        return "success"

    success, result, failed_req = await handler.execute_with_retry(retry_func, "p1")
    assert success
    assert result == "success"
    assert attempts == 2


def test_cost_tracker_token_count_error():
    tracker = CostTracker()
    # Check if tracker.encoding is not None before patching
    if tracker.encoding:
        with patch.object(tracker.encoding, "encode", side_effect=Exception("encode error")):
            count = tracker.count_tokens("test")
            assert count == 1  # len("test") // 4
    else:
        count = tracker.count_tokens("test")
        assert count == 1


def test_cost_tracker_normalize_models():
    tracker = CostTracker()
    assert tracker._normalize_model_name("gpt-4-turbo-preview") == "gpt-4-turbo-preview"
    assert tracker._normalize_model_name("gpt-4-turbo") == "gpt-4-turbo-preview"
    assert tracker._normalize_model_name("gpt-3.5-turbo-16k") == "gpt-3.5-turbo"
    assert tracker._normalize_model_name("claude-3-opus") == "claude-opus-4-6"
    assert tracker._normalize_model_name("claude-3-sonnet") == "claude-sonnet-4-6"
    assert tracker._normalize_model_name("claude-3-haiku") == "claude-haiku-4-5-20251001"


def test_prompt_loader_with_schema(tmp_path):
    schema = {"type": "object", "properties": {"a": {"type": "number"}}}
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema))

    loader = PromptLoader(str(schema_path))

    valid_file = tmp_path / "valid.json"
    valid_file.write_text(json.dumps({"a": 1}))
    assert loader.load_and_validate(str(valid_file)) == {"a": 1}

    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text(json.dumps({"a": "not-a-number"}))
    with pytest.raises(ValueError, match="Schema validation failed"):
        loader.load_and_validate(str(invalid_file))


def test_scoring_engine_judge_with_min_max():
    engine = ScoringEngine()
    params = {"min_val": 1, "max_val": 10}
    val, notes = engine._score_judge("The score is 5", params)
    assert val is not None
    assert pytest.approx(val) == 4 / 9

    params = {"min_val": 0, "max_val": 1, "json_key": "score"}
    val, notes = engine._score_judge('{"score": 0.8}', params)
    assert val == 0.8


def test_scoring_engine_rules():
    engine = ScoringEngine()

    # contains_terms
    params = {"rule": "contains_terms", "terms": ["AI", "ML"], "min_match": 1}
    val, notes = engine._score_rule("AI is great", params)
    assert val == 1.0
    val, notes = engine._score_rule("ML is great", params)
    assert val == 1.0
    val, notes = engine._score_rule("Python is great", params)
    assert val == 0.0

    # mentions_entity
    params = {"rule": "mentions_entity", "entity": "OpenAI"}
    val, notes = engine._score_rule("I love OpenAI", params)
    assert val == 1.0
    val, notes = engine._score_rule("I love Anthropic", params)
    assert val == 0.0

    # length_within
    params = {"rule": "length_within", "max_len": 5}
    val, notes = engine._score_rule("one two three four five", params)
    assert val == 1.0
    val, notes = engine._score_rule("one two three four five six", params)
    assert val == 0.0


def test_data_validator_behavioral():
    dv = DataValidator()

    # Test inconsistent grade-score
    df = pd.DataFrame(
        {"prompt_id": ["1"], "response": ["hi"], "overall_score": [5.0], "grade": ["F"]}
    )
    is_valid, issues = dv.validate_dataframe(df, "scored_results")
    assert not is_valid
    assert any("inconsistent" in issue for issue in issues)

    # Test duplicated prompt IDs
    df = pd.DataFrame(
        {
            "prompt_id": ["1", "1"],
            "prompt": ["a", "b"],
            "response": ["c", "d"],
            "timestamp": ["2024-01-01", "2024-01-01"],
        }
    )
    is_valid, issues = dv.validate_dataframe(df, "raw_results")
    assert not is_valid
    assert any("Duplicate" in issue for issue in issues)


def test_evaluation_pipeline_safe_int_conversion():
    pipeline = EvaluationPipeline()
    assert pipeline._safe_int_conversion(10) == 10
    assert pipeline._safe_int_conversion("20") == 20
    assert pipeline._safe_int_conversion(30.5) == 30
    assert pipeline._safe_int_conversion(None) == 0
    assert pipeline._safe_int_conversion(float("nan")) == 0
    assert pipeline._safe_int_conversion(float("inf")) == 0


def test_report_generator_statistics_calculation():
    generator = ReportGenerator()
    data = [
        {"overall_score": 4.0, "score_accuracy": 0.8},
        {"overall_score": 2.0, "score_accuracy": 0.4},
    ]
    stats = generator.calculate_statistics(data)
    assert stats["total_evaluations"] == 2
    assert pytest.approx(stats["mean_overall"]) == 3.0
    assert pytest.approx(stats["mean_accuracy"]) == 3.0  # (0.8+0.4)/2 * 5.0 = 0.6 * 5.0 = 3.0


@pytest.mark.asyncio
async def test_evaluation_pipeline_failure_propagation(tmp_path):
    config = {"output": {"directory": str(tmp_path)}, "model": "gpt-4"}
    pipeline = EvaluationPipeline(config)

    with patch.object(
        pipeline.prompt_loader, "load_and_validate", side_effect=ValueError("Loader error")
    ):
        with pytest.raises(ValueError, match="Loader error"):
            await pipeline._run_async("fake.json")


def test_scoring_engine_edge_case_no_numeric():
    engine = ScoringEngine()
    # Response with no numbers when judge expects numeric fallback
    report = engine.score_response({"text": "test", "id": "1"}, response_text="No numbers here")
    # Should handle it gracefully, likely 0.0 or lowest score
    accuracy_comp = next(c for c in report.components if c.key == "accuracy")
    assert accuracy_comp.normalized is not None


def test_report_generator_low_score_insight(tmp_path):
    generator = ReportGenerator(str(tmp_path))
    data = [{"prompt_id": "1", "overall_score": 1.0}]
    reports = generator.generate_reports(data)
    with open(reports["executive_summary"], "r", encoding="utf-8") as f:
        content = f.read()
    assert "Performance below expectations" in content
