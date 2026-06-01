"""
Input validation utilities for prompts and configuration.
"""

import json
from typing import Dict, List, Any
from jsonschema import validate, ValidationError
from pathlib import Path

PROMPT_SCHEMA = {
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
                "required": ["id", "version", "category", "text"],
                "properties": {
                    "id": {"type": "string", "pattern": "^[A-Z0-9_]+$"},
                    "version": {"type": "string"},
                    "category": {"type": "string"},
                    "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "text": {"type": "string", "minLength": 10},
                    "expected_criteria": {"type": "object"},
                },
            },
        },
    },
}


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
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Prompt file not found: {filepath}")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {filepath}: {str(e)}", e.doc, e.pos)

    # Validate against schema
    try:
        validate(instance=data, schema=PROMPT_SCHEMA)
    except ValidationError as e:
        raise ValidationError(f"Schema validation failed: {e.message}")

    # Additional validation: check for duplicate IDs
    prompt_ids = [p["id"] for p in data["prompts"]]
    if len(prompt_ids) != len(set(prompt_ids)):
        duplicates = [pid for pid in prompt_ids if prompt_ids.count(pid) > 1]
        raise ValidationError(f"Duplicate prompt IDs found: {set(duplicates)}")

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
