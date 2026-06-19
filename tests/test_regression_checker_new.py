import os
import tempfile

import pandas as pd
import pytest

from scripts.regression_checker import RegressionDetector


@pytest.fixture
def baseline_df():
    return pd.DataFrame(
        {
            "overall_score": [4.0, 4.2, 3.8, 4.5, 4.1, 4.3],
            "score_accuracy": [4.5, 4.4, 4.6, 4.7, 4.5, 4.4],
            "score_reasoning": [4.0, 3.9, 4.1, 4.2, 4.0, 3.8],
            "score_tone": [5.0, 4.9, 5.0, 4.8, 5.0, 4.9],
            "score_completeness": [3.5, 3.6, 3.4, 3.7, 3.5, 3.4],
            "grade": ["A", "A", "B", "A", "A", "B"],
        }
    )


@pytest.fixture
def current_df_regression():
    return pd.DataFrame(
        {
            "overall_score": [2.0, 2.1, 1.9, 2.2, 2.0, 2.1],
            "score_accuracy": [2.5, 2.4, 2.6, 2.7, 2.5, 2.4],
            "score_reasoning": [2.0, 1.9, 2.1, 2.2, 2.0, 1.8],
            "score_tone": [5.0, 4.9, 5.0, 4.8, 5.0, 4.9],
            "score_completeness": [1.5, 1.6, 1.4, 1.7, 1.5, 1.4],
            "grade": ["D", "F", "D", "C", "F", "D"],
        }
    )


def test_regression_detector_no_baseline():
    detector = RegressionDetector("non_existent.csv")
    results = detector.check_regression(pd.DataFrame())
    assert results["has_regression"] is False
    assert "No baseline" in results["reason"]


def test_regression_detector_insufficient_samples(baseline_df):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        baseline_df.to_csv(f.name, index=False)
        temp_csv = f.name

    try:
        detector = RegressionDetector(temp_csv)
        results = detector.check_regression(pd.DataFrame({"overall_score": [4.0]}))
        assert results["has_regression"] is False
        assert "Insufficient samples" in results["reason"]
    finally:
        os.unlink(temp_csv)


def test_regression_detector_detects_regression(baseline_df, current_df_regression):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        baseline_df.to_csv(f.name, index=False)
        temp_csv = f.name

    try:
        detector = RegressionDetector(temp_csv)
        results = detector.check_regression(current_df_regression)
        assert results["has_regression"] is True
        assert len(results["regressions"]) > 0

        report = detector.generate_regression_report(results)
        assert "REGRESSIONS DETECTED" in report
    finally:
        os.unlink(temp_csv)


def test_save_as_baseline(baseline_df):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=True) as f:
        temp_csv = f.name

    detector = RegressionDetector(temp_csv)
    detector.save_as_baseline(baseline_df)
    assert os.path.exists(temp_csv)
    os.unlink(temp_csv)
