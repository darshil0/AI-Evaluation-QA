import asyncio
import csv
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
import openai

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
        self.model = model
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.failure_count = 0
        self.total_count = 0
        self.semaphore = asyncio.Semaphore(self.config.get("max_concurrent_requests", 5))

    def _get_api_client(self, provider: str):
        if provider == "openai":
            from evaluation.clients.openai_client import OpenAIClient

            return OpenAIClient(self.config)
        elif provider == "anthropic":
            from evaluation.clients.anthropic_client import AnthropicClient

            return AnthropicClient(self.config)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def execute_prompt(self, prompt: str) -> str:
        """Execute a single prompt synchronously with retries."""
        self.total_count += 1
        last_exception = Exception("No attempts made")

        for attempt in range(self.retry_attempts):
            try:
                api_key = os.getenv("OPENAI_API_KEY") or self.config.get("api_key")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY environment variable not set")

                client = openai.OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=self.timeout,
                )
                return response.choices[0].message.content
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
        """Execute multiple prompts."""
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
            self.failure_count += 1
        self.total_count += 1
        return result

    async def _execute_with_semaphore(
        self, prompt: Dict[str, Any], session: aiohttp.ClientSession
    ) -> Dict[str, Any]:
        """Execute a single prompt with semaphore for concurrency control."""
        async with self.semaphore:
            return await self.execute_prompt_async(prompt, session)

    async def run_prompts(
        self, prompts: List[Dict[str, Any]], checkpoint_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """Execute prompts asynchronously with concurrency control and optional checkpointing."""
        results = []
        async with aiohttp.ClientSession() as session:
            tasks = [self._execute_with_semaphore(prompt, session) for prompt in prompts]

            # Use as_completed to process results as they arrive for immediate checkpointing
            for future in asyncio.as_completed(tasks):
                try:
                    result = await future
                    results.append(result)
                    if checkpoint_callback:
                        checkpoint_callback(results)
                except Exception as e:
                    logger.error(f"Unexpected error in prompt execution task: {e}")

            return results

    def save_responses(
        self, results: List[Dict[str, Any]], filepath: str, format: str = "csv"
    ) -> None:
        """Save responses to file."""
        if format == "csv":
            # Collect all unique keys
            all_keys = set()
            for r in results:
                all_keys.update(r.keys())

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=sorted(list(all_keys)))
                writer.writeheader()
                writer.writerows(results)
        elif format == "json":
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Saved {len(results)} responses to {filepath}")

    def save_results(self, results: List[Dict[str, Any]], filepath: str) -> None:
        """Save results to CSV file (legacy method)."""
        self.save_responses(results, filepath, format="csv")

    def print_summary(self) -> None:
        """Print execution summary."""
        logger.info(f"Prompt run summary: {self.total_count} total, {self.failure_count} failures")


def execute_prompts(
    prompts: List[Dict[str, Any]], config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Standalone function to execute prompts."""
    runner = PromptRunner(config=config)
    return runner.execute_prompts(prompts)
