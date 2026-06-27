import os
import tempfile

import pytest
import yaml

from config.config_loader import ConfigError, ConfigLoader, ConfigVersionError


def test_config_loader_incompatible_version():
    # Version 1.0 should be migrated to 2.3, not raise error if it can be migrated
    # But if it's explicitly below MIN_COMPATIBLE_VERSION after possible migration?
    # Actually _check_version_compatibility is called BEFORE _migrate_config

    config_low = {
        "version": "0.1",
        "models": {"primary": {"provider": "openai", "model_name": "gpt-4"}},
        "api": {"max_retries": 3},
        "scoring": {"criteria": {"accuracy": {"weight": 1.0}}},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_low, f)
        temp_file = f.name

    try:
        # 0.1 < 2.0
        with pytest.raises(ConfigVersionError):
            ConfigLoader.load(temp_file)
    finally:
        os.unlink(temp_file)


def test_config_loader_invalid_yaml():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("invalid: yaml: :")
        temp_file = f.name
    try:
        with pytest.raises(ConfigError, match="Invalid YAML"):
            ConfigLoader.load(temp_file)
    finally:
        os.unlink(temp_file)


def test_config_loader_not_a_dict():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("- item1\n- item2")
        temp_file = f.name
    try:
        with pytest.raises(ConfigError, match="root must be a mapping"):
            ConfigLoader.load(temp_file)
    finally:
        os.unlink(temp_file)


def test_config_loader_missing_fields():
    config = {"version": "2.3"}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        temp_file = f.name
    try:
        with pytest.raises(ConfigError, match="Missing required field"):
            ConfigLoader.load(temp_file)
    finally:
        os.unlink(temp_file)


def test_config_loader_invalid_temperature(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    config = {
        "version": "2.3",
        "models": {"primary": {"provider": "openai", "model_name": "gpt-4", "temperature": 2.5}},
        "api": {"max_retries": 3},
        "scoring": {"criteria": {"accuracy": {"weight": 1.0}}},
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        temp_file = f.name
    try:
        with pytest.raises(ConfigError, match="temperature must be between 0 and 2"):
            ConfigLoader.load(temp_file)
    finally:
        os.unlink(temp_file)


def test_config_loader_invalid_max_retries():
    config = {
        "version": "2.3",
        "models": {"primary": {"provider": "openai", "model_name": "gpt-4"}},
        "api": {"max_retries": 11},
        "scoring": {"criteria": {"accuracy": {"weight": 1.0}}},
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        temp_file = f.name
    try:
        with pytest.raises(ConfigError, match="max_retries must be an integer between 1 and 10"):
            ConfigLoader.load(temp_file)
    finally:
        os.unlink(temp_file)
