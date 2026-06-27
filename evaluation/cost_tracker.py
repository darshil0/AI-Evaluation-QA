import logging
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CostTracker:
    """Track API costs based on token usage or text analysis."""

    # Pricing per 1M tokens (as of 2025)
    PRICING = {
        "gpt-4": {"input": 30.00, "output": 60.00},
        "gpt-4-turbo-preview": {"input": 10.00, "output": 30.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
        "claude-opus-4-6": {"input": 15.00, "output": 75.00},
        "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    }

    def __init__(
        self,
        model_name: str = "gpt-4",
        budget_limit: Optional[float] = None,
        budget_threshold: Optional[float] = None,
    ) -> None:
        """
        Initialize CostTracker.

        Args:
            model_name: Default model name for text-based tracking
            budget_limit: Optional budget limit in USD
            budget_threshold: Alias for budget_limit for backward compatibility
        """
        self.model_name = model_name
        self.budget_limit = budget_limit if budget_limit is not None else budget_threshold
        self.budget_threshold = self.budget_limit  # Compatibility
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.request_count = 0
        self.usage_log: List[Dict[str, Any]] = []
        self.alerts: List[Dict[str, Any]] = []
        self.requests: List[Dict[str, Any]] = []  # Legacy compatibility

        # Initialize tokenizer
        self.encoding: Any = None
        try:
            import tiktoken

            if "gpt" in model_name.lower():
                self.encoding = tiktoken.encoding_for_model(model_name)
            else:
                # Use cl100k_base for Claude (approximate)
                self.encoding = tiktoken.get_encoding("cl100k_base")  # pragma: no cover
        except Exception as e:  # pragma: no cover
            logger.warning(f"Could not load tokenizer for {model_name}: {e}")  # pragma: no cover

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if not text:
            return 0  # pragma: no cover

        return self._count_tokens_cached(text, self.encoding)

    @staticmethod
    @lru_cache(maxsize=1000)
    def _count_tokens_cached(text: str, encoding: Any) -> int:
        if encoding is None:
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4  # pragma: no cover

        try:
            return len(encoding.encode(text))
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            return len(text) // 4

    def track_request(self, prompt: str, response: str) -> Dict[str, float]:
        """Track a single request based on text and return costs"""
        input_tokens = self.count_tokens(prompt)
        output_tokens = self.count_tokens(response)

        cost = self.add_request(
            model=self.model_name, input_tokens=input_tokens, output_tokens=output_tokens
        )

        return {
            "input_tokens": float(input_tokens),
            "output_tokens": float(output_tokens),
            "total_tokens": float(input_tokens + output_tokens),
            "cost": cost,
            "cumulative_cost": self.total_cost,
        }

    def add_request(
        self, model: str, input_tokens: int, output_tokens: int, prompt_id: Optional[str] = None
    ) -> float:
        """
        Add a request with known token counts.
        """
        return self.calculate_cost(model, input_tokens, output_tokens, prompt_id)

    def calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int, prompt_id: Optional[str] = None
    ) -> float:
        """
        Calculate and track cost for a single API call.
        """
        cost = self._calculate_cost(model, input_tokens, output_tokens)

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost
        self.request_count += 1

        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "prompt_id": prompt_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": round(cost, 6),
        }
        self.usage_log.append(entry)
        self.requests.append(entry)

        # Check budget
        if self.budget_limit:
            self.check_budget()

        return cost

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for tokens"""
        model_key = self._normalize_model_name(model)
        pricing = self.PRICING.get(model_key)

        if pricing is None:
            logger.warning(f"No pricing data for {model}, using default GPT-4 pricing")
            pricing = self.PRICING["gpt-4"]

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def _normalize_model_name(self, model: str) -> str:
        """Normalize model name to match pricing keys."""
        model_lower = model.lower()

        if "gpt-4-turbo" in model_lower:
            return "gpt-4-turbo-preview"
        elif "gpt-4" in model_lower:
            return "gpt-4"
        elif "gpt-3.5" in model_lower or "gpt-35" in model_lower:
            return "gpt-3.5-turbo"
        elif "sonnet" in model_lower:
            return "claude-sonnet-4-6"
        elif "opus" in model_lower:
            return "claude-opus-4-6"
        elif "haiku" in model_lower:
            return "claude-haiku-4-5-20251001"

        return model

    def get_total_tokens(self) -> int:
        """Return the total number of tokens processed."""
        return self.total_input_tokens + self.total_output_tokens

    def get_summary(self) -> Dict[str, Any]:
        """Get cost tracking summary"""
        by_model: Dict[str, float] = {}
        for entry in self.usage_log:
            m = str(entry["model"])
            by_model[m] = by_model.get(m, 0.0) + float(entry["cost"])

        return {
            "model": self.model_name,
            "total_requests": self.request_count,
            "total_calls": self.request_count,  # Compatibility
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost": round(self.total_cost, 4),
            "total_cost_usd": round(self.total_cost, 4),
            "avg_tokens_per_request": (
                (self.total_input_tokens + self.total_output_tokens) / max(1, self.request_count)
            ),
            "average_cost_per_call": round(self.total_cost / max(1, self.request_count), 4),
            "budget_limit": self.budget_limit,
            "budget_threshold": self.budget_limit,
            "budget_remaining": (
                round(self.budget_limit - self.total_cost, 4) if self.budget_limit else None
            ),
            "budget_utilized_percent": (
                round((self.total_cost / self.budget_limit * 100), 2) if self.budget_limit else 0
            ),
            "by_model": {m: round(c, 6) for m, c in by_model.items()},
            "requests": self.requests,
            "usage_log": self.usage_log,
        }

    def check_budget(self, budget_limit: Optional[float] = None) -> Tuple[bool, float]:
        """
        Check if within budget.

        **Preconditions:**
        - budget_limit: float >= 0 or None

        **Postconditions:**
        - Returns (within_budget: bool, remaining: float)
        - Raises: ValueError if budget_limit < 0
        """
        limit = budget_limit if budget_limit is not None else self.budget_limit

        # VALIDATION: limit is valid
        if limit is not None and limit < 0:
            raise ValueError(f"budget_limit must be >= 0, got {limit}")

        if limit is None:
            return True, float("inf")  # pragma: no cover

        remaining = limit - self.total_cost
        within_budget = remaining >= 0

        if not within_budget:
            msg = f"Budget exceeded: ${self.total_cost:.4f} spent, ${limit:.4f} available"
            logger.error(msg)
            self.alerts.append(
                {"type": "error", "message": msg, "timestamp": datetime.now().isoformat()}
            )
        elif remaining < limit * 0.2:
            msg = f"Budget warning: ${remaining:.4f} remaining (80% spent)"
            logger.warning(msg)
            self.alerts.append(
                {"type": "warning", "message": msg, "timestamp": datetime.now().isoformat()}
            )

        return within_budget, remaining

    def export_usage_log(self, filepath: str) -> None:
        """Export usage log to JSON file."""
        import json  # pragma: no cover
        from pathlib import Path  # pragma: no cover

        # pragma: no cover
        file_path = Path(filepath)  # pragma: no cover
        file_path.parent.mkdir(parents=True, exist_ok=True)  # pragma: no cover

        with open(file_path, "w", encoding="utf-8") as f:  # pragma: no cover
            json.dump(
                {"summary": self.get_summary(), "usage_log": self.usage_log}, f, indent=2
            )  # pragma: no cover
        # pragma: no cover
        logger.info(f"Usage log exported to {file_path}")  # pragma: no cover
