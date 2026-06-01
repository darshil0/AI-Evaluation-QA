import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
from typing import Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)


class RegressionDetector:
    def __init__(self, baseline_path: str, confidence_level: float = 0.95):
        self.baseline_path = Path(baseline_path)
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level

    def check_regression(self, current_results: pd.DataFrame, min_sample_size: int = 5) -> Dict:
        """Check for statistically significant regressions"""

        if not self.baseline_path.exists():
            logger.warning(f"No baseline found at {self.baseline_path}")
            return {"has_regression": False, "reason": "No baseline available", "details": {}}

        baseline_df = pd.read_csv(self.baseline_path)

        # Check sample sizes
        if len(baseline_df) < min_sample_size or len(current_results) < min_sample_size:
            logger.warning("Insufficient sample size for statistical testing")
            return {
                "has_regression": False,
                "reason": f"Insufficient samples (need at least {min_sample_size})",
                "details": {},
            }

        results = {
            "has_regression": False,
            "regressions": [],
            "improvements": [],
            "stable_metrics": [],
            "statistical_details": {},
        }

        # Check overall score
        overall_result = self._check_metric_regression(
            baseline_df["overall_score"], current_results["overall_score"], "Overall Score"
        )

        if overall_result["is_regression"]:
            results["has_regression"] = True
            results["regressions"].append(overall_result)
        elif overall_result["is_improvement"]:
            results["improvements"].append(overall_result)
        else:
            results["stable_metrics"].append("Overall Score")

        # Check dimension scores
        dimensions = ["accuracy", "reasoning", "tone", "completeness"]
        for dim in dimensions:
            col_name = f"score_{dim}"
            if col_name in baseline_df.columns and col_name in current_results.columns:
                dim_result = self._check_metric_regression(
                    baseline_df[col_name], current_results[col_name], dim.capitalize()
                )

                if dim_result["is_regression"]:
                    results["has_regression"] = True
                    results["regressions"].append(dim_result)
                elif dim_result["is_improvement"]:
                    results["improvements"].append(dim_result)
                else:
                    results["stable_metrics"].append(dim.capitalize())

        # Check grade distribution
        grade_result = self._check_grade_regression(baseline_df, current_results)
        if grade_result["is_regression"]:
            results["has_regression"] = True
            results["regressions"].append(grade_result)

        return results

    def _check_metric_regression(
        self,
        baseline_values: pd.Series,
        current_values: pd.Series,
        metric_name: str,
        effect_size_threshold: float = 0.3,
    ) -> Dict:
        """Check if a metric has regressed using statistical tests"""

        # Remove NaN values
        baseline_clean = baseline_values.dropna()
        current_clean = current_values.dropna()

        baseline_mean = baseline_clean.mean()
        current_mean = current_clean.mean()

        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt((baseline_clean.std() ** 2 + current_clean.std() ** 2) / 2)
        cohens_d = (current_mean - baseline_mean) / pooled_std if pooled_std > 0 else 0

        # Perform t-test
        t_stat, p_value = stats.ttest_ind(current_clean, baseline_clean)

        # Determine if regression based on:
        # 1. Statistical significance (p-value < alpha)
        # 2. Practical significance (effect size > threshold)
        # 3. Direction (current < baseline)

        is_significant = p_value < self.alpha
        is_large_effect = abs(cohens_d) > effect_size_threshold
        is_worse = current_mean < baseline_mean

        is_regression = is_significant and is_large_effect and is_worse
        is_improvement = is_significant and is_large_effect and not is_worse

        percent_change = (
            ((current_mean - baseline_mean) / baseline_mean * 100) if baseline_mean != 0 else 0
        )

        return {
            "metric": metric_name,
            "baseline_mean": round(baseline_mean, 3),
            "current_mean": round(current_mean, 3),
            "percent_change": round(percent_change, 2),
            "cohens_d": round(cohens_d, 3),
            "p_value": round(p_value, 4),
            "is_significant": is_significant,
            "is_large_effect": is_large_effect,
            "is_regression": is_regression,
            "is_improvement": is_improvement,
            "confidence_level": self.confidence_level,
        }

    def _check_grade_regression(self, baseline_df: pd.DataFrame, current_df: pd.DataFrame) -> Dict:
        """Check for regression in grade distribution"""

        baseline_grades = baseline_df["grade"].value_counts(normalize=True)
        current_grades = current_df["grade"].value_counts(normalize=True)

        # Calculate percentage of failing grades (D and F)
        baseline_fail_pct = (baseline_grades.get("D", 0) + baseline_grades.get("F", 0)) * 100
        current_fail_pct = (current_grades.get("D", 0) + current_grades.get("F", 0)) * 100

        # Chi-square test for grade distribution
        all_grades = ["A", "B", "C", "D", "F"]
        baseline_counts = [baseline_df[baseline_df["grade"] == g].shape[0] for g in all_grades]
        current_counts = [current_df[current_df["grade"] == g].shape[0] for g in all_grades]

        try:
            chi2, p_value = stats.chisquare(current_counts, baseline_counts)
        except Exception as e:
            logger.warning(f"Could not perform chi-square test: {e}")
            chi2, p_value = 0, 1.0

        # Regression if fail rate increased significantly
        fail_increase = current_fail_pct - baseline_fail_pct
        is_regression = fail_increase > 10 and p_value < self.alpha

        return {
            "metric": "Grade Distribution",
            "baseline_fail_pct": round(baseline_fail_pct, 2),
            "current_fail_pct": round(current_fail_pct, 2),
            "fail_increase": round(fail_increase, 2),
            "chi2": round(chi2, 3),
            "p_value": round(p_value, 4),
            "is_regression": is_regression,
            "is_improvement": False,
        }

    def save_as_baseline(self, results_df: pd.DataFrame):
        """Save current results as new baseline"""
        self.baseline_path.parent.mkdir(parents=True, exist_ok=True)
        results_df.to_csv(self.baseline_path, index=False)
        logger.info(f"Saved new baseline to {self.baseline_path}")

    def generate_regression_report(self, regression_results: Dict) -> str:
        """Generate human-readable regression report"""
        report = ["# Regression Detection Report\n"]

        if regression_results.get("reason"):
            report.append(f"**Status:** {regression_results['reason']}\n")
            return "\n".join(report)

        if regression_results["has_regression"]:
            report.append("## ⚠️ REGRESSIONS DETECTED\n")
            for reg in regression_results["regressions"]:
                report.append(f"### {reg['metric']}")
                report.append(
                    f"- Baseline: {reg.get('baseline_mean', reg.get('baseline_fail_pct', 'N/A'))}"
                )
                report.append(
                    f"- Current: {reg.get('current_mean', reg.get('current_fail_pct', 'N/A'))}"
                )
                if "percent_change" in reg:
                    report.append(f"- Change: {reg['percent_change']:+.2f}%")
                if "cohens_d" in reg:
                    report.append(f"- Effect Size (Cohen's d): {reg['cohens_d']}")
                report.append(f"- P-value: {reg['p_value']}")
                report.append("")
        else:
            report.append("## ✅ No Significant Regressions\n")

        if regression_results.get("improvements"):
            report.append("## 📈 Improvements\n")
            for imp in regression_results["improvements"]:
                report.append(f"- **{imp['metric']}**: {imp['percent_change']:+.2f}%")
            report.append("")

        if regression_results.get("stable_metrics"):
            report.append("## 📊 Stable Metrics\n")
            report.append(", ".join(regression_results["stable_metrics"]))
            report.append("")

        return "\n".join(report)


# CLI entrypoint
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python check_regression.py <current_results_file> [--baseline <baseline_file>] [--save-baseline]"
        )
        sys.exit(1)

    current_file = sys.argv[1]
    baseline_file = "reports/baseline.csv"
    save_baseline = False

    # Parse arguments
    if "--baseline" in sys.argv:
        idx = sys.argv.index("--baseline")
        baseline_file = sys.argv[idx + 1]

    if "--save-baseline" in sys.argv:
        save_baseline = True

    # Load current results
    current_df = pd.read_csv(current_file)

    # Check regression
    detector = RegressionDetector(baseline_file)
    results = detector.check_regression(current_df)

    # Generate and print report
    report = detector.generate_regression_report(results)
    print(report)

    # Save as baseline if requested
    if save_baseline:
        detector.save_as_baseline(current_df)
        print(f"\n✅ Saved as new baseline: {baseline_file}")

    # Exit with error code if regression detected
    sys.exit(1 if results["has_regression"] else 0)
