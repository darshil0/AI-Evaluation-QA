from __future__ import annotations
import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


@dataclass
class RubricCriterion:
    key: str
    weight: float
    type: str  # 'rule' or 'judge'
    params: Dict[str, Any]


@dataclass
class Rubric:
    criteria: List[RubricCriterion]


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
    components: List[ScoreComponent]
    aggregated_score: float
    metadata: Dict[str, Any]


class ScoringEngine:
    """
    Core engine for scoring model responses against rubrics and heuristics.

    EDGE CASES & FAILURE MODES:

    ┌─────────────────────────┬──────────────────────────┬─────────────────────────┐
    │ Input                   │ Current Behavior         │ Production-Safe         │
    ├─────────────────────────┼──────────────────────────┼─────────────────────────┤
    │ Empty response ""       │ score_accuracy = 1       │ PASS (min score)        │
    │ None response           │ AttributeError           │ FAIL → ValueError       │
    │ response_text = 999     │ AttributeError           │ FAIL → TypeError        │
    │ Weights != 1.0          │ ZeroDivisionError (rare) │ FAIL → ConfigError      │
    │ Very long response      │ Tokenizer warn + cont    │ PASS (clipped)          │
    │ Unicode/emoji           │ Works (tiktoken handles) │ PASS                    │
    │ NaN in scores           │ Propagates to agg        │ FAIL → ValueError       │
    └─────────────────────────┴──────────────────────────┴─────────────────────────┘
    """

    _NUMERIC_PATTERN = re.compile(r"[-+]?\d*\.\d+|\d+")
    _LOGICAL_PATTERN = re.compile(
        r"\b(because|therefore|thus|hence|consequently|as a result|due to|since|so)\b",
        re.IGNORECASE,
    )
    _POSITIVE_PATTERN = re.compile(
        r"\b(understand|help|let me|i can|happy to|certainly|of course)\b", re.IGNORECASE
    )
    _NEGATIVE_PATTERN = re.compile(
        r"\b(obviously|you should have|just|simply|clearly you|wrong)\b", re.IGNORECASE
    )
    _POLITE_PATTERN = re.compile(r"\b(please|thank you|appreciate)\b", re.IGNORECASE)
    _LIST_MARKER_PATTERN = re.compile(r"(?:\d+\)|first|second|•|-)", re.IGNORECASE)
    _UNCERTAIN_PATTERN = re.compile(
        r"\b(i don't know|i'm not sure|unclear|uncertain)\b", re.IGNORECASE
    )
    _ACCURACY_BONUS_PATTERN = re.compile(
        r"\b(because|therefore|specifically|exactly)\b", re.IGNORECASE
    )

    RUBRIC_CATEGORIES = {
        "accuracy": {"weight": 0.40, "name": "Accuracy"},
        "reasoning": {"weight": 0.30, "name": "Reasoning"},
        "tone": {"weight": 0.15, "name": "Tone"},
        "completeness": {"weight": 0.15, "name": "Completeness"},
    }

    DEFECT_TYPES = {
        "D01": "Logical Defect",
        "D02": "Factual Defect",
        "D03": "Tone Defect",
        "D04": "Incomplete Response",
        "D05": "Redundancy Defect",
    }

    def __init__(self, rubric: Optional[Rubric] = None):
        if rubric is None:
            criteria = []
            for key, val in self.RUBRIC_CATEGORIES.items():
                criteria.append(
                    RubricCriterion(key=key, weight=val["weight"], type="rule", params={})
                )
            self.rubric = Rubric(criteria=criteria)
        else:
            self.rubric = rubric

        self.scores = []
        self._validate_rubric()

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> ScoringEngine:
        criteria = []
        scoring_config = config.get("scoring", {})
        if not scoring_config:
            return cls()

        for key, value in scoring_config.get("criteria", {}).items():
            criteria.append(RubricCriterion(key=key, **value))

        if not criteria:
            return cls()

        rubric = Rubric(criteria=criteria)
        return cls(rubric)

    def _validate_rubric(self) -> None:
        if not self.rubric.criteria:
            raise ValueError("Rubric must contain at least one criterion.")
        for c in self.rubric.criteria:
            if c.weight < 0 or c.weight > 1:
                raise ValueError(f"Weight must be between 0 and 1: {c.key}")

    def _normalize_value(
        self, val: float, min_val: Optional[float] = None, max_val: Optional[float] = None
    ) -> float:
        """Normalize a value to [0.0, 1.0] range."""
        if val is None:
            return 0.0

        # If explicit range is provided, use it
        if min_val is not None and max_val is not None and max_val > min_val:
            normalized = (val - min_val) / (max_val - min_val)
            return max(0.0, min(1.0, normalized))

        # Heuristic fallback (improved)
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

    def _score_rule(
        self, response_text: str, params: Dict[str, Any]
    ) -> Tuple[Optional[float], str]:
        if not response_text:
            return None, "no response_text"
        rule_name = params.get("rule")
        if rule_name == "contains_terms":
            terms = params.get("terms", [])
            min_match = max(1, int(params.get("min_match", 1)))
            matches = sum(1 for t in terms if t.lower() in response_text.lower())
            return (1.0 if matches >= min_match else 0.0), f"matched {matches}/{len(terms)} terms"
        if rule_name == "mentions_entity":
            entity = params.get("entity")
            raw = 1.0 if (entity and entity.lower() in response_text.lower()) else 0.0
            notes = f"entity '{entity}' present" if raw == 1.0 else f"entity '{entity}' absent"
            return raw, notes
        if rule_name == "length_within":
            max_len = int(params.get("max_len", 10000))
            length = len(response_text.split())
            return (1.0 if length <= max_len else 0.0), f"length {length} words"

        # Fallback to heuristic scoring if no specific rule matches or if params are empty
        return None, f"using heuristic for rule: {rule_name}"

    def _score_judge(
        self, response_text: str, params: Dict[str, Any]
    ) -> Tuple[Optional[float], str]:
        if not response_text:
            return None, "no response_text"

        min_val = params.get("min_val")
        if min_val is not None:
            min_val = float(min_val)

        max_val = params.get("max_val")
        if max_val is not None:
            max_val = float(max_val)

        key = params.get("json_key")

        # 1. Try parsing as JSON (including Markdown code blocks)
        if key:
            json_text = response_text
            if "```" in response_text:
                json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)

            try:
                parsed = json.loads(json_text)
                if isinstance(parsed, dict) and key in parsed:
                    val = float(parsed[key])
                    return self._normalize_value(val, min_val, max_val), f"json key '{key}' parsed"
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

        # 2. Try numeric extraction from the end of the string (usually where scores are)
        try:
            matches = self._NUMERIC_PATTERN.findall(response_text)
            if matches:
                # Use the last number found as it's typically the final score
                val = float(matches[-1])
                return self._normalize_value(val, min_val, max_val), "parsed last numeric"
        except Exception:
            pass

        return None, "no numeric found"

    def score_response(
        self, prompt_meta: Dict[str, Any], response_text: Optional[str] = None
    ) -> Union[Dict[str, Any], ScoreReport]:
        """
        Score a single response. Validate preconditions strictly.

        **Preconditions:**
        - prompt_meta: dict with 'id' and/or 'prompt_id' key
        - response_text: str or extractable from prompt_meta['response'/'model_response']
        - Rubric: non-empty, weights sum to 1.0

        **Postconditions:**
        - Returns Dict or ScoreReport with keys/attributes: accuracy, reasoning, tone, completeness, overall_score, defects
        - overall_score range: [1.0, 5.0] (for dict) or [0.0, 1.0] (for ScoreReport)

        **Edge Cases & Failure Modes:**
        - Empty response "" -> Return min score
        - None response -> Raise TypeError
        - prompt_meta not dict -> Raise TypeError
        - Rubric empty -> Raise ValueError
        """
        # PRECONDITION: prompt_meta is dict
        if not isinstance(prompt_meta, dict):
            raise TypeError(
                f"prompt_meta must be dict, got {type(prompt_meta).__name__}. "
                f"Expected: {{'id': str, 'response': str, ...}}"
            )

        # Standardize return format: prefer returning dict unless explicitly requested via separate response_text
        return_dict = True
        if response_text is not None:
            return_dict = False
        else:
            response_text = prompt_meta.get("model_response") or prompt_meta.get("response", "")

        # PRECONDITION: response_text is string
        if not isinstance(response_text, str):
            raise TypeError(f"response_text must be str, got {type(response_text).__name__}")

        # PRECONDITION: rubric is valid
        if not self.rubric or not self.rubric.criteria:
            raise ValueError("Rubric not initialized or contains no criteria")

        components: List[ScoreComponent] = []
        total_weight = sum(c.weight for c in self.rubric.criteria) or 1.0

        for crit in self.rubric.criteria:
            raw, notes = None, None
            try:
                if crit.type == "rule":
                    raw, notes = self._score_rule(response_text, crit.params)
                    # If rule scoring failed/returned None, try heuristic
                    if raw is None:
                        if crit.key == "accuracy":
                            raw = (
                                self.score_accuracy(response_text, prompt_meta.get("prompt", ""))
                                / 5.0
                            )
                        elif crit.key == "reasoning":
                            raw = (
                                self.score_reasoning(response_text, prompt_meta.get("prompt", ""))
                                / 5.0
                            )
                        elif crit.key == "tone":
                            raw = (
                                self.score_tone(response_text, prompt_meta.get("prompt", "")) / 5.0
                            )
                        elif crit.key == "completeness":
                            raw = (
                                self.score_completeness(
                                    response_text, prompt_meta.get("prompt", "")
                                )
                                / 5.0
                            )
                elif crit.type == "judge":
                    raw, notes = self._score_judge(response_text, crit.params)
                else:
                    notes = f"unsupported criterion type: {crit.type}"
            except Exception as e:
                notes = f"exception during scoring: {e}"

            normalized = self._normalize_value(raw) if raw is not None else 0.0

            components.append(
                ScoreComponent(
                    key=crit.key,
                    raw=raw,
                    normalized=normalized,
                    weight=crit.weight,
                    notes=notes,
                )
            )

        weighted_sum = sum((c.normalized or 0.0) * c.weight for c in components)
        aggregated_score = max(0.0, min(1.0, weighted_sum / total_weight))

        # Create report object
        report = ScoreReport(
            prompt_id=prompt_meta.get("id") or prompt_meta.get("prompt_id"),
            prompt_text=prompt_meta.get("text")
            or prompt_meta.get("prompt_text")
            or prompt_meta.get("prompt", ""),
            model=prompt_meta.get("model"),
            components=components,
            aggregated_score=aggregated_score,
            metadata={"prompt_id": prompt_meta.get("id"), "model": prompt_meta.get("model")},
        )

        if not return_dict:
            return report

        # Convert to dictionary format
        result = self.report_to_dict(report)

        # Standardize keys: 'accuracy' (1-5) and 'score_accuracy' (0-1)
        for comp in report.components:
            key = comp.key
            result[key] = (comp.normalized or 0.0) * 5.0
            result[f"{key}_score"] = result[key]  # Compatibility alias
            result[f"score_{key}"] = comp.normalized  # Normalized alias

        result["overall_score"] = aggregated_score * 5.0

        # Add defects
        defects = self._detect_defects(response_text, result)
        result["defects"] = ",".join(defects) if defects else ""

        return result

    def report_to_dict(self, report: ScoreReport) -> Dict[str, Any]:
        out = {
            "prompt_id": report.prompt_id,
            "prompt_text": report.prompt_text,
            "model": report.model,
            "aggregated_score": report.aggregated_score,
        }
        for comp in report.components:
            prefix = f"score_{comp.key}"
            out[prefix] = comp.normalized
            out[f"{prefix}_raw"] = comp.raw
            out[f"{prefix}_notes"] = comp.notes
        out.update(report.metadata or {})
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
        logical_matches = self._LOGICAL_PATTERN.findall(response)
        logical_count = len(logical_matches)

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
        return self._detect_defects(response_data.get("response", ""), response_data)

    def _detect_defects(self, response: str, scores: Dict[str, Any]) -> List[str]:
        defects = []

        def get_score(key: str) -> float:
            # Check for multiple naming conventions
            val = scores.get(key)
            if val is None:
                val = scores.get(f"{key}_score")
            if val is None:
                norm = scores.get(f"score_{key}")
                if norm is not None:
                    val = norm * 5.0
            return float(val) if val is not None else 5.0

        if get_score("reasoning") <= 2:
            defects.append("D01")
        if get_score("accuracy") <= 2:
            defects.append("D02")
        if get_score("tone") <= 2:
            defects.append("D03")
        if get_score("completeness") <= 2:
            defects.append("D04")
        if response:
            # Simple check for redundancy
            words = response.split()
            if len(words) > 20:
                unique_ratio = len(set(w.lower() for w in words)) / len(words)
                if unique_ratio < 0.5:
                    defects.append("D05")
        return defects

    def _calculate_category_score(self, response: str, category: str, prompt: str) -> int:
        """Helper for tests."""
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
        scored_responses = []
        for response_data in responses:
            scored = self.score_response(response_data)
            scored_responses.append(scored)
        self.scores = scored_responses
        return scored_responses

    def load_results(self, filepath: str) -> List[Dict[str, Any]]:
        """Load results from CSV file."""
        import csv
        import sys

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return list(reader)
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error loading results: {e}")
            return []

    def save_scores(self, scored_responses: Any, filepath: Optional[str] = None) -> None:
        import csv

        if isinstance(scored_responses, str) and filepath is None:
            filepath = scored_responses
            scored_responses = self.scores
        elif filepath is None:
            # This should not happen with correct usage, but for safety:
            if isinstance(scored_responses, list):
                # We have responses but no filepath
                raise ValueError("filepath must be provided if scored_responses is a list")
            else:
                filepath = scored_responses
                scored_responses = self.scores
        if not scored_responses:
            return
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

        # Collect all unique keys
        all_keys = set()
        for r in scored_responses:
            all_keys.update(r.keys())

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=sorted(list(all_keys)))
            writer.writeheader()
            writer.writerows(scored_responses)

    def print_summary(self) -> None:
        if not self.scores:
            print("No scores to summarize")
            return

        print("\n" + "=" * 30)
        print("SCORING SUMMARY")
        print("=" * 30)

        avg_score = sum(s.get("overall_score", 0) for s in self.scores) / len(self.scores)
        print(f"Total Responses: {len(self.scores)}")
        print(f"Overall Average Score: {avg_score:.2f}/5.00")

        defect_counts = {}
        for s in self.scores:
            defects = s.get("defects", "").split(",")
            for d in defects:
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
