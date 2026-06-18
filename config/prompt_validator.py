"""Prompt file validation and schema checking."""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple

import aiohttp

from config.logging_config import setup_logging
from config.validator import PromptValidator as BasePromptValidator
from config.validator import validate_before_execution, validate_prompt_file
from evaluation.cost_tracker import CostTracker
from evaluation.error_handler import EvaluationErrorHandler
from evaluation.prompt_runner import PromptRunner, execute_prompts_with_tracking

logger = logging.getLogger(__name__)


class PromptValidator:
    """Validates prompt files against schema."""

    @staticmethod
    def validate_schema(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate prompt data against JSON schema."""
        return BasePromptValidator.validate_schema(data)

    @staticmethod
    def validate_semantic(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate semantic correctness beyond schema."""
        warnings = []
        prompt_ids = set()

        for idx, prompt in enumerate(data.get("prompts", [])):
            prompt_id = prompt.get("id")

            if prompt_id in prompt_ids:
                warnings.append(f"Duplicate prompt ID at index {idx}: {prompt_id}")
            prompt_ids.add(prompt_id)

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
            logger.warning(f"Found {len(warnings)} semantic warnings in prompts")

        return True, warnings

    @staticmethod
    def load_and_validate(file_path: str) -> Dict[str, Any]:
        """Load JSON file and validate it completely."""
        try:
            data = validate_prompt_file(file_path)

            _, warnings = PromptValidator.validate_semantic(data)
            if warnings:
                for warning in warnings:
                    logger.warning(f"⚠ {warning}")

            logger.info(f"✓ Successfully loaded and validated {file_path}")
            logger.info(f"  Prompts: {len(data.get('prompts', []))}")

            return data
        except Exception as e:
            logger.error(f"✗ Failed to load or validate prompts: {str(e)}")
            raise


def main():
    """Main entry point for prompt execution."""
    # Setup logging
    setup_logging(log_level="INFO", log_file="evaluation.log")

    logger.info("=" * 60)
    logger.info("Starting AI Evaluation Pipeline")
    logger.info("=" * 60)

    # Validate configuration
    logger.info("Validating configuration...")
    validation_results = validate_before_execution(
        config_path="config/settings.yaml", prompts_file="data/prompts/reasoning_tests.json"
    )

    if validation_results["errors"]:
        for error in validation_results["errors"]:
            logger.error(f"✗ {error}")
        raise ValueError("Configuration validation failed")

    logger.info("✓ Configuration validation passed")

    # Load and validate prompts
    logger.info("Loading prompts...")
    try:
        prompts_data = PromptValidator.load_and_validate("data/prompts/reasoning_tests.json")
    except Exception as e:
        logger.error(f"✗ Failed to load prompts: {str(e)}")
        raise

    prompts = prompts_data.get("prompts", [])
    logger.info(f"✓ Loaded {len(prompts)} prompts")

    # Initialize handlers
    error_handler = EvaluationErrorHandler(max_retries=3, backoff_factor=2.0)
    budget_limit = os.getenv("BUDGET_LIMIT")
    cost_tracker = CostTracker(budget_limit=float(budget_limit) if budget_limit else None)

    logger.info("✓ Pipeline initialized and ready")
