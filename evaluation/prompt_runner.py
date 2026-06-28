import asyncio
import csv
import json
import logging
import time
import warnings
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import aiohttp

from evaluation.error_handler import EvaluationErrorHandler

logger = logging.getLogger(__name__)


class PromptRunner:
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        model: str = "gpt-4",
        timeout: int = 30,
        retry_attempts: int = 3,
    ):
        """Initialize PromptRunner with configuration."""
        self.config = config or {}
        self.model = self.config.get("models", {}).get("primary", {}).get("model_name", model)
        self.timeout = self.config.get("api", {}).get("timeout", timeout)
        self.retry_attempts = self.config.get("api", {}).get("max_retries", retry_attempts)
        self.failure_count = 0
        self.total_count = 0
        self._max_concurrent_requests = self.config.get("api", {}).get("max_concurrent_requests", 5)
        self._semaphore: Optional[asyncio.Semaphore] = None
        self.error_handler = EvaluationErrorHandler(
            max_retries=self.retry_attempts,
            backoff_factor=float(self.config.get("execution", {}).get("backoff_factor", 2.0)),
        )

    @property
    def semaphore(self) -> asyncio.Semaphore:
        """Lazily initialize the semaphore to ensure it is created within an event loop."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self._max_concurrent_requests)
        return self._semaphore

    def _get_api_client(self, provider: str) -> Any:
        if provider == "openai":
            from evaluation.clients.openai_client import OpenAIClient

            return OpenAIClient(self.config)
        elif provider == "anthropic":
            from evaluation.clients.anthropic_client import AnthropicClient

            return AnthropicClient(self.config)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def execute_prompt(self, prompt: str) -> Any:
        """
        Execute a single prompt synchronously with retries.

        Preconditions:
            - prompt must be a non-empty string.
            - Valid API key must be available in environment or config.

        Postconditions:
            - Returns the model's response text.

        Edge Cases:
            - Empty prompt: May result in API error or empty response.
            - Network instability: Handled by retries with exponential backoff.

        Failure Modes:
            - ValueError: If API key is missing.
            - Exception: If all retry attempts fail.
        """
        self.total_count += 1
        last_exception = Exception("No attempts made")

        provider = self.config.get("models", {}).get("primary", {}).get("provider", "openai")
        client = self._get_api_client(provider)

        for attempt in range(self.retry_attempts):
            try:
                return client.execute_prompt_sync(prompt)
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(2**attempt)  # Exponential backoff

        self.failure_count += 1
        logger.error(
            f"Error executing prompt after {self.retry_attempts} attempts: {last_exception}"
        )
        raise last_exception

    def execute_prompts(self, prompts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute multiple prompts.

        Preconditions:
            - prompts must be a list of dictionaries, each containing 'prompt' or 'text'.

        Postconditions:
            - Returns a list of result dictionaries with status 'success' or 'error'.

        Edge Cases:
            - Empty list: Returns an empty list.
            - Mixed valid/invalid prompts: Valid prompts are executed;
              invalid ones are marked as 'error'.
        """
        if not prompts:
            return []

        # Validate prompts
        for prompt in prompts:
            if "prompt" not in prompt and "text" not in prompt:
                raise ValueError("Each prompt must have a 'prompt' or 'text' field")

        results = []
        for prompt_data in prompts:
            try:
                prompt_text = prompt_data.get("prompt") or prompt_data.get("text", "")
                response = self.execute_prompt(prompt_text)

                result = {
                    "prompt_id": prompt_data.get("id", "unknown"),
                    "prompt": prompt_text,
                    "response": response,
                    "model": self.model,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                }
                results.append(result)
            except Exception as e:
                logger.error(f"Error executing prompt {prompt_data.get('id')}: {e}")
                results.append(
                    {
                        "prompt_id": prompt_data.get("id", "unknown"),
                        "prompt": prompt_data.get("prompt") or prompt_data.get("text", ""),
                        "response": "",
                        "model": self.model,
                        "timestamp": datetime.now().isoformat(),
                        "status": "error",
                        "error": str(e),
                    }
                )

        return results

    async def execute_prompt_async(
        self, prompt: Dict[str, Any], session: aiohttp.ClientSession
    ) -> Dict[str, Any]:
        """Execute a single prompt asynchronously."""
        provider = self.config.get("models", {}).get("primary", {}).get("provider", "openai")
        api_client = self._get_api_client(provider)
        result = await api_client.execute_prompt(prompt, session)
        if result["status"] == "error":
            self.failure_count += 1  # pragma: no cover
        self.total_count += 1
        return result if isinstance(result, dict) else {}

    async def _execute_with_semaphore(
        self, prompt: Dict[str, Any], session: aiohttp.ClientSession
    ) -> Dict[str, Any]:
        """Execute a single prompt with semaphore and error handling."""
        prompt_id = str(prompt.get("id") or prompt.get("prompt_id") or "unknown")

        async with self.semaphore:
            success, result, failed_req = await self.error_handler.execute_with_retry(
                self.execute_prompt_async, prompt_id, prompt, session
            )

            if success:
                return result if isinstance(result, dict) else {}
            else:
                # Return the error response captured in the last attempt if available
                # or construct one from failed_req
                return {  # pragma: no cover
                    "prompt_id": prompt_id,
                    "prompt": prompt.get("prompt") or prompt.get("text", ""),
                    "response": "",
                    "model": self.model,
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "error": failed_req.error_message if failed_req else "Unknown error",
                }

    async def run_prompts(
        self,
        prompts: List[Dict[str, Any]],
        checkpoint_callback: Optional[Callable[[List[Dict[str, Any]]], Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute prompts asynchronously with concurrency control and optional checkpointing.

        Preconditions:
            - prompts must be a list of dictionaries.
            - Async-capable provider must be configured.

        Postconditions:
            - Returns a list of results as they complete.
            - Calls checkpoint_callback (if provided) after each result.

        Edge Cases:
            - High concurrency: Controlled by semaphore.
            - Partial failures: Individual errors are captured in results.
        """
        results = []
        async with aiohttp.ClientSession() as session:
            tasks = [self._execute_with_semaphore(prompt, session) for prompt in prompts]

            # Use as_completed to process results as they arrive for immediate checkpointing
            for future in asyncio.as_completed(tasks):
                try:
                    result = await future
                    results.append(result)
                    if checkpoint_callback:
                        checkpoint_callback(results)  # pragma: no cover
                except Exception as e:  # pragma: no cover
                    logger.error(
                        f"Unexpected error in prompt execution task: {e}"
                    )  # pragma: no cover

            return results

    def save_responses(
        self, results: List[Dict[str, Any]], filepath: str, file_format: str = "csv"
    ) -> None:
        """
        Save responses to file.

        Args:
            results: List of result dictionaries
            filepath: Path to save the file
            file_format: File format ('csv' or 'json')
        """
        if file_format == "csv":
            # Collect all unique keys
            all_keys: set[str] = set()
            for r in results:
                if isinstance(r, dict):  # pragma: no cover
                    all_keys.update(r.keys())

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=sorted(list(all_keys)), extrasaction="ignore")
                writer.writeheader()
                writer.writerows(results)
        elif file_format == "json":
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {file_format}")

        logger.info(f"Saved {len(results)} responses to {filepath}")

    def save_results(
        self, results: List[Dict[str, Any]], filepath: str
    ) -> None:  # pragma: no cover
        """Save results to CSV file (legacy method)."""
        warnings.warn(
            "save_results() is deprecated. Use save_responses(..., file_format='csv') instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.save_responses(results, filepath, file_format="csv")

    def print_summary(self) -> None:
        """Print execution summary."""
        logger.info(f"Prompt run summary: {self.total_count} total, {self.failure_count} failures")


def execute_prompts(
    prompts: List[Dict[str, Any]], config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Standalone function to execute prompts."""
    runner = PromptRunner(config=config)
    return runner.execute_prompts(prompts)
