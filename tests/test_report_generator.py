import pytest
import pandas as pd
from pathlib import Path
from evaluation.report_generator import ReportGenerator


@pytest.fixture
def sample_scored_dataframe():
    return pd.DataFrame(
        {
            "prompt_id": ["P1", "P2", "P3", "P4", "P5"],
            "response": ["Response 1", "Response 2", "Response 3", "Response 4", "Response 5"],
            "overall_score": [4.5, 3.8, 2.1, 4.9, 3.2],
            "score_accuracy": [4.5, 4.0, 2.0, 5.0, 3.5],
            "score_reasoning": [4.5, 3.5, 2.5, 4.8, 3.0],
            "score_tone": [4.5, 4.0, 2.0, 5.0, 3.0],
            "score_completeness": [4.5, 3.8, 2.0, 4.8, 3.2],
            "grade": ["A", "B", "D", "A", "C"],
        }
    )


def test_generate_reports_valid_data(tmp_path, sample_scored_dataframe):
    """Test report generation with valid data"""
    generator = ReportGenerator(str(tmp_path))
    reports = generator.generate_reports(sample_scored_dataframe)

    assert "executive_summary" in reports
    assert (tmp_path / "executive_summary.md").exists()
    assert (tmp_path / "executive_summary.json").exists()


def test_generate_reports_empty_data(tmp_path):
    """Test report generation with empty data"""
    empty_df = pd.DataFrame()

    generator = ReportGenerator(str(tmp_path))
    reports = generator.generate_reports(empty_df)

    assert isinstance(reports, dict)
    assert len(reports) == 0


def test_executive_summary_content(tmp_path, sample_scored_dataframe):
    """Test executive summary contains expected content"""
    generator = ReportGenerator(str(tmp_path))
    summary_path = generator._generate_executive_summary(sample_scored_dataframe)

    with open(summary_path) as f:
        content = f.read()

    assert "Total Evaluations:** 5" in content
    assert "Average Score:" in content
    assert "Dimension Performance" in content


def test_generate_accuracy_chart(tmp_path, sample_scored_dataframe):
    """Test accuracy chart generation"""
    generator = ReportGenerator(str(tmp_path))
    scored_responses = sample_scored_dataframe.to_dict("records")
    # Use name expected by generate_accuracy_chart
    for r in scored_responses:
        r["accuracy"] = r["score_accuracy"]

    output_file = tmp_path / "accuracy.png"
    generator.generate_accuracy_chart(scored_responses, str(output_file))

    assert output_file.exists()


def test_generate_html_report(tmp_path, sample_scored_dataframe):
    """Test HTML report generation"""
    generator = ReportGenerator(str(tmp_path))
    scored_responses = sample_scored_dataframe.to_dict("records")
    output_file = tmp_path / "report.html"
    generator.generate_html_report(scored_responses, str(output_file))

    assert output_file.exists()
    with open(output_file) as f:
        content = f.read()
    assert "Evaluation Summary" in content
