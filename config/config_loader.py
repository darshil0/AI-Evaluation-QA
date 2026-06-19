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
    """
    Loads and validates YAML configuration files with support for:
    - Required field validation
    - Provider validation
    - Scoring criteria weight validation
    - Environment variable validation
    - Config migration from older versions
    """
    
    REQUIRED_FIELDS = [
        "models.primary.provider",
        "models.primary.model_name",
        "api.max_retries",
        "scoring.criteria",
    ]

    VALID_PROVIDERS = {"openai", "anthropic", "azure"}
    CURRENT_VERSION = "2.3"
    MIN_COMPATIBLE_VERSION = "2.0"
    
    ENV_KEY_MAP = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "azure": "AZURE_OPENAI_API_KEY",
    }

    @classmethod
    def load(cls, config_path: str = "config/settings.yaml") -> Dict[str, Any]:
        """
        Load and validate configuration from a YAML file.
        
        Args:
            config_path: Path to the YAML configuration file
            
        Returns:
            Validated configuration dictionary
            
        Raises:
            ConfigError: If configuration is invalid or missing required fields
            ConfigVersionError: If configuration version is incompatible
        """
        path = Path(config_path)
        
        try:
            with path.open("r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            raise ConfigError(f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in configuration file: {e}") from e
        except OSError as e:
            raise ConfigError(f"Unable to read configuration file: {e}") from e

        if not isinstance(config, dict):
            raise ConfigError("Configuration root must be a mapping/dictionary")

        cls._check_version_compatibility(config)
        config = cls._migrate_config(config)
        cls._validate_config(config)
        cls._load_env_variables(config)

        logger.info("Configuration loaded and validated successfully")
        return config

    @classmethod
    def _check_version_compatibility(cls, config: Dict[str, Any]) -> None:
        """Check if configuration version is compatible."""
        version = config.get("version")
        
        if version is None:
            logger.warning("No version specified in configuration. Assuming legacy format.")
            return
        
        if version == cls.CURRENT_VERSION:
            return
        
        try:
            current_major, current_minor = map(int, cls.MIN_COMPATIBLE_VERSION.split("."))
            version_major, version_minor = map(int, version.split("."))
            
            if version_major < current_major or (version_major == current_major and version_minor < current_minor):
                raise ConfigVersionError(
                    f"Configuration version '{version}' is incompatible. "
                    f"Minimum compatible version: {cls.MIN_COMPATIBLE_VERSION}, "
                    f"current version: {cls.CURRENT_VERSION}"
                )
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse version '{version}', proceeding with validation")

    @classmethod
    def _migrate_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate configuration from older versions to current format.
        
        Mutates config in place and returns it.
        """
        version = config.get("version")
        
        if version is None or version.startswith("1."):
            scoring = config.get("scoring")
            if isinstance(scoring, dict):
                if "dimensions" in scoring and "criteria" not in scoring:
                    logger.info("Migrating configuration: 'scoring.dimensions' -> 'scoring.criteria'")
                    scoring["criteria"] = scoring.pop("dimensions")

                    # VALIDATE IMMEDIATELY to catch issues early
                    try:
                        cls._validate_scoring_criteria(scoring["criteria"])
                        logger.info("Migration validated successfully")
                    except ConfigError as e:
                        raise ConfigError(f"Migration failed validation: {e}") from e
            
            config["version"] = cls.CURRENT_VERSION
            logger.info(f"Configuration migrated to version {cls.CURRENT_VERSION}")

        return config

    @classmethod
    def _validate_config(cls, config: Dict[str, Any]) -> None:
        """Validate all configuration fields and constraints."""
        for field_path in cls.REQUIRED_FIELDS:
            value = cls._get_nested_value(config, field_path)
            if value is None:
                raise ConfigError(f"Missing required field: {field_path}")

        provider = cls._get_nested_value(config, "models.primary.provider")
        if provider not in cls.VALID_PROVIDERS:
            raise ConfigError(
                f"Invalid provider '{provider}'. Must be one of: {sorted(cls.VALID_PROVIDERS)}"
            )

        model_name = cls._get_nested_value(config, "models.primary.model_name")
        if not isinstance(model_name, str) or not model_name.strip():
            raise ConfigError("models.primary.model_name must be a non-empty string")

        criteria = cls._get_nested_value(config, "scoring.criteria")
        if not isinstance(criteria, dict) or not criteria:
            raise ConfigError("scoring.criteria must be a non-empty dictionary")

        cls._validate_scoring_criteria(criteria)

        max_retries = cls._get_nested_value(config, "api.max_retries")
        if not isinstance(max_retries, int) or isinstance(max_retries, bool) or not 1 <= max_retries <= 10:
            raise ConfigError(f"max_retries must be an integer between 1 and 10, got {max_retries}")

        temperature = cls._get_nested_value(config, "models.primary.temperature")
        if temperature is not None:
            if not isinstance(temperature, (int, float)) or isinstance(temperature, bool):
                raise ConfigError(f"temperature must be a number between 0 and 2, got {temperature}")
            if not 0 <= float(temperature) <= 2:
                raise ConfigError(f"temperature must be between 0 and 2, got {temperature}")

    @classmethod
    def _validate_scoring_criteria(cls, criteria: Dict[str, Any]) -> float:
        """
        Validate scoring criteria and return total weight.
        
        Raises ConfigError if any criterion is invalid.
        """
        total_weight = 0.0
        
        for name, item in criteria.items():
            if not isinstance(item, dict):
                raise ConfigError(f"scoring.criteria.{name} must be a dictionary")
            if "weight" not in item:
                raise ConfigError(f"Missing weight for scoring.criteria.{name}")
            
            weight = item["weight"]
            if not isinstance(weight, (int, float)) or isinstance(weight, bool):
                raise ConfigError(f"Weight for scoring.criteria.{name} must be numeric, got {type(weight).__name__}")
            
            total_weight += float(weight)

        if abs(total_weight - 1.0) > 0.01:
            raise ConfigError(f"Scoring criteria weights must sum to 1.0, got {round(total_weight, 3)}")
        
        return total_weight

    @staticmethod
    def _get_nested_value(d: Dict[str, Any], path: str) -> Optional[Any]:
        """
        Get a value from a nested dictionary using dot notation path.
        
        Args:
            d: Dictionary to search
            path: Dot-separated path (e.g., "models.primary.provider")
            
        Returns:
            The value at the path, or None if not found
        """
        keys = path.split(".")
        value: Any = d
        
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return None
            value = value[key]
        
        return value

    @classmethod
    def _load_env_variables(cls, config: Dict[str, Any]) -> None:
        """
        Validate and inject API keys from environment variables into config.
        
        This mutates the config dict to add the API key under a standard key.
        """
        provider = cls._get_nested_value(config, "models.primary.provider")
        
        if provider not in cls.ENV_KEY_MAP:
            return

        env_key = cls.ENV_KEY_MAP[provider]
        api_key = os.getenv(env_key)
        
        if not api_key:
            raise ConfigError(
                f"Missing environment variable: {env_key}. "
                f"Please set it in your environment before running."
            )
        
        # Use setdefault for cleaner nested dict creation
        config.setdefault("models", {}).setdefault("primary", {})
        config["models"]["primary"]["api_key"] = api_key
        logger.debug(f"API key loaded from {env_key} environment variable")
