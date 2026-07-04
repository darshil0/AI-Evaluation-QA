"""Automated defect detection for model responses."""

import logging
from typing import Any, Dict, List

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

    _REFUSAL_PATTERNS = [
        "as an ai model",
        "as a large language model",
        "i cannot fulfill",
        "i am unable to provide",
        "against my safety guidelines",
        "my programming does not allow",
    ]

    _HALLUCINATION_MARKERS = [
        "to the best of my knowledge",
        "as far as i know",
        "if i remember correctly",
        "i believe that",
        "it is possible that",
    ]

    @staticmethod
    def detect_defects(response_text: str, scores: Dict[str, Any]) -> List[str]:
        """
        Identify defects based on scores and response text heuristics.

        Args:
            response_text: The actual text response from the model.
            scores: Dictionary containing scores for different dimensions.

        Returns:
            List of defect codes (e.g., ["D01", "D05"]).
        """
        defects: List[str] = []

        def get_score(key: str) -> float:
            # Handle different possible score formats in the dictionary
            val = scores.get(key)
            if val is None:
                val = scores.get(f"{key}_score")
            if val is None:
                norm = scores.get(f"score_{key}")
                if norm is not None:
                    val = float(norm) * 5.0
            return float(val) if val is not None else 5.0

        # Threshold-based defect detection
        if get_score("reasoning") <= 2:
            defects.append("D01")
        if get_score("accuracy") <= 2:
            defects.append("D02")
        if get_score("tone") <= 2:
            defects.append("D03")
        if get_score("completeness") <= 2:
            defects.append("D04")

        # Heuristic-based detection
        if response_text:
            response_lower = response_text.lower()
            words = response_text.split()

            # Redundancy detection
            if len(words) > 20:
                unique_ratio = len(set(w.lower() for w in words)) / len(words)
                if unique_ratio < 0.5:
                    defects.append("D05")

            # Refusal detection
            if any(pattern in response_lower for pattern in DefectDetector._REFUSAL_PATTERNS):
                defects.append("D06")

            # Hallucination warning markers
            if any(marker in response_lower for marker in DefectDetector._HALLUCINATION_MARKERS):
                defects.append("D07")

        return defects
