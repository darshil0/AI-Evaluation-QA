import pytest
import yaml

from config.config_loader import ConfigError, ConfigLoader


@pytest.fixture
def sample_config():
    return {
        "models": {"primary": {"provider": "openai", "model_name": "gpt-4", "temperature": 0.7}},
        "api": {"max_retries": 3, "rate_limit_rpm": 60},
        "scoring": {
            "criteria": {
                "accuracy": {"weight": 0.3},
                "reasoning": {"weight": 0.3},
                "tone": {"weight": 0.2},
                "completeness": {"weight": 0.2},
            }
        },
    }


def test_load_valid_config(tmp_path, sample_config, monkeypatch):
    """Test loading valid configuration"""
    config_file = tmp_path / "settings.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(sample_config, f)

    # Mock environment variable
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")

    config = ConfigLoader.load(str(config_file))
    assert config["models"]["primary"]["provider"] == "openai"


def test_missing_config_file():
    """Test error on missing config file"""
    with pytest.raises(ConfigError, match="Configuration file not found"):
        ConfigLoader.load("nonexistent.yaml")


def test_missing_required_fields(tmp_path, monkeypatch):
    """Test error on missing required fields"""
    config_file = tmp_path / "settings.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump({"models": {}}, f)

    monkeypatch.setenv("OPENAI_API_KEY", "test_key")

    with pytest.raises(ConfigError, match="Missing required field"):
        ConfigLoader.load(str(config_file))


def test_invalid_provider(tmp_path, sample_config, monkeypatch):
    """Test error on invalid provider"""
    sample_config["models"]["primary"]["provider"] = "invalid_provider"
    config_file = tmp_path / "settings.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(sample_config, f)

    with pytest.raises(ConfigError, match="Invalid provider"):
        ConfigLoader.load(str(config_file))


def test_invalid_weights(tmp_path, sample_config, monkeypatch):
    """Test error when dimension weights don't sum to 1.0"""
    sample_config["scoring"]["criteria"]["accuracy"]["weight"] = 0.5
    config_file = tmp_path / "settings.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(sample_config, f)

    monkeypatch.setenv("OPENAI_API_KEY", "test_key")

    with pytest.raises(ConfigError, match="weights must sum to 1.0"):
        ConfigLoader.load(str(config_file))


def test_invalid_max_retries(tmp_path, sample_config, monkeypatch):
    """Test error on invalid max_retries value"""
    sample_config["api"]["max_retries"] = 20
    config_file = tmp_path / "settings.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(sample_config, f)

    monkeypatch.setenv("OPENAI_API_KEY", "test_key")

    with pytest.raises(ConfigError, match="max_retries must be an integer between"):
        ConfigLoader.load(str(config_file))


def test_missing_api_key(tmp_path, sample_config, monkeypatch):
    """Test error on missing API key"""
    config_file = tmp_path / "settings.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(sample_config, f)

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_API_KEY", raising=False)

    with pytest.raises(ConfigError, match="Missing environment variable"):
        ConfigLoader.load(str(config_file))
