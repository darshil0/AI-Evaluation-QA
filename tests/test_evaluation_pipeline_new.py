from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from evaluation.evaluation_pipeline import EvaluationPipeline


@pytest.fixture
def pipeline_config():
    return {
        "model": "gpt-4",
        "evaluation": {"budget_limit": 10.0},
        "output": {"directory": "test_reports", "checkpoint_directory": "test_checkpoints"},
    }


def test_pipeline_init(pipeline_config):
    pipeline = EvaluationPipeline(pipeline_config)
    assert pipeline.config == pipeline_config
    assert pipeline.cost_tracker.budget_limit == 10.0


@pytest.mark.asyncio
async def test_save_checkpoint(pipeline_config, tmp_path):
    checkpoint_dir = tmp_path / "checkpoints"
    pipeline_config["output"]["checkpoint_directory"] = str(checkpoint_dir)
    pipeline = EvaluationPipeline(pipeline_config)

    results = [{"id": "1", "response": "test"}, {"id": "2", "response": "test2"}]
    pipeline._save_checkpoint(results, "test_checkpoint.csv")

    checkpoint_file = checkpoint_dir / "test_checkpoint.csv"
    assert checkpoint_file.exists()
    df = pd.read_csv(checkpoint_file)
    assert len(df) == 2


@pytest.mark.asyncio
async def test_process_results_async(pipeline_config):
    pipeline = EvaluationPipeline(pipeline_config)

    results = [
        {
            "prompt_id": "test_001",
            "status": "success",
            "response": "This is a good response.",
            "prompt_tokens": 10,
            "response_tokens": 20,
            "model": "gpt-4",
        }
    ]

    with patch.object(pipeline.scoring_engine, "score_response") as mock_score:
        mock_report = MagicMock()
        mock_report.metadata = {"response": "This is a good response."}
        mock_score.return_value = mock_report

        with patch.object(pipeline.scoring_engine, "report_to_dict") as mock_report_to_dict:
            mock_report_to_dict.return_value = {
                "overall_score": 4.5,
                "score_accuracy": 5,
                "score_reasoning": 4,
                "score_tone": 5,
                "score_completeness": 4,
                "defects": "",
            }

            final_df = await pipeline.process_results_async(results)

            assert final_df is not None
            assert len(final_df) == 1
            assert "overall_score" in final_df.columns
            assert "cost" in final_df.columns


def test_safe_int_conversion():
    pipeline = EvaluationPipeline()
    assert pipeline._safe_int_conversion(10) == 10
    assert pipeline._safe_int_conversion("10") == 10
    assert pipeline._safe_int_conversion(10.5) == 10
    assert pipeline._safe_int_conversion(None) == 0
    assert pipeline._safe_int_conversion(float("nan")) == 0
    assert pipeline._safe_int_conversion(float("inf")) == 0


@pytest.mark.asyncio
async def test_run_pipeline_async(pipeline_config, tmp_path):
    # Mocking components to avoid real API calls
    pipeline = EvaluationPipeline(pipeline_config)

    with patch.object(pipeline.prompt_loader, "load_and_validate") as mock_load:
        mock_load.return_value = {"prompts": [{"id": "p1", "text": "test"}]}

        with patch.object(
            pipeline.prompt_runner, "run_prompts", new_callable=AsyncMock
        ) as mock_run:
            mock_run.return_value = [
                {
                    "prompt_id": "p1",
                    "status": "success",
                    "response": "resp",
                    "prompt_tokens": 5,
                    "response_tokens": 5,
                }
            ]

            with patch.object(
                pipeline, "process_results_async", new_callable=AsyncMock
            ) as mock_process:
                mock_df = pd.DataFrame([{"prompt_id": "p1", "overall_score": 4.0, "cost": 0.01}])
                mock_process.return_value = mock_df

                with patch.object(
                    pipeline.report_generator, "generate_reports_async", new_callable=AsyncMock
                ) as mock_gen:
                    result_df = await pipeline._run_async("dummy_path")

                    assert result_df is not None
                    assert len(result_df) == 1
                    mock_gen.assert_called_once()


def test_run_pipeline_sync(pipeline_config):
    pipeline = EvaluationPipeline(pipeline_config)
    with patch.object(pipeline, "_run_async", new_callable=AsyncMock) as mock_run_async:
        mock_run_async.return_value = pd.DataFrame([{"result": "ok"}])
        result = pipeline.run("dummy_path")
        assert len(result) == 1
