from __future__ import annotations

import csv
import json
import logging
import math
import os
import re
from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, List, Optional, Tuple

from evaluation.defect_detector import DefectDetector

logger = logging.getLogger(__name__)


@dataclass
class RubricCriterion:
    key: str
    weight: float
    type: str  # 'rule' or 'judge'
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Rubric:
    criteria: List[RubricCriterion] = field(default_factory=list)


@dataclass
class ScoreComponent:
    key: str
    raw: Optional[float]
    normalized: Optional[float]
    weight: float
    notes: Optional[str] = None


@dataclass
class ScoreReport:
    prompt_id: Any
    prompt_text: str
    model: Optional[str]
    response_text: str
    components: List[ScoreComponent]
    aggregated_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ScoringEngine:
    """
    Core engine for scoring model responses against rubrics and heuristics.
    """

    _NUMERIC_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"[-+]?\d*\.\d+|\d+")
    _LOGICAL_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"\b(because|therefore|thus|hence|consequently|as a result|due to|since|so|furthermore|moreover|specifically|nevertheless|however|alternatively)\b",
        re.IGNORECASE,
    )
    _POSITIVE_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"\b(understand|help|let me|i can|happy to|certainly|of course|delighted|pleasure|assist|welcome)\b",
        re.IGNORECASE,
    )
    _NEGATIVE_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"\b(obviously|you should have|just|simply|clearly you|wrong)\b", re.IGNORECASE
    )
    _POLITE_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"\b(please|thank you|appreciate)\b", re.IGNORECASE)
    _LIST_MARKER_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"(?:\d+\)|first|second|•|-)", re.IGNORECASE)
    _UNCERTAIN_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"\b(i don't know|i'm not sure|unclear|uncertain)\b", re.IGNORECASE
    )
    _ACCURACY_BONUS_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"\b(because|therefore|specifically|exactly|precisely|in fact|evidently|documented)\b",
        re.IGNORECASE,
    )

    RUBRIC_CATEGORIES: ClassVar[Dict[str, Dict[str, Any]]] = {
        "accuracy": {"weight": 0.40, "name": "Accuracy"},
        "reasoning": {"weight": 0.30, "name": "Reasoning"},
        "tone": {"weight": 0.15, "name": "Tone"},
        "completeness": {"weight": 0.15, "name": "Completeness"},
    }

    def __init__(self, rubric: Optional[Rubric] = None):
        if rubric is None:
            self.rubric = Rubric(
                criteria=[
                    RubricCriterion(key=key, weight=float(val["weight"]), type="rule")
                    for key, val in self.RUBRIC_CATEGORIES.items()
                ]
            )
        else:
            self.rubric = rubric

        self.scores: List[Dict[str, Any]] = []
        self._validate_rubric()

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> ScoringEngine:
        scoring_config = config.get("scoring", {})
        criteria_cfg = scoring_config.get("criteria", {})

        if not criteria_cfg:
            return cls()

        criteria: List[RubricCriterion] = []
        for key, value in criteria_cfg.items():
            if not isinstance(value, dict):
                raise TypeError(f"Criterion config for '{key}' must be a dict.")
            criterion_type = str(value.get("type", "rule"))
            weight = float(value.get("weight", 0.0))
            params = value.get("params", {})
            if params is None:
                params = {}
            if not isinstance(params, dict):
                raise TypeError(f"Criterion params for '{key}' must be a dict.")

            if "min_score" in value and "min_val" not in params:
                params["min_val"] = value["min_score"]
            if "max_score" in value and "max_val" not in params:
                params["max_val"] = value["max_score"]

            criteria.append(RubricCriterion(key=key, weight=weight, type=criterion_type, params=params))

        return cls(Rubric(criteria=criteria)) if criteria else cls()

    def _validate_rubric(self) -> None:
        if not self.rubric.criteria:
            raise ValueError("Rubric must contain at least one criterion.")

        total_weight = sum(c.weight for c in self.rubric.criteria)
        if not math.isfinite(total_weight) or total_weight <= 0:
            raise ValueError("Rubric weights must sum to a positive finite value.")

        for c in self.rubric.criteria:
            if not math.isfinite(c.weight):
                raise ValueError(f"Weight must be finite: {c.key}")
            if c.weight < 0:
                raise ValueError(f"Weight must be non-negative: {c.key}")

        if abs(total_weight - 1.0) > 1e-6:
            logger.warning("Rubric weights sum to %s, not 1.0; scores will be normalized.", total_weight)

    def _normalize_value(
        self, val: Optional[float], min_val: Optional[float] = None, max_val: Optional[float] = None
    ) -> float:
        if val is None or not isinstance(val, (int, float)) or not math.isfinite(val):
            return 0.0

        val = float(val)

        if min_val is not None and max_val is not None and max_val > min_val:
            normalized = (val - min_val) / (max_val - min_val)
            return max(0.0, min(1.0, normalized))

        if val < 0:
            return 0.0
        if val <= 1.0:
            return val
        if val <= 5.0:
            return val / 5.0
        if val <= 10.0:
            return val / 10.0
        if val <= 100.0:
            return val / 100.0
        return 1.0

    def _score_rule(self, response_text: str, params: Dict[str, Any]) -> Tuple[Optional[float], str]:
        if not response_text:
            return None, "no response_text"

        rule_name = params.get("rule")
        if rule_name == "contains_terms":
            terms = params.get("terms", [])
            if not isinstance(terms, list):
                raise TypeError("params['terms'] must be a list")
            min_match = max(1, int(params.get("min_match", 1)))
            matches = sum(1 for t in terms if str(t).lower() in response_text.lower())
            return (1.0 if matches >= min_match else 0.0), f"matched {matches}/{len(terms)} terms"

        if rule_name == "mentions_entity":
            entity = params.get("entity")
            raw = 1.0 if (entity and str(entity).lower() in response_text.lower()) else 0.0
            notes = f"entity '{entity}' present" if raw == 1.0 else f"entity '{entity}' absent"
            return raw, notes

        if rule_name == "length_within":
            max_len = int(params.get("max_len", 10000))
            length = len(response_text.split())
            return (1.0 if length <= max_len else 0.0), f"length {length} words"

        return None, f"using heuristic for rule: {rule_name}"

    def _extract_json_block(self, text: str) -> Optional[str]:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
        return match.group(1) if match else None

    def _score_judge(self, response_text: str, params: Dict[str, Any]) -> Tuple[Optional[float], str]:
        if not response_text:
            return None, "no response_text"

        min_val = params.get("min_val")
        if min_val is not None:
            min_val = float(min_val)

        max_val = params.get("max_val")
        if max_val is not None:
            max_val = float(max_val)

        key = params.get("json_key")
        if key:
            json_text = self._extract_json_block(response_text) or response_text
            try:
                parsed = json.loads(json_text)
                if isinstance(parsed, dict) and key in parsed:
                    val = float(parsed[key])
                    return self._normalize_value(val, min_val, max_val), f"json key '{key}' parsed"
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

        matches = self._NUMERIC_PATTERN.findall(response_text)
        if matches:
            try:
                val = float(matches[-1])
                return self._normalize_value(val, min_val, max_val), "parsed last numeric"
            except (ValueError, TypeError):
                pass

        return None, "no numeric found"

    def score_response(
        self, prompt_meta: Dict[str, Any], response_text: Optional[str] = None
    ) -> ScoreReport:
        if not isinstance(prompt_meta, dict):
            raise TypeError(f"prompt_meta must be dict, got {type(prompt_meta).__name__}")

        if response_text is None:
            response_text = prompt_meta.get("model_response") or prompt_meta.get("response", "")

        if not isinstance(response_text, str):
            raise TypeError(f"response_text must be str, got {type(response_text).__name__}")

        if not self.rubric or not self.rubric.criteria:
            raise ValueError("Rubric not initialized or contains no criteria")

        components: List[ScoreComponent] = []
        total_weight = sum(c.weight for c in self.rubric.criteria)

        prompt_text = (
            prompt_meta.get("text")
            or prompt_meta.get("prompt_text")
            or prompt_meta.get("prompt", "")
        )

        for crit in self.rubric.criteria:
            raw: Optional[float] = None
            notes: Optional[str] = None
            try:
                if crit.type == "rule":
                    raw, notes = self._score_rule(response_text, crit.params)
                    if raw is None:
                        if crit.key == "accuracy":
                            raw = self.score_accuracy(response_text, prompt_text) / 5.0
                        elif crit.key == "reasoning":
                            raw = self.score_reasoning(response_text, prompt_text) / 5.0
                        elif crit.key == "tone":
                            raw = self.score_tone(response_text, prompt_text) / 5.0
                        elif crit.key == "completeness":
                            raw = self.score_completeness(response_text, prompt_text) / 5.0
                elif crit.type == "judge":
                    raw, notes = self._score_judge(response_text, crit.params)
                else:
                    notes = f"unsupported criterion type: {crit.type}"
            except Exception as e:
                notes = f"exception during scoring: {e}"

            normalized = self._normalize_value(raw) if raw is not None else 0.0
            components.append(ScoreComponent(crit.key, raw, normalized, crit.weight, notes))

        weighted_sum = sum((c.normalized or 0.0) * c.weight for c in components)
        aggregated_score = max(0.0, min(1.0, weighted_sum / total_weight if total_weight else 0.0))

        return ScoreReport(
            prompt_id=prompt_meta.get("id") or prompt_meta.get("prompt_id"),
            prompt_text=prompt_text,
            model=prompt_meta.get("model"),
            response_text=response_text,
            components=components,
            aggregated_score=aggregated_score,
            metadata={"prompt_id": prompt_meta.get("id"), "model": prompt_meta.get("model")},
        )

    def report_to_dict(self, report: ScoreReport, include_defects: bool = False) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "prompt_id": report.prompt_id,
            "prompt_text": report.prompt_text,
            "model": report.model,
            "response": report.response_text,
            "aggregated_score": report.aggregated_score,
            "overall_score": report.aggregated_score * 5.0,
        }

        for comp in report.components:
            prefix = f"score_{comp.key}"
            out[prefix] = comp.normalized
            out[f"{prefix}_raw"] = comp.raw
            out[f"{prefix}_notes"] = comp.notes
            score_1_to_5 = (comp.normalized or 0.0) * 5.0
            out[comp.key] = score_1_to_5
            out[f"{comp.key}_score"] = score_1_to_5

        out.update(report.metadata or {})

        if include_defects:
            defects = self._detect_defects(report.response_text, out)
            out["defects"] = ",".join(defects) if defects else ""

        return out

    def validate_report_integrity(self, report: Any) -> bool:
        return (
            isinstance(report, ScoreReport)
            and isinstance(report.components, list)
            and all(isinstance(c, ScoreComponent) for c in report.components)
        )

    def score_accuracy(self, response: str, prompt: str) -> int:
        if not response or not response.strip():
            return 1
        if self._UNCERTAIN_PATTERN.search(response):
            return 2
        score = 3
        if len(response.split()) > 20:
            score += 1
        if self._ACCURACY_BONUS_PATTERN.search(response):
            score += 1
        return min(5, max(1, score))

    def score_reasoning(self, response: str, prompt: str) -> int:
        if not response or not response.strip():
            return 1
        score = 3
        logical_count = len(self._LOGICAL_PATTERN.findall(response))
        if logical_count >= 2:
            score += 1
        elif logical_count == 0:
            score -= 1
        if self._LIST_MARKER_PATTERN.search(response):
            score += 1
        return min(5, max(1, score))

    def score_tone(self, response: str, prompt: str) -> int:
        if not response or not response.strip():
            return 1
        score = 3
        if self._POSITIVE_PATTERN.search(response):
            score += 1
        if self._NEGATIVE_PATTERN.search(response):
            score -= 1
        if self._POLITE_PATTERN.search(response):
            score += 1
        return min(5, max(1, score))

    def score_completeness(self, response: str, prompt: str) -> int:
        if not response or not response.strip():
            return 1
        word_count = len(response.split())
        if word_count < 10:
            score = 2
        elif word_count < 30:
            score = 3
        elif word_count < 100:
            score = 4
        else:
            score = 5
        if self._LIST_MARKER_PATTERN.search(response):
            score = min(5, score + 1)
        return max(1, score)

    def identify_defects(self, response_data: Dict[str, Any]) -> List[str]:
        return DefectDetector.detect_defects(response_data.get("response", ""), response_data)

    def _detect_defects(self, response: str, scores: Dict[str, Any]) -> List[str]:
        return DefectDetector.detect_defects(response, scores)

    def _calculate_category_score(self, response: str, category: str, prompt: str) -> int:
        if category == "accuracy":
            return self.score_accuracy(response, prompt)
        if category == "reasoning":
            return self.score_reasoning(response, prompt)
        if category == "tone":
            return self.score_tone(response, prompt)
        if category == "completeness":
            return self.score_completeness(response, prompt)
        return 3

    def score_batch(self, responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        scored_responses: List[Dict[str, Any]] = []
        for response_data in responses:
            report = self.score_response(response_data)
            scored = self.report_to_dict(report, include_defects=True)
            scored_responses.append(scored)
        self.scores = scored_responses
        return scored_responses

    def load_results(self, filepath: str) -> List[Dict[str, Any]]:
        try:
            with open(filepath, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                return list(reader)
        except FileNotFoundError:
            logger.error("File not found: %s", filepath)
            raise
        except Exception as e:
            logger.error("Error loading results: %s", e)
            return []

    def save_scores(self, scored_responses: List[Dict[str, Any]], filepath: str) -> None:
        if not filepath:
            raise ValueError("filepath is required")
        if not scored_responses:
            return

        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

        all_keys: set[str] = set()
        for r in scored_responses:
            all_keys.update(r.keys())

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
            writer.writeheader()
            writer.writerows(scored_responses)

    def print_summary(self) -> None:
        if not self.scores:
            print("No scores to summarize")
            return

        import pandas as pd

        df = pd.DataFrame(self.scores)
        print("\n" + "=" * 30)
        print("SCORING SUMMARY")
        print("=" * 30)

        score_col = "overall_score" if "overall_score" in df.columns else "aggregated_score"
        avg_score = df[score_col].mean()
        threshold = 3.5 if score_col == "overall_score" else 0.7
        success_rate = (df[score_col] >= threshold).sum() / len(df) * 100 if len(df) > 0 else 0

        if score_col == "aggregated_score":
            avg_score *= 5.0

        print(f"Total Responses: {len(self.scores)}")
        print(f"Overall Average Score: {avg_score:.2f}/5.00")
        print(f"Success Rate: {success_rate:.1f}%")

        defect_counts: Dict[str, int] = {}
        for s in self.scores:
            for d in str(s.get("defects", "")).split(","):
                if d:
                    defect_counts[d] = defect_counts.get(d, 0) + 1

        if defect_counts:
            print("\nDefects Detected:")
            for d, count in defect_counts.items():
                print(f"- {d}: {count}")
        print("=" * 30 + "\n")


def score_responses(
    responses: List[Dict[str, Any]], config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    engine = ScoringEngine.from_config(config) if config else ScoringEngine()
    return engine.score_batch(responses)
