import logging
from typing import Any, Dict, Optional
import aiohttp
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.api_key = os.getenv("OPENAI_API_KEY") or self.config.get("api_key")
        self.model = self.config.get("models", {}).get("primary", {}).get("model_name", "gpt-4")

    async def execute_prompt(self, prompt_data: Dict[str, Any], session: aiohttp.ClientSession) -> Dict[str, Any]:
        prompt_text = prompt_data.get("prompt") or prompt_data.get("text", "")
        prompt_id = prompt_data.get("id") or "unknown"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt_text}]
        }

        try:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "prompt_id": prompt_id,
                        "prompt": prompt_text,
                        "response": data["choices"][0]["message"]["content"],
                        "model": self.model,
                        "timestamp": datetime.now().isoformat(),
                        "status": "success",
                        "prompt_tokens": data.get("usage", {}).get("prompt_tokens"),
                        "response_tokens": data.get("usage", {}).get("completion_tokens")
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"OpenAI API error: {response.status} - {error_text}")
                    return self._error_response(prompt_id, prompt_text, f"API error {response.status}")
        except Exception as e:
            logger.error(f"Exception during OpenAI API call: {e}")
            return self._error_response(prompt_id, prompt_text, str(e))

    def _error_response(self, prompt_id: str, prompt_text: str, error_msg: str) -> Dict[str, Any]:
        return {
            "prompt_id": prompt_id,
            "prompt": prompt_text,
            "response": "",
            "model": self.model,
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error": error_msg
        }
