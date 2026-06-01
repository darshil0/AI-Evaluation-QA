"""Environment and configuration validation module."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConfigurationValidator:
    """Validates environment configuration and settings."""

    # At least ONE of these must be present (not all required)
    REQUIRED_ENV_VARS_ANY_OF = {
        "OPENAI_API_KEY": "OpenAI API key for GPT models",
        "ANTHROPIC_API_KEY": "Anthropic API key for Claude models",
    }

    OPTIONAL_ENV_VARS = {
        "AZURE_API_KEY": "Azure OpenAI API key",
        "LOG_LEVEL": "Logging level (DEBUG, INFO, WARNING, ERROR)",
        "ENABLE_CACHING": "Enable API response caching (true/false)",
        "BUDGET_LIMIT": "Maximum budget in USD",
    }

    @staticmethod
    def validate_env_variables(strict: bool = False) -> Dict[str, Any]:
        """
        Validate that at least one required API key environment variable is set.

        At least one of OPENAI_API_KEY or ANTHROPIC_API_KEY must be present.
        Having neither is an error; having one is sufficient.

        Args:
            strict: If True, raise error when no valid key found. If False, warn.

        Returns:
            Dictionary with validation results.

        Raises:
            ValueError: If strict=True and no API key is present.
        """
        present_vars: Dict[str, str] = {}
        missing_vars: List[tuple] = []

        for var_name, description in ConfigurationValidator.REQUIRED_ENV_VARS_ANY_OF.items():
            value = os.getenv(var_name)
            if value and value.strip():
                present_vars[var_name] = "***"
            else:
                missing_vars.append((var_name, description))

        # Valid if at least one key is present
        has_any_key = len(present_vars) > 0

        if not has_any_key:
            error_msg = (
                "No API keys found. At least one of the following must be set:\n"
                + "\n".join([f"  - {var}: {desc}" for var, desc in missing_vars])
                + "\n\nPlease set at least one in your .env file.\n"
                "See config/env.example for a template."
            )

            if strict:
                raise ValueError(error_msg)
            else:
                logger.warning(error_msg)
                return {
                    "valid": False,
                    "missing": missing_vars,
                    "present": present_vars,
                }

        logger.info("✓ At least one API key is configured")
        return {
            "valid": True,
            "missing": [m for m in missing_vars],
            "present": present_vars,
        }

    @staticmethod
    def validate_yaml_config(config_path: str) -> bool:
        """Validate that settings.yaml exists and is readable."""
        if not Path(config_path).exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, "r") as f:
                f.read()
            logger.info(f"✓ Configuration file valid: {config_path}")
            return True
        except Exception as e:
            raise ValueError(f"Error reading configuration file: {str(e)}")

    @staticmethod
    def validate_prompts_file(file_path: str) -> bool:
        """Validate that prompts file exists."""
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Prompts file not found: {file_path}")
        return True


def validate_before_execution(
    config_path: str = "config/settings.yaml",
    prompts_file: Optional[str] = None,
) -> Dict[str, Any]:
    """Perform all validations before starting evaluation."""
    validator = ConfigurationValidator()
    results: Dict[str, Any] = {
        "env_valid": False,
        "config_valid": False,
        "prompts_valid": False,
        "errors": [],
    }

    try:
        env_result = validator.validate_env_variables(strict=True)
        results["env_valid"] = env_result["valid"]
    except ValueError as e:
        results["errors"].append(str(e))
        return results

    try:
        validator.validate_yaml_config(config_path)
        results["config_valid"] = True
    except (FileNotFoundError, ValueError) as e:
        results["errors"].append(str(e))

    if prompts_file:
        try:
            validator.validate_prompts_file(prompts_file)
            results["prompts_valid"] = True
        except FileNotFoundError as e:
            results["errors"].append(str(e))

    return results
