"""Prompt file validation and schema checking."""

import logging
import os
import asyncio
import aiohttp
from typing import Dict, Any, List, Tuple
from pathlib import Path
from jsonschema import validate, ValidationError
from config.validator import validate_before_execution
from evaluation.error_handler import EvaluationErrorHandler
from evaluation.cost_tracker import CostTracker
from evaluation.prompt_runner import PromptRunner
from config.logging_config import setup_logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


PROMPT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "metadata": {
            "type": "object",
            "properties": {"version": {"type": "string"}, "description": {"type": "string"}},
            "required": ["version", "description"],
        },
        "prompts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "pattern": "^[A-Za-z0-9_-]+$"},
                    "version": {"type": "string"},
                    "category": {"type": "string"},
                    "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "text": {"type": "string", "minLength": 10},
                    "expected_criteria": {"type": "object"},
                },
                "required": ["id", "text", "category"],
            },
            "minItems": 1,
        },
    },
    "required": ["metadata", "prompts"],
}


async def execute_prompts_with_tracking(
    prompts: List[Dict],
    error_handler: EvaluationErrorHandler,
    cost_tracker: CostTracker,
    config: Dict,
) -> Dict[str, Any]:
    """Execute prompts with error and cost tracking."""
    results = {"successful": [], "failed": [], "summary": {}}

    runner = PromptRunner(config=config)

    async with aiohttp.ClientSession() as session:
        for prompt in prompts:
            try:
                success, result, failed_req = await error_handler.execute_with_retry(
                    runner.execute_prompt_async, prompt["id"], prompt, session
                )

                if success:
                    results["successful"].append(result)

                    # Track costs
                    cost_tracker.add_request(
                        model=result.get("model", config.get("model", "gpt-4")),
                        input_tokens=result.get("prompt_tokens", 0),
                        output_tokens=result.get("response_tokens", 0),
                        prompt_id=prompt["id"],
                    )
                else:
                    results["failed"].append(
                        {
                            "prompt_id": prompt["id"],
                            "error": failed_req.error_message if failed_req else "Unknown error",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
            except Exception as e:
                logger.error(f"Failed to execute prompt {prompt['id']}: {str(e)}")
                results["failed"].append(
                    {
                        "prompt_id": prompt["id"],
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

    results["summary"] = {
        "total": len(prompts),
        "success": len(results["successful"]),
        "failed": len(results["failed"]),
        "success_rate": (len(results["successful"]) / len(prompts) * 100) if prompts else 0,
        "costs": cost_tracker.get_summary(),
        "errors": error_handler.get_summary(),
    }

    return results


class PromptValidator:
    """Validates prompt files against schema."""

    @staticmethod
    def validate_schema(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate prompt data against JSON schema."""
        errors = []

        try:
            validate(instance=data, schema=PROMPT_SCHEMA)
            logger.info("✓ Prompt schema validation passed")
            return True, []
        except ValidationError as e:
            error_msg = (
                f"Schema validation error at {'.'.join(str(p) for p in e.path)}: " f"{e.message}"
            )
            errors.append(error_msg)
            logger.error(error_msg)
            return False, errors

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
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Prompts file not found: {file_path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in {file_path}: {e.msg}", e.doc, e.pos)

        is_valid, schema_errors = PromptValidator.validate_schema(data)
        if not is_valid:
            raise ValueError(f"Schema validation failed: {schema_errors[0]}")

        _, warnings = PromptValidator.validate_semantic(data)
        if warnings:
            for warning in warnings:
                logger.warning(f"⚠ {warning}")

        logger.info(f"✓ Successfully loaded and validated {file_path}")
        logger.info(f"  Prompts: {len(data.get('prompts', []))}")

        return data


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
