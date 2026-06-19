import pytest
import pandas as pd
from pathlib import Path
import json


def test_end_to_end_pipeline(tmp_path, monkeypatch):
    """Test complete evaluation pipeline"""
    from config.config_loader import ConfigLoader
    from evaluation.scoring_engine import ScoringEngine
    from evaluation.report_generator import ReportGenerator

    # Setup mock data
    results_df = pd.DataFrame(
        {
            "prompt_id": ["P1", "P2", "P3"],
            "prompt": ["Test 1", "Test 2", "Test 3"],
            "response": ["Response 1", "Response 2", "Response 3"],
        }
    )

    # Create mock config
    config_file = tmp_path / "settings.yaml"
    import yaml

    config = {
        "models": {"primary": {"provider": "openai", "model_name": "gpt-4", "temperature": 0.7}},
        "api": {"max_retries": 3},
        "scoring": {
            "criteria": {
                "accuracy": {"weight": 0.3},
                "reasoning": {"weight": 0.3},
                "tone": {"weight": 0.2},
                "completeness": {"weight": 0.2},
            },
            "automated_scoring": {"use_llm_judge": False},
            "thresholds": {"excellent": 4.5, "good": 3.5, "acceptable": 2.5, "poor": 1.5},
        },
    }
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f)

    monkeypatch.setenv("OPENAI_API_KEY", "test_key")

    # Load config
    from evaluation.scoring_engine import Rubric, RubricCriterion

    loaded_config = ConfigLoader.load(str(config_file))

    # Score responses
    criteria = [
        RubricCriterion(key=k, weight=v["weight"], type="rule", params={})
        for k, v in loaded_config["scoring"]["criteria"].items()
    ]
    rubric = Rubric(criteria=criteria)
    engine = ScoringEngine(rubric)

    results_df["scored_output"] = results_df["response"].apply(
        lambda x: engine.score_response({"id": "test"}, x)
    )
    scored_df = pd.json_normalize(
        results_df["scored_output"].apply(lambda x: engine.report_to_dict(x))
    )

    # Verify scoring
    assert "aggregated_score" in scored_df.columns
    assert len(scored_df) == 3

    # Generate reports
    report_dir = tmp_path / "reports"
    generator = ReportGenerator(str(report_dir))
    reports = generator.generate_reports(scored_df)

    # Verify reports
    assert "executive_summary" in reports
    assert Path(reports["executive_summary"]).exists()


def test_prompt_validation_pipeline(tmp_path):
    """Test prompt validation and loading"""
    from scripts.prompt_loader import PromptLoader

    # Create valid prompt file
    prompt_file = tmp_path / "prompts.json"
    prompts_data = {
        "metadata": {"version": "1.0", "description": "Test prompts"},
        "prompts": [
            {"id": "P1", "text": "This is a test prompt", "category": "test", "difficulty": "easy"},
            {
                "id": "P2",
                "text": "This is another test prompt",
                "category": "test",
                "difficulty": "medium",
            },
        ],
    }

    with open(prompt_file, "w", encoding="utf-8") as f:
        json.dump(prompts_data, f)

    # Load and validate
    loader = PromptLoader()
    loaded_data = loader.load_and_validate(str(prompt_file))

    assert len(loaded_data["prompts"]) == 2
    assert loaded_data["prompts"][0]["id"] == "P1"
    assert loaded_data["metadata"]["version"] == "1.0"
