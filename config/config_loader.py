import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Custom exception for configuration errors."""

    pass


class ConfigVersionError(ConfigError):
    """Raised when configuration version is outdated or incompatible."""

    pass


class ConfigLoader:
    REQUIRED_FIELDS = [
        "models.primary.provider",
        "models.primary.model_name",
        "api.max_retries",
        "scoring.criteria",
    ]

    VALID_PROVIDERS = {"openai", "anthropic", "azure"}
    CURRENT_VERSION = "2.3"

    @classmethod
    def load(cls, config_path: str = "config/settings.yaml") -> Dict[str, Any]:
        path = Path(config_path)
        if not path.exists():
            raise ConfigError(f"Configuration file not found: {config_path}")

        try:
            with path.open("r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in configuration file: {e}") from e
        except OSError as e:
            raise ConfigError(f"Unable to read configuration file: {e}") from e

        if not isinstance(config, dict):
            raise ConfigError("Configuration root must be a mapping/dictionary")

        config = cls._migrate_config(config)
        cls._validate_config(config)
        cls._load_env_variables(config)

        logger.info("Configuration loaded and validated successfully")
        return config

    @classmethod
    def _migrate_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        scoring = config.get("scoring")
        if isinstance(scoring, dict):
            if "dimensions" in scoring and "criteria" not in scoring:
                logger.info("Migrating configuration: 'scoring.dimensions' -> 'scoring.criteria'")
                scoring["criteria"] = scoring.pop("dimensions")
                config.setdefault("version", cls.CURRENT_VERSION)

        return config

    @classmethod
    def _validate_config(cls, config: Dict[str, Any]) -> None:
        for field_path in cls.REQUIRED_FIELDS:
            value = cls._get_nested_value(config, field_path)
            if value is None:
                raise ConfigError(f"Missing required field: {field_path}")

        provider = cls._get_nested_value(config, "models.primary.provider")
        if provider not in cls.VALID_PROVIDERS:
            raise ConfigError(
                f"Invalid provider '{provider}'. Must be one of: {sorted(cls.VALID_PROVIDERS)}"
            )

        criteria = cls._get_nested_value(config, "scoring.criteria")
        if not isinstance(criteria, dict) or not criteria:
            raise ConfigError("scoring.criteria must be a non-empty dictionary")

        total_weight = 0.0
        for name, item in criteria.items():
            if not isinstance(item, dict):
                raise ConfigError(f"scoring.criteria.{name} must be a dictionary")
            if "weight" not in item:
                raise ConfigError(f"Missing weight for scoring.criteria.{name}")
            weight = item["weight"]
            if not isinstance(weight, (int, float)):
                raise ConfigError(f"Weight for scoring.criteria.{name} must be numeric")
            total_weight += float(weight)

        if abs(total_weight - 1.0) > 0.01:
            raise ConfigError(f"Scoring criteria weights must sum to 1.0, got {total_weight}")

        max_retries = cls._get_nested_value(config, "api.max_retries")
        if not isinstance(max_retries, int) or not 1 <= max_retries <= 10:
            raise ConfigError(f"max_retries must be an integer between 1 and 10, got {max_retries}")

        temperature = cls._get_nested_value(config, "models.primary.temperature")
        if temperature is not None:
            if not isinstance(temperature, (int, float)) or not 0 <= float(temperature) <= 2:
                raise ConfigError(f"temperature must be between 0 and 2, got {temperature}")

    @staticmethod
    def _get_nested_value(d: Dict[str, Any], path: str) -> Optional[Any]:
        keys = path.split(".")
        value: Any = d
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return None
            value = value[key]
        return value

    @staticmethod
    def _load_env_variables(config: Dict[str, Any]) -> None:
        provider = ConfigLoader._get_nested_value(config, "models.primary.provider")

        env_key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "azure": "AZURE_API_KEY",
        }

        env_key = env_key_map.get(provider)
        if env_key and not os.getenv(env_key):
            raise ConfigError(
                f"Missing environment variable: {env_key}. Please set it in your environment."
            )
