import pytest
import pandas as pd
from pathlib import Path
from scripts.regression_checker import RegressionDetector


@pytest.fixture
def baseline_df():
    return pd.DataFrame(
        {
            "prompt_id": [f"P{i}" for i in range(10)],
            "overall_score": [4.5, 4.2, 4.0, 3.8, 4.1, 4.3, 4.0, 3.9, 4.2, 4.4],
            "score_accuracy": [4.5, 4.0, 4.2, 3.9, 4.1, 4.3, 4.0, 3.8, 4.2, 4.5],
            "grade": ["A", "B", "B", "B", "B", "B", "B", "B", "B", "A"],
        }
    )


@pytest.fixture
def current_df_no_regression():
    return pd.DataFrame(
        {
            "prompt_id": [f"P{i}" for i in range(10)],
            "overall_score": [4.4, 4.3, 4.1, 3.9, 4.0, 4.2, 4.1, 4.0, 4.3, 4.5],
            "score_accuracy": [4.4, 4.1, 4.3, 4.0, 4.0, 4.2, 4.1, 3.9, 4.3, 4.6],
            "grade": ["A", "B", "B", "B", "B", "B", "B", "B", "B", "A"],
        }
    )


@pytest.fixture
def current_df_with_regression():
    return pd.DataFrame(
        {
            "prompt_id": [f"P{i}" for i in range(10)],
            "overall_score": [2.5, 2.2, 2.0, 1.8, 2.1, 2.3, 2.0, 1.9, 2.2, 2.4],
            "score_accuracy": [2.5, 2.0, 2.2, 1.9, 2.1, 2.3, 2.0, 1.8, 2.2, 2.5],
            "grade": ["C", "D", "D", "D", "D", "C", "D", "D", "C", "C"],
        }
    )


def test_no_baseline(tmp_path, current_df_no_regression):
    """Test handling when no baseline exists"""
    detector = RegressionDetector(str(tmp_path / "baseline.csv"))
    results = detector.check_regression(current_df_no_regression)

    assert results["has_regression"] == False
    assert "No baseline available" in results["reason"]


def test_no_regression_detected(tmp_path, baseline_df, current_df_no_regression):
    """Test when no regression is detected"""
    baseline_path = tmp_path / "baseline.csv"
    baseline_df.to_csv(baseline_path, index=False)

    detector = RegressionDetector(str(baseline_path))
    results = detector.check_regression(current_df_no_regression)

    assert results["has_regression"] == False


def test_regression_detected(tmp_path, baseline_df, current_df_with_regression):
    """Test when regression is detected"""
    baseline_path = tmp_path / "baseline.csv"
    baseline_df.to_csv(baseline_path, index=False)

    detector = RegressionDetector(str(baseline_path))
    results = detector.check_regression(current_df_with_regression)

    assert results["has_regression"] == True
    assert len(results["regressions"]) > 0


def test_insufficient_samples(tmp_path):
    """Test handling of insufficient sample size"""
    baseline_path = tmp_path / "baseline.csv"
    small_df = pd.DataFrame(
        {"prompt_id": ["P1", "P2"], "overall_score": [4.0, 4.5], "grade": ["B", "A"]}
    )
    small_df.to_csv(baseline_path, index=False)

    detector = RegressionDetector(str(baseline_path))
    results = detector.check_regression(small_df)

    assert results["has_regression"] == False
    assert "Insufficient samples" in results["reason"]


def test_save_as_baseline(tmp_path, current_df_no_regression):
    """Test saving current results as baseline"""
    baseline_path = tmp_path / "baseline.csv"

    detector = RegressionDetector(str(baseline_path))
    detector.save_as_baseline(current_df_no_regression)

    assert baseline_path.exists()
    loaded_df = pd.read_csv(baseline_path)
    assert len(loaded_df) == len(current_df_no_regression)


def test_generate_regression_report(tmp_path, baseline_df, current_df_with_regression):
    """Test report generation"""
    baseline_path = tmp_path / "baseline.csv"
    baseline_df.to_csv(baseline_path, index=False)

    detector = RegressionDetector(str(baseline_path))
    results = detector.check_regression(current_df_with_regression)
    report = detector.generate_regression_report(results)

    assert "REGRESSIONS DETECTED" in report
    assert "Overall Score" in report
