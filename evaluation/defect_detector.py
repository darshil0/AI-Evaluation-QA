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
    }

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

        # Heuristic-based redundancy detection
        if response_text:
            words = response_text.split()
            if len(words) > 20:
                unique_ratio = len(set(w.lower() for w in words)) / len(words)
                if unique_ratio < 0.5:
                    defects.append("D05")

        return defects
