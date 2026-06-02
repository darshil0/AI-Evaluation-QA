from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


RUBRIC_CATEGORIES = {
    "acc",
    "accuracy",
    "helpfulness",
    "clarity",
    "style",
    "relevance",
    "safety",
    "reasoning",
    "completeness",
}


@dataclass
class RubricCriterion:
    key: str
    weight: float
    type: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Rubric:
    criteria: List[RubricCriterion] = field(default_factory=list)


@dataclass
class ScoreReport:
    data: Dict[str, Any]

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.data)


class ScoringEngine:
    def __init__(self, rubric: Optional[Rubric] = None):
        self.rubric = rubric or Rubric(criteria=[])

    def _normalize_value(self, value: Any) -> float:
        if value is None:
            return 0.0
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        try:
            v = float(value)
        except (TypeError, ValueError):
            return 0.0

        if v <= 0:
            return 0.0
        if v <= 1.0:
            return max(0.0, min(1.0, v))
        if v <= 5.0:
            return max(0.0, min(1.0, v / 5.0))
        if v <= 10.0:
            return max(0.0, min(1.0, v / 10.0))
        return max(0.0, min(1.0, v / 100.0))

    def _extract_json_block(self, text: str) -> Optional[str]:
        if not text:
            return None
        match = re.search(
            r"```json\s*(\{.*?\}|\[.*?\])\s*```",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()
        return None

    def _extract_last_number(self, text: str) -> Optional[float]:
        if not text:
            return None
        matches = re.findall(r"(?<!\w)(?:\d+(?:\.\d+)?|\.\d+)(?:/\d+(?:\.\d+)?)?", text)
        if not matches:
            return None
        raw = matches[-1]
        if "/" in raw:
            left, right = raw.split("/", 1)
            try:
                return float(left) / float(right)
            except Exception:
                return None
        try:
            return float(raw)
        except Exception:
            return None

    def _parse_judge_score(self, response: str, params: Dict[str, Any]) -> tuple[float, str]:
        json_key = params.get("json_key")
        if json_key:
            json_text = self._extract_json_block(response)
            if json_text:
                try:
                    payload = json.loads(json_text)
                    if isinstance(payload, dict) and json_key in payload:
                        score = self._normalize_value(payload.get(json_key))
                        return score, f"json key '{json_key}' parsed"
                except json.JSONDecodeError:
                    pass

        last_number = self._extract_last_number(response)
        if last_number is not None:
            return self._normalize_value(last_number), "numeric score parsed from last number"

        return 0.0, "no score found"

    def _apply_rule(self, response: str, params: Dict[str, Any]) -> tuple[float, str]:
        rule = params.get("rule")

        if rule == "length_within":
            max_len = int(params.get("max_len", 0))
            if max_len <= 0:
                return 0.0, "invalid rule params"
            return (1.0 if len(response) <= max_len else 0.0), "rule 'length_within' evaluated"

        if rule:
            return 0.0, f"using heuristic for rule: {rule}"

        return 0.0, "no rule provided"

    def score_response(self, *args: Any, **kwargs: Any) -> Union[Dict[str, Any], ScoreReport]:
        if len(args) == 1 and isinstance(args[0], dict):
            item = args[0]
            response = item.get("response", "")
            return_dict = True
        elif len(args) >= 2 and isinstance(args[0], dict):
            item = args[0]
            response = args[1]
            return_dict = False
        else:
            raise TypeError("score_response expects either (item) or (item, response)")

        report: Dict[str, Any] = {"id": item.get("id")}
        weighted_sum = 0.0
        total_weight = 0.0

        for criterion in self.rubric.criteria:
            key = criterion.key
            weight = float(criterion.weight or 0.0)
            ctype = criterion.type
            params = criterion.params or {}

            if ctype == "judge":
                score, notes = self._parse_judge_score(response, params)
            elif ctype == "rule":
                score, notes = self._apply_rule(response, params)
            else:
                score, notes = 0.0, f"unknown criterion type: {ctype}"

            report[f"score_{key}"] = score
            report[f"score_{key}_notes"] = notes

            weighted_sum += score * weight
            total_weight += weight

        report["aggregated_score"] = weighted_sum / total_weight if total_weight > 0 else 0.0

        if return_dict:
            return report
        return ScoreReport(report)
