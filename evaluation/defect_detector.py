import logging
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)


class DefectDetector:
    """Detects common defects in AI model responses."""

    DEFECT_TYPES = {
        "D01": "Logical Defect",
        "D02": "Factual Defect",
        "D03": "Tone Defect",
        "D04": "Incomplete Response",
        "D05": "Redundancy Defect",
        "D06": "Refusal/Avoidance",
        "D07": "Hallucination Warning",
    }

    _REFUSAL_PATTERNS = (
        "as an ai model",
        "as a large language model",
        "i cannot fulfill",
        "i am unable to provide",
        "against my safety guidelines",
        "my programming does not allow",
    )

    _HALLUCINATION_MARKERS = (
        "to the best of my knowledge",
        "as far as i know",
        "if i remember correctly",
        "i believe that",
        "it is possible that",
    )

    @staticmethod
    def detect_defects(response_text: str, scores: dict[str, Any]) -> list[str]:
        defects: list[str] = []

        def get_score(key: str) -> float:
            val = scores.get(key)
            if val is None:
                val = scores.get(f"{key}_score")
            if val is None:
                norm = scores.get(f"score_{key}")
                if norm is not None:
                    try:
                        val = float(norm) * 5.0
                    except (TypeError, ValueError):
                        val = None
            try:
                return float(val) if val is not None else 5.0
            except (TypeError, ValueError):
                return 5.0

        if get_score("reasoning") <= 2:
            defects.append("D01")
        if get_score("accuracy") <= 2:
            defects.append("D02")
        if get_score("tone") <= 2:
            defects.append("D03")
        if get_score("completeness") <= 2:
            defects.append("D04")

        if response_text:
            response_lower = response_text.lower()
            words = response_text.split()

            if len(words) > 20:
                normalized_words = [
                    w.strip(".,;:!?()[]{}\"'`").lower()
                    for w in words
                    if w.strip()
                ]
                if normalized_words:
                    unique_ratio = len(set(normalized_words)) / len(normalized_words)
                    if unique_ratio < 0.5:
                        defects.append("D05")

            if any(pattern in response_lower for pattern in DefectDetector._REFUSAL_PATTERNS):
                defects.append("D06")

            if any(marker in response_lower for marker in DefectDetector._HALLUCINATION_MARKERS):
                defects.append("D07")

        return sorted(set(defects))
