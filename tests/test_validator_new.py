import pytest

from config.validator import ConfigurationValidator, validate_before_execution, validate_config


def test_validate_yaml_config_not_found():
    with pytest.raises(FileNotFoundError):
        ConfigurationValidator.validate_yaml_config("non_existent.yaml")


def test_validate_config_missing_keys():
    with pytest.raises(ValueError, match="Missing required config key"):
        validate_config({})


def test_validate_config_missing_primary_model():
    config = {"models": {}, "api": {}, "scoring": {}}
    with pytest.raises(ValueError, match="Missing 'primary' model"):
        validate_config(config)


def test_validate_config_invalid_max_retries():
    config = {"models": {"primary": {}}, "api": {"max_retries": -1}, "scoring": {}}
    with pytest.raises(ValueError, match="max_retries must be non-negative"):
        validate_config(config)


def test_validate_config_invalid_rate_limit():
    config = {
        "models": {"primary": {}},
        "api": {"max_retries": 3, "rate_limit_rpm": 0},
        "scoring": {},
    }
    with pytest.raises(ValueError, match="rate_limit_rpm must be positive"):
        validate_config(config)


def test_validate_before_execution_missing_prompts(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    results = validate_before_execution(prompts_file="non_existent.json")
    assert results["prompts_valid"] is False
    assert any("not found" in e for e in results["errors"])
