import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


class AnthropicClient:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.api_key = os.getenv("ANTHROPIC_API_KEY") or self.config.get("api_key")
        self.model = (
            self.config.get("models", {})
            .get("primary", {})
            .get("model_name", "claude-3-opus-20240229")
        )

    async def execute_prompt(
        self, prompt_data: Dict[str, Any], session: aiohttp.ClientSession
    ) -> Dict[str, Any]:
        prompt_text = prompt_data.get("prompt") or prompt_data.get("text", "")
        prompt_id = prompt_data.get("id") or "unknown"

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt_text}],
            "max_tokens": 1024,
        }

        try:
            async with session.post(
                "https://api.anthropic.com/v1/messages", headers=headers, json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "prompt_id": prompt_id,
                        "prompt": prompt_text,
                        "response": data["content"][0]["text"],
                        "model": self.model,
                        "timestamp": datetime.now().isoformat(),
                        "status": "success",
                        "prompt_tokens": data.get("usage", {}).get("input_tokens"),
                        "response_tokens": data.get("usage", {}).get("output_tokens"),
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Anthropic API error: {response.status} - {error_text}")
                    return self._error_response(
                        prompt_id, prompt_text, f"API error {response.status}"
                    )
        except Exception as e:
            logger.error(f"Exception during Anthropic API call: {e}")
            return self._error_response(prompt_id, prompt_text, str(e))

    def _error_response(self, prompt_id: str, prompt_text: str, error_msg: str) -> Dict[str, Any]:
        return {
            "prompt_id": prompt_id,
            "prompt": prompt_text,
            "response": "",
            "model": self.model,
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error": error_msg,
        }
