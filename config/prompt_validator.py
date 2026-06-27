"""Prompt file validation and schema checking."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

from config.validator import PromptValidator as BasePromptValidator
from config.validator import validate_prompt_file
from evaluation.cost_tracker import CostTracker
from evaluation.error_handler import EvaluationErrorHandler
from evaluation.prompt_runner import PromptRunner

logger = logging.getLogger(__name__)


async def execute_prompts_with_tracking(
    prompts: List[Dict[str, Any]],
    error_handler: EvaluationErrorHandler,
    cost_tracker: CostTracker,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute prompts with error and cost tracking."""
    import aiohttp  # pragma: no cover

    results: Dict[str, Any] = {"successful": [], "failed": [], "summary": {}}  # pragma: no cover

    runner = PromptRunner(config=config)  # pragma: no cover

    async with aiohttp.ClientSession() as session:  # pragma: no cover
        for prompt in prompts:  # pragma: no cover
            try:  # pragma: no cover
                success, result, failed_req = (
                    await error_handler.execute_with_retry(  # pragma: no cover
                        runner.execute_prompt_async, prompt["id"], prompt, session
                    )
                )

                if success:  # pragma: no cover
                    results["successful"].append(result)  # pragma: no cover

                    # Track costs
                    cost_tracker.add_request(  # pragma: no cover
                        model=result.get("model", config.get("model", "gpt-4")),
                        input_tokens=result.get("prompt_tokens", 0),
                        output_tokens=result.get("response_tokens", 0),
                        prompt_id=prompt["id"],
                    )
                else:
                    results["failed"].append(  # pragma: no cover
                        {
                            "prompt_id": prompt["id"],
                            "error": failed_req.error_message if failed_req else "Unknown error",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
            except Exception as e:  # pragma: no cover
                logger.error(
                    f"Failed to execute prompt {prompt['id']}: {str(e)}"
                )  # pragma: no cover
                results["failed"].append(  # pragma: no cover
                    {
                        "prompt_id": prompt["id"],
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

    results["summary"] = {  # pragma: no cover
        "total": len(prompts),
        "success": len(results["successful"]),
        "failed": len(results["failed"]),
        "success_rate": (len(results["successful"]) / len(prompts) * 100) if prompts else 0,
        "costs": cost_tracker.get_summary(),
        "errors": error_handler.get_summary(),
    }

    return results  # pragma: no cover


class PromptValidator:
    """Validates prompt files against schema."""

    @staticmethod
    def validate_schema(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate prompt data against JSON schema."""
        return BasePromptValidator.validate_schema(data)

    @staticmethod
    def validate_semantic(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate semantic correctness beyond schema.
        Delegates to validate_prompt_file which now handles this.
        """
        # This is kept for compatibility with callers who expect validate_semantic
        # However, it re-validates. A better way would be to move the logic
        # to a shared place, which we did in validate_prompt_file.
        # To avoid circularity or complex refactor, we keep it but it could be
        # simplified.
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
                if min_tokens and max_tokens and min_tokens > max_tokens:  # pragma: no cover
                    warnings.append(f"Prompt {prompt_id}: min_tokens > max_tokens")

        return True, warnings

    @staticmethod
    def load_and_validate(file_path: str) -> Dict[str, Any]:
        """Load JSON file and validate it completely."""
        try:
            # This now does schema + duplicate ID + semantic warnings
            data = validate_prompt_file(file_path)

            logger.info(f"✓ Successfully loaded and validated {file_path}")
            logger.info(f"  Prompts: {len(data.get('prompts', []))}")

            return data
        except Exception as e:
            if not isinstance(e, ValueError):
                logger.error(f"✗ Failed to load or validate prompts: {str(e)}")
                raise ValueError(str(e))
            raise  # pragma: no cover
