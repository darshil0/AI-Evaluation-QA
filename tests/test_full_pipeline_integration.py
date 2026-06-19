import json
import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest

from evaluation.evaluation_pipeline import EvaluationPipeline


@pytest.fixture
def integration_config():
    return {
        "version": "2.3",
        "model": "gpt-4",
        "models": {"primary": {"provider": "openai", "model_name": "gpt-4", "api_key": "test_key"}},
        "api": {"max_retries": 3, "rate_limit_rpm": 60},
        "scoring": {"criteria": {"accuracy": {"weight": 0.5}, "reasoning": {"weight": 0.5}}},
        "output": {
            "directory": "test_reports_integration",
            "checkpoint_directory": "test_checkpoints_integration",
        },
    }


@pytest.mark.asyncio
async def test_full_pipeline_integration(integration_config):
    # Setup temporary prompt file
    prompts_data = {
        "metadata": {"version": "1.0", "description": "Integration test prompts"},
        "prompts": [{"id": "p1", "category": "test", "text": "What is 2+2?"}],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(prompts_data, f)
        prompt_file = f.name

    try:
        pipeline = EvaluationPipeline(integration_config)

        # Mocking the network call inside PromptRunner
        mock_response = {
            "prompt_id": "p1",
            "prompt": "What is 2+2?",
            "response": "2+2 is 4",
            "model": "gpt-4",
            "status": "success",
            "prompt_tokens": 10,
            "response_tokens": 10,
        }

        with patch.object(
            pipeline.prompt_runner, "run_prompts", new_callable=AsyncMock
        ) as mock_run:
            mock_run.return_value = [mock_response]

            # Run the pipeline
            # We need to mock report generation to avoid file I/O during test
            with patch.object(
                pipeline.report_generator, "generate_reports_async", new_callable=AsyncMock
            ):
                # We also want to check if it actually scores
                result_df = await pipeline._run_async(prompt_file)

                assert result_df is not None
                assert len(result_df) == 1
                assert "overall_score" in result_df.columns
                assert result_df.iloc[0]["response"] == "2+2 is 4"
                assert result_df.iloc[0]["cost"] > 0

    finally:
        if os.path.exists(prompt_file):
            os.unlink(prompt_file)
        import shutil

        if os.path.exists("test_reports_integration"):
            shutil.rmtree("test_reports_integration")
        if os.path.exists("test_checkpoints_integration"):
            shutil.rmtree("test_checkpoints_integration")
