"""Environment and configuration validation module."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jsonschema import ValidationError, validate

logger = logging.getLogger(__name__)

PROMPT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["metadata", "prompts"],
    "properties": {
        "metadata": {
            "type": "object",
            "required": ["version", "description"],
            "properties": {"version": {"type": "string"}, "description": {"type": "string"}},
        },
        "prompts": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "category", "text"],
                "properties": {
                    "id": {"type": "string", "pattern": "^[A-Za-z0-9_-]+$"},
                    "version": {"type": "string"},
                    "category": {"type": "string"},
                    "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "text": {"type": "string", "minLength": 10},
                    "expected_criteria": {"type": "object"},
                },
            },
            "minItems": 1,
        },
    },
}


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
            with open(config_path, "r", encoding="utf-8") as f:
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


class PromptValidator:
    """Validates prompt files against schema."""

    @staticmethod
    def validate_schema(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate prompt data against JSON schema."""
        try:
            validate(instance=data, schema=PROMPT_SCHEMA)
            logger.info("✓ Prompt schema validation passed")
            return True, []
        except ValidationError as e:
            error_msg = (
                f"Schema validation error at {'.'.join(str(p) for p in e.path)}: " f"{e.message}"
            )
            logger.error(error_msg)
            return False, [error_msg]


def validate_prompt_file(filepath: str) -> Dict:
    """
    Validate prompt JSON file against schema.

    Args:
        filepath: Path to prompt JSON file

    Returns:
        Validated prompt data

    Raises:
        ValidationError: If file doesn't match schema
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    filepath_path = Path(filepath)

    if not filepath_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {filepath}")

    try:
        with open(filepath_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {filepath}: {str(e)}", e.doc, e.pos)

    # Validate against schema
    try:
        validate(instance=data, schema=PROMPT_SCHEMA)
    except ValidationError as e:
        raise ValidationError(f"Prompt schema validation failed: {e.message}")

    # Additional validation: check for duplicate IDs and semantic correctness
    prompt_ids = set()
    warnings = []

    for _, prompt in enumerate(data.get("prompts", [])):
        prompt_id = prompt.get("id")

        if prompt_id in prompt_ids:
            raise ValidationError(
                f"Duplicate prompt ID found: {prompt_id}. Prompt IDs must be unique."
            )
        prompt_ids.add(prompt_id)

        # Semantic warnings (not errors)
        text_length = len(prompt.get("text", ""))
        if text_length < 20:
            warnings.append(f"Prompt {prompt_id} text is very short ({text_length} chars)")

        criteria = prompt.get("expected_criteria", {})
        if criteria:
            min_tokens = criteria.get("min_tokens")
            max_tokens = criteria.get("max_tokens")
            if min_tokens and max_tokens and min_tokens > max_tokens:
                warnings.append(f"Prompt {prompt_id}: min_tokens > max_tokens")

    if warnings:
        for warning in warnings:
            logger.warning(f"⚠ {warning}")

    return data


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration dictionary.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ValueError: If configuration is invalid
    """
    required_keys = ["models", "api", "scoring"]

    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")

    # Validate models config
    if "primary" not in config["models"]:
        raise ValueError("Missing 'primary' model configuration")

    # Validate API config
    api_config = config["api"]
    if "max_retries" in api_config and api_config["max_retries"] < 0:
        raise ValueError("max_retries must be non-negative")

    if "rate_limit_rpm" in api_config and api_config["rate_limit_rpm"] <= 0:
        raise ValueError("rate_limit_rpm must be positive")


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
