"""
Edge case and complete coverage tests for ReportGenerator.
"""

import csv
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from evaluation.report_generator import ReportGenerator, generate_reports

try:
    import matplotlib  # noqa: F401

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import pandas as pd  # noqa: F401

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import plotly  # noqa: F401

    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


class TestReportGeneratorEdgeCases:
    """Edge case tests to achieve 100% coverage."""

    def test_initialization_default_output_dir(self):
        """Test initialization with default output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "reports", "sample_run")
            generator = ReportGenerator(output_dir)
            assert generator.output_dir.exists()

    def test_initialization_creates_directory(self):
        """Test initialization creates output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "new_dir", "reports")
            ReportGenerator(output_dir)
            assert os.path.exists(output_dir)

    def test_load_data_from_csv(self):
        """Test load_data loads CSV correctly."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["prompt_id", "response", "accuracy"])
            writer.writeheader()
            writer.writerow({"prompt_id": "p1", "response": "Answer", "accuracy": "5"})
            writer.writerow({"prompt_id": "p2", "response": "Answer2", "accuracy": "4"})
            temp_file = f.name

        try:
            generator = ReportGenerator()
            data = generator.load_data(temp_file)
            assert len(data) == 2
            assert data[0]["prompt_id"] == "p1"
        finally:
            os.unlink(temp_file)

    def test_load_data_file_not_found(self):
        """Test load_data raises FileNotFoundError for non-existent file."""
        generator = ReportGenerator()
        with pytest.raises(FileNotFoundError):
            generator.load_data("non_existent_file_xyz_123.csv")

    def test_load_data_directory_raises_exception(self):
        """Test load_data handles exceptions when opening directory instead of file."""
        generator = ReportGenerator()
        with tempfile.TemporaryDirectory() as tmpdir:
            data = generator.load_data(tmpdir)
            assert data == []

    def test_calculate_statistics_empty_list(self):
        """Test calculate_statistics with empty list."""
        generator = ReportGenerator()
        stats = generator.calculate_statistics([])
        assert stats == {}

    def test_calculate_statistics_valid_data(self):
        """Test calculate_statistics with valid data."""
        generator = ReportGenerator()
        data = [
            {
                "accuracy": "5",
                "reasoning": "4",
                "tone": "5",
                "completeness": "4",
                "overall_score": "4.5",
            },
            {
                "accuracy": "4",
                "reasoning": "3",
                "tone": "4",
                "completeness": "3",
                "overall_score": "3.7",
            },
        ]

        stats = generator.calculate_statistics(data)
        assert stats["total_evaluations"] == 2
        assert stats["mean_accuracy"] == 4.5
        assert stats["mean_reasoning"] == 3.5

    def test_calculate_statistics_invalid_values(self):
        """Test calculate_statistics handles invalid values gracefully."""
        generator = ReportGenerator()
        data = [
            {
                "accuracy": "invalid",
                "reasoning": "4",
                "tone": "5",
                "completeness": "4",
                "overall_score": "4.5",
            },
            {
                "accuracy": "5",
                "reasoning": "bad",
                "tone": "4",
                "completeness": "3",
                "overall_score": "3.7",
            },
        ]

        stats = generator.calculate_statistics(data)
        assert "total_evaluations" in stats

    def test_calculate_statistics_pandas_missing(self):
        """Test calculate_statistics returns empty dict when pandas is not available."""
        generator = ReportGenerator()
        with patch.dict(sys.modules, {"pandas": None}):
            stats = generator.calculate_statistics([{"overall_score": 4.5}])
            assert stats == {}

    def test_calculate_statistics_score_scaling(self):
        """Test score scaling from 0-1 to 0-5 for aggregated_score and score_* columns."""
        generator = ReportGenerator()
        data = [
            {
                "score_accuracy": "0.8",  # should scale to 4.0
                "score_reasoning": "0.6",  # should scale to 3.0
                "aggregated_score": "0.7",  # should scale to 3.5
                "overall_score": "3.5",  # should NOT scale (stays 3.5)
            }
        ]
        stats = generator.calculate_statistics(data)
        assert stats["mean_accuracy"] == pytest.approx(4.0)
        assert stats["mean_reasoning"] == pytest.approx(3.0)
        assert stats["mean_overall"] == pytest.approx(3.5)

    def test_calculate_statistics_all_nan(self):
        """Test calculate_statistics returns 0.0 when column values are all coerced to NaN."""
        generator = ReportGenerator()
        data = [{"score_accuracy": "invalid_val"}]
        stats = generator.calculate_statistics(data)
        assert stats["mean_accuracy"] == 0.0

    def test_calculate_statistics_get_mean_exception_handling(self):
        """Test calculate_statistics get_mean handles unexpected exceptions gracefully."""
        generator = ReportGenerator()
        data = [{"score_accuracy": "1.0"}]
        with patch("pandas.to_numeric", side_effect=Exception("Simulated to_numeric failure")):
            stats = generator.calculate_statistics(data)
            assert stats["mean_accuracy"] == 0.0

    def test_generate_accuracy_chart_success(self):
        """Test generate_accuracy_chart creates chart file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(tmpdir)
            data = [{"accuracy": "5"}, {"accuracy": "4"}, {"accuracy": "3"}]

            output_file = os.path.join(tmpdir, "accuracy.png")
            generator.generate_accuracy_chart(data, output_file)

            if HAS_MATPLOTLIB:
                assert os.path.exists(output_file)

    def test_generate_accuracy_chart_error_handling(self):
        """Test generate_accuracy_chart handles errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator()
            data = [{"accuracy": "invalid"}]
            output_file = os.path.join(tmpdir, "test.png")

            # Should not crash even with invalid data
            generator.generate_accuracy_chart(data, output_file)

    def test_generate_accuracy_chart_matplotlib_missing(self):
        """Test generate_accuracy_chart returns early when matplotlib is not available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator()
            output_file = os.path.join(tmpdir, "test.png")
            with patch.dict(sys.modules, {"matplotlib": None}):
                generator.generate_accuracy_chart([{"accuracy": 5}], output_file)

    def test_generate_accuracy_chart_fallback(self):
        """Test fallback from accuracy to score_accuracy and then to 0.0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(tmpdir)
            data = [
                {"accuracy": "4.5"},  # accuracy works -> 4.5
                {
                    "accuracy": "invalid",
                    "score_accuracy": "0.8",
                },  # fallback to score_accuracy * 5 -> 4.0
                {"accuracy": "invalid", "score_accuracy": "invalid"},  # fallback to 0.0
            ]
            output_file = os.path.join(tmpdir, "test_chart.png")
            generator.generate_accuracy_chart(data, output_file)
            if HAS_MATPLOTLIB:
                assert os.path.exists(output_file)

    def test_generate_defect_summary_no_defects(self):
        """Test generate_defect_summary with no defects."""
        generator = ReportGenerator()
        data = [{"defects": ""}, {"defects": ""}]

        summary = generator.generate_defect_summary(data)
        assert summary == {}

    def test_generate_defect_summary_with_defects(self):
        """Test generate_defect_summary with various defects."""
        generator = ReportGenerator()
        data = [
            {"defects": "D01,D02"},
            {"defects": "D01"},
            {"defects": "D03,D04,D05"},
            {"defects": ""},
        ]

        summary = generator.generate_defect_summary(data)
        assert summary["D01"] == 2
        assert summary["D02"] == 1
        assert summary["D03"] == 1
        assert summary["D04"] == 1
        assert summary["D05"] == 1

    def test_generate_defect_summary_list_format(self):
        """Test generate_defect_summary when defects is a list or tuple."""
        generator = ReportGenerator()
        data = [{"defects": ["D01", "D02"]}, {"defects": ("D01", "D03")}]
        summary = generator.generate_defect_summary(data)
        assert summary["D01"] == 2
        assert summary["D02"] == 1
        assert summary["D03"] == 1

    def test_generate_defect_summary_whitespace_handling(self):
        """Test generate_defect_summary handles whitespace."""
        generator = ReportGenerator()
        data = [{"defects": " D01 , D02 "}, {"defects": "D01"}]

        summary = generator.generate_defect_summary(data)
        assert summary["D01"] == 2
        assert summary["D02"] == 1

    def test_generate_html_report_creates_file(self):
        """Test generate_html_report creates HTML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(tmpdir)
            data = [
                {
                    "accuracy": "5",
                    "reasoning": "4",
                    "tone": "5",
                    "completeness": "4",
                    "overall_score": "4.5",
                }
            ]

            output_file = os.path.join(tmpdir, "report.html")
            generator.generate_html_report(data, output_file)

            assert os.path.exists(output_file)
            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()
                assert "<html>" in content
                assert "Evaluation Summary" in content

    def test_generate_html_report_contains_statistics(self):
        """Test generate_html_report includes statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(tmpdir)
            data = [
                {
                    "accuracy": "5",
                    "reasoning": "4",
                    "tone": "5",
                    "completeness": "4",
                    "overall_score": "4.5",
                },
                {
                    "accuracy": "4",
                    "reasoning": "3",
                    "tone": "4",
                    "completeness": "3",
                    "overall_score": "3.7",
                },
            ]

            output_file = os.path.join(tmpdir, "report.html")
            generator.generate_html_report(data, output_file)

            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()
                assert "Total Evaluations" in content
                assert "Mean Accuracy" in content

    def test_generate_html_report_plotly_missing(self):
        """Test generate_html_report falls back when plotly is not available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(tmpdir)
            with patch.dict(sys.modules, {"plotly": None, "plotly.express": None}):
                output_file = os.path.join(tmpdir, "report_no_plotly.html")
                generator.generate_html_report([{"overall_score": 4.5}], output_file)
                assert os.path.exists(output_file)

    def test_generate_html_report_prompt_handling_and_scaling(self):
        """Test prompt truncation, empty prompts, and score fallback/scaling in HTML report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(tmpdir)
            long_prompt = "A" * 150
            data = [
                {
                    "prompt_id": "p1",
                    "prompt_text": long_prompt,
                    "model": "test-model",
                    "overall_score": "invalid",  # triggers exception, falls back
                    "aggregated_score": "0.8",  # should be preferred and scaled to 4.0
                },
                {
                    "prompt_id": "p2",
                    "prompt": "",  # empty prompt
                    "model": "test-model",
                    "overall_score": "4.5",  # doesn't scale
                },
            ]
            output_file = os.path.join(tmpdir, "report.html")
            generator.generate_html_report(data, output_file)

            assert os.path.exists(output_file)
            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()
                expected_truncated = "A" * 100 + "..."
                assert expected_truncated in content
                assert "p2" in content
                assert "4.00" in content
                assert "4.50" in content

    def test_generate_html_report_no_score_columns(self):
        """Test generate_html_report when no score columns are in the input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(tmpdir)
            # score_col becomes None, and HTML should still generate with 0.00 scores
            data = [{"prompt_id": "p1", "model": "test-model"}]
            output_file = os.path.join(tmpdir, "report_no_scores.html")
            generator.generate_html_report(data, output_file)
            assert os.path.exists(output_file)
            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()
                assert "0.00" in content

    def test_generate_all_reports_creates_all_files(self):
        """Test generate_all_reports creates all report files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(tmpdir)
            data = [
                {
                    "accuracy": "5",
                    "reasoning": "4",
                    "tone": "5",
                    "completeness": "4",
                    "overall_score": "4.5",
                    "defects": "D01",
                },
                {
                    "accuracy": "4",
                    "reasoning": "3",
                    "tone": "4",
                    "completeness": "3",
                    "overall_score": "3.7",
                    "defects": "",
                },
            ]

            generator.generate_all_reports(data)

            if HAS_MATPLOTLIB:
                assert (Path(tmpdir) / "accuracy_trends.png").exists()
            assert (Path(tmpdir) / "defect_summary.csv").exists()
            assert (Path(tmpdir) / "evaluation_summary.html").exists()

    def test_generate_all_reports_with_custom_output_dir(self):
        """Test generate_all_reports with custom output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = os.path.join(tmpdir, "custom_reports")
            generator = ReportGenerator(tmpdir)
            data = [
                {
                    "accuracy": "5",
                    "reasoning": "4",
                    "tone": "5",
                    "completeness": "4",
                    "overall_score": "4.5",
                    "defects": "",
                }
            ]

            generator.generate_all_reports(data, output_dir=custom_dir)

            assert os.path.exists(custom_dir)
            assert (Path(custom_dir) / "defect_summary.csv").exists()

    def test_generate_all_reports_uses_self_output_dir(self):
        """Test generate_all_reports uses self.output_dir when no dir specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(tmpdir)
            data = [
                {
                    "accuracy": "5",
                    "reasoning": "4",
                    "tone": "5",
                    "completeness": "4",
                    "overall_score": "4.5",
                    "defects": "",
                }
            ]

            generator.generate_all_reports(data, output_dir=None)

            assert (Path(tmpdir) / "defect_summary.csv").exists()

    def test_generate_reports_legacy_method(self):
        """Test generate_reports (legacy method) with DataFrame."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(tmpdir)
            df = pd.DataFrame(
                {
                    "aggregated_score": [4.5, 3.7, 4.2],
                    "score_accuracy": [5, 4, 4],
                    "score_reasoning": [4, 3, 4],
                }
            )

            reports = generator.generate_reports(df)
            assert "executive_summary" in reports

    def test_generate_reports_legacy_empty_dataframe(self):
        """Test generate_reports with empty DataFrame."""
        generator = ReportGenerator()
        df = pd.DataFrame()

        reports = generator.generate_reports(df)
        assert reports == {}

    def test_generate_reports_with_none_data(self):
        """Test generate_reports handles None data gracefully."""
        generator = ReportGenerator()
        reports = generator.generate_reports(None)
        assert reports == {}

    def test_generate_reports_pandas_missing(self):
        """Test generate_reports returns empty dict when pandas is not available."""
        generator = ReportGenerator()
        with patch.dict(sys.modules, {"pandas": None}):
            reports = generator.generate_reports([{"overall_score": 4.5}])
            assert reports == {}

    @pytest.mark.asyncio
    async def test_generate_reports_async(self):
        """Test generate_reports_async asynchronously delegates to generate_reports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(tmpdir)
            data = [{"overall_score": 4.5}]
            reports = await generator.generate_reports_async(data)
            assert "executive_summary" in reports

    def test_generate_reports_exception_recovery(self):
        """Test exception recovery in generate_reports when sub-methods fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(tmpdir)
            data = [{"overall_score": "4.5"}]

            generator.generate_accuracy_chart = MagicMock(
                side_effect=Exception("Chart generation failed")
            )
            generator.generate_defect_summary = MagicMock(
                side_effect=Exception("Defect summary failed")
            )
            generator.generate_html_report = MagicMock(side_effect=Exception("HTML report failed"))
            generator._generate_executive_summary = MagicMock(
                side_effect=Exception("Executive summary failed")
            )

            reports = generator.generate_reports(data)
            assert reports == {}

    def test_generate_reports_partial_exception_recovery(self):
        """Test partial exception recovery in generate_reports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(tmpdir)
            data = [{"overall_score": "4.5", "defects": "D01"}]

            generator.generate_accuracy_chart = MagicMock(
                side_effect=Exception("Chart generation failed")
            )

            reports = generator.generate_reports(data)
            assert "accuracy_chart" not in reports
            assert "defect_summary" in reports
            assert "html_report" in reports
            assert "executive_summary" in reports

    def test_generate_executive_summary_exception_handling(self):
        """Test _generate_executive_summary recovers from general exceptions."""
        generator = ReportGenerator()

        class BadDataFrame:
            columns = ["overall_score"]

            def copy(self):
                raise ValueError("Simulated error during copy")

        res = generator._generate_executive_summary(BadDataFrame())
        assert res == generator.output_dir / "executive_summary.md"

    def test_generate_executive_summary_pandas_missing(self):
        """Test _generate_executive_summary recovers when pandas is missing."""
        df = pd.DataFrame({"overall_score": [4.5]})
        generator = ReportGenerator()
        with patch.dict(sys.modules, {"pandas": None}):
            res = generator._generate_executive_summary(df)
            assert res == generator.output_dir / "executive_summary.md"

    def test_generate_executive_summary_dimension_type_error(self):
        """Test _generate_executive_summary handles non-numeric dimension scores gracefully."""
        df = pd.DataFrame({"overall_score": [4.0, 4.2], "score_reasoning": [[1, 2], [3, 4]]})
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(tmpdir)
            generator._generate_executive_summary(df)
            with open(os.path.join(tmpdir, "executive_summary.json"), "r", encoding="utf-8") as f:
                data = json.load(f)
                assert "reasoning" not in data["dimension_averages"]

    def test_generate_executive_summary_variations(self):
        """Test _generate_executive_summary with different scores and column configurations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(tmpdir)

            # Case 1: both present (aggregated_score is preferred and scaled to 0-5)
            df1 = pd.DataFrame({"aggregated_score": [0.9, 0.8], "overall_score": [4.5, 4.0]})
            generator._generate_executive_summary(df1)
            with open(os.path.join(tmpdir, "executive_summary.md"), "r", encoding="utf-8") as f:
                content = f.read()
                assert "Average Score" in content
                assert "4.25/5.00" in content
                assert "✅ Good performance with room for improvement" in content

            # Case 2: only overall_score present, average >= 4.5, std_dev <= 1.0
            df2 = pd.DataFrame({"overall_score": [4.8, 4.6]})
            generator._generate_executive_summary(df2)
            with open(os.path.join(tmpdir, "executive_summary.md"), "r", encoding="utf-8") as f:
                content = f.read()
                assert "Average Score" in content
                assert "4.70/5.00" in content
                assert "✅ Excellent overall performance across all evaluations" in content

            # Case 3: only overall_score present, average >= 2.5 and < 3.5, std_dev > 1.0
            df3 = pd.DataFrame({"overall_score": [4.5, 1.5]})
            generator._generate_executive_summary(df3)
            with open(os.path.join(tmpdir, "executive_summary.md"), "r", encoding="utf-8") as f:
                content = f.read()
                assert "Average Score" in content
                assert "3.00/5.00" in content
                assert "⚠️ Acceptable performance but needs attention" in content
                assert "⚠️ High variance in scores indicates inconsistent performance" in content

            # Case 4: average < 2.5
            df4 = pd.DataFrame({"overall_score": [2.0, 1.8]})
            generator._generate_executive_summary(df4)
            with open(os.path.join(tmpdir, "executive_summary.md"), "r", encoding="utf-8") as f:
                content = f.read()
                assert "Average Score" in content
                assert "1.90/5.00" in content
                assert "❌ Performance below expectations, immediate action required" in content

            # Case 5: neither present
            df5 = pd.DataFrame({"other_column": [1.0, 2.0]})
            generator._generate_executive_summary(df5)

    def test_generate_executive_summary_custom_score_column_0_1_scaling(self):
        """Test _generate_executive_summary scaling with custom score column and avg <= 1.0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(tmpdir)
            df = pd.DataFrame(
                {"custom_score": [0.8, 0.6]}  # mean is 0.7 <= 1.0, should scale to 3.5
            )
            generator._generate_executive_summary(df)
            with open(os.path.join(tmpdir, "executive_summary.md"), "r", encoding="utf-8") as f:
                content = f.read()
                assert "3.50/5.00" in content

    def test_generate_executive_summary_empty_dataframe(self):
        """Test _generate_executive_summary with an empty DataFrame (no columns)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(tmpdir)
            df = pd.DataFrame()  # completely empty with no columns
            res = generator._generate_executive_summary(df)
            assert res == generator.output_dir / "executive_summary.md"

    def test_standalone_generate_reports_function(self):
        """Test standalone generate_reports function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data = [
                {
                    "accuracy": "5",
                    "reasoning": "4",
                    "tone": "5",
                    "completeness": "4",
                    "overall_score": "4.5",
                    "defects": "",
                }
            ]

            reports = generate_reports(data, output_dir=tmpdir)

            assert "accuracy_trends" in reports
            assert "defect_summary" in reports
            assert "evaluation_summary" in reports

    def test_standalone_generate_reports_default_dir(self):
        """Test standalone generate_reports with default directory."""
        data = [
            {
                "accuracy": "5",
                "reasoning": "4",
                "tone": "5",
                "completeness": "4",
                "overall_score": "4.5",
                "defects": "",
            }
        ]

        reports = generate_reports(data)
        assert isinstance(reports, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=evaluation.report_generator", "--cov-report=term-missing"])
