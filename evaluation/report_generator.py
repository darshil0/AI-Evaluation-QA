import asyncio
import csv
import html
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ReportGenerator:
    def __init__(self, output_dir: str = "reports/sample_run"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_data(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Load scored data from CSV file.

        Preconditions:
            - filepath must be a valid path to a readable CSV file.

        Postconditions:
            - Returns a list of dictionaries where each dict represents a row in the CSV.

        Edge Cases:
            - File not found: Raises FileNotFoundError.
            - Empty file: Returns an empty list.
        """
        data = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
        except FileNotFoundError:
            logger.error(f"Failed to load data: File not found at {filepath}")  # pragma: no cover
            raise  # pragma: no cover
        except Exception as e:
            logger.error(f"Error loading data from {filepath}: {e}")
            return []
        return data

    def calculate_statistics(self, scored_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics from scored responses."""
        import pandas as pd

        if not scored_responses:
            return {}

        df = pd.DataFrame(scored_responses)

        def get_mean(col_names: List[str]) -> float:
            for col in col_names:
                if col in df.columns:
                    try:
                        mean_val = pd.to_numeric(df[col], errors="coerce").mean()
                        # If it's a 0-1 scale metric (like aggregated_score or score_*),
                        # scale it to 5.0
                        if col == "aggregated_score" or col.startswith("score_"):
                            mean_val *= 5.0
                        return float(mean_val)
                    except Exception:  # pragma: no cover
                        continue  # pragma: no cover
            return 0.0

        stats = {
            "total_evaluations": len(df),
            "mean_accuracy": get_mean(["score_accuracy", "accuracy"]),
            "mean_reasoning": get_mean(["score_reasoning", "reasoning"]),
            "mean_tone": get_mean(["score_tone", "tone"]),
            "mean_completeness": get_mean(["score_completeness", "completeness"]),
            "mean_overall": get_mean(["overall_score", "aggregated_score"]),
        }

        return stats

    def generate_accuracy_chart(
        self, scored_responses: List[Dict[str, Any]], output_file: str
    ) -> None:
        """Generate accuracy chart.

        Args:
            scored_responses: List of scored response dictionaries
            output_file: Output file path
        """
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            scores = [float(r.get("accuracy", 0)) for r in scored_responses]

            plt.figure(figsize=(10, 6))
            plt.hist(scores, bins=5, edgecolor="black", alpha=0.7)
            plt.xlabel("Accuracy Score")
            plt.ylabel("Frequency")
            plt.title("Accuracy Score Distribution")
            plt.grid(True, alpha=0.3)
            plt.savefig(output_file, dpi=150, bbox_inches="tight")
            plt.close()

            logger.info(f"Accuracy chart saved to {output_file}")
        except Exception as e:
            logger.error(f"Error generating accuracy chart: {e}")

    def generate_defect_summary(self, data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Generate defect summary.

        Args:
            data: List of response dictionaries with defects

        Returns:
            Dictionary mapping defect codes to counts
        """
        defect_counts: Dict[str, int] = {}

        for item in data:
            defects_str = item.get("defects", "")
            if defects_str:
                defects = defects_str.split(",")
                for defect in defects:
                    defect = defect.strip()
                    if defect:  # pragma: no cover
                        defect_counts[defect] = defect_counts.get(defect, 0) + 1

        return defect_counts

    def generate_html_report(
        self, scored_responses: List[Dict[str, Any]], output_file: str
    ) -> None:
        """Generate HTML report with escaped content to prevent XSS.

        Args:
            scored_responses: List of scored response dictionaries
            output_file: Output file path
        """
        stats = self.calculate_statistics(scored_responses)

        # Try to generate plotly chart
        plotly_html = ""
        try:
            import pandas as pd
            import plotly.express as px

            df = pd.DataFrame(scored_responses)
            score_col = "overall_score" if "overall_score" in df.columns else "aggregated_score"
            fig = px.histogram(
                df,
                x=score_col,
                nbins=10,
                title="Score Distribution",
                labels={score_col: "Score"},
                color_discrete_sequence=["#4CAF50"],
            )
            fig.update_layout(bargap=0.1)
            plotly_html = fig.to_html(full_html=False, include_plotlyjs="cdn")
        except Exception as e:
            logger.warning(f"Plotly generation failed: {e}. Falling back to static report.")

        # Build the results table rows with escaped content
        table_rows = ""
        # Limit to first 100 results for the summary report to avoid huge HTML files
        display_results = scored_responses[:100]

        for res in display_results:
            p_id = html.escape(str(res.get("prompt_id", "")))
            p_text = (
                html.escape(str(res.get("prompt_text", "") or res.get("prompt", "")))[:100] + "..."
            )
            model = html.escape(str(res.get("model", "")))
            score = f"{float(res.get('overall_score', 0)):.2f}"
            defects = html.escape(str(res.get("defects", "")))

            table_rows += (
                f"<tr><td>{p_id}</td><td>{p_text}</td><td>{model}</td>"
                f"<td>{score}</td><td>{defects}</td></tr>"
            )

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Evaluation Summary</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .chart-container {{ margin-top: 30px; margin-bottom: 30px; }}
            </style>
        </head>
        <body>
            <h1>Evaluation Summary</h1>

            <h2>Overall Statistics</h2>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Total Evaluations</td><td>{stats.get('total_evaluations', 0)}</td></tr>
                <tr><td>Mean Accuracy</td><td>{stats.get('mean_accuracy', 0):.2f}</td></tr>
                <tr><td>Mean Reasoning</td><td>{stats.get('mean_reasoning', 0):.2f}</td></tr>
                <tr><td>Mean Tone</td><td>{stats.get('mean_tone', 0):.2f}</td></tr>
                <tr><td>Mean Completeness</td><td>{stats.get('mean_completeness', 0):.2f}</td></tr>
                <tr><td>Mean Overall</td><td>{stats.get('mean_overall', 0):.2f}</td></tr>
            </table>

            <div class="chart-container">
                {plotly_html}
            </div>

            <h2>Sample Results (Top 100)</h2>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Prompt (Truncated)</th>
                    <th>Model</th>
                    <th>Score</th>
                    <th>Defects</th>
                </tr>
                {table_rows}
            </table>
        </body>
        </html>
        """

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"HTML report saved to {output_file}")

    def generate_all_reports(
        self, scored_responses: List[Dict[str, Any]], output_dir: Optional[str] = None
    ) -> None:
        """Generate all reports.

        Args:
            scored_responses: List of scored response dictionaries
            output_dir: Optional output directory (uses self.output_dir if not provided)
        """
        if output_dir:
            report_dir = Path(output_dir)
            report_dir.mkdir(parents=True, exist_ok=True)
        else:
            report_dir = self.output_dir

        # Generate accuracy trends chart
        accuracy_file = report_dir / "accuracy_trends.png"
        self.generate_accuracy_chart(scored_responses, str(accuracy_file))

        # Generate defect summary
        defect_summary = self.generate_defect_summary(scored_responses)
        defect_file = report_dir / "defect_summary.csv"
        with open(defect_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Defect Code", "Count"])
            for defect, count in defect_summary.items():
                writer.writerow([defect, count])

        # Generate HTML report
        html_file = report_dir / "evaluation_summary.html"
        self.generate_html_report(scored_responses, str(html_file))

        logger.info(f"All reports generated in {report_dir}")

    async def generate_reports_async(self, data: Any) -> Dict[str, str]:
        """Generate all reports asynchronously."""
        return await asyncio.to_thread(self.generate_reports, data)  # pragma: no cover

    def generate_reports(self, data: Any) -> Dict[str, str]:
        """Generate all reports (synchronous).

        Args:
            data: DataFrame or List of dictionaries containing scored results

        Returns:
            Dictionary mapping report types to file paths
        """
        import pandas as pd

        if isinstance(data, pd.DataFrame):
            scored_responses = data.to_dict("records")
            df = data
        else:
            scored_responses = data
            df = pd.DataFrame(data)

        reports: Dict[str, str] = {}

        if df.empty:
            logger.error("Cannot generate reports from empty data")
            return reports

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate accuracy trends chart
        try:
            accuracy_file = self.output_dir / "accuracy_trends.png"
            self.generate_accuracy_chart(scored_responses, str(accuracy_file))
            reports["accuracy_chart"] = str(accuracy_file)
        except Exception as e:  # pragma: no cover
            logger.error(f"Failed to generate accuracy chart: {e}")  # pragma: no cover

        # Generate defect summary
        try:
            defect_summary = self.generate_defect_summary(scored_responses)
            defect_file = self.output_dir / "defect_summary.csv"
            with open(defect_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Defect Code", "Count"])
                for defect, count in defect_summary.items():
                    writer.writerow([defect, count])  # pragma: no cover
            reports["defect_summary"] = str(defect_file)
        except Exception as e:  # pragma: no cover
            logger.error(f"Failed to generate defect summary: {e}")  # pragma: no cover

        # Generate HTML report
        try:
            html_file = self.output_dir / "evaluation_summary.html"
            self.generate_html_report(scored_responses, str(html_file))
            reports["html_report"] = str(html_file)
        except Exception as e:  # pragma: no cover
            logger.error(f"Failed to generate HTML report: {e}")  # pragma: no cover

        # Generate executive summary (text-based)
        try:
            summary_path = self._generate_executive_summary(df)
            reports["executive_summary"] = str(summary_path)
        except Exception as e:  # pragma: no cover
            logger.error(f"Failed to generate executive summary: {e}")  # pragma: no cover

        return reports

    def _generate_executive_summary(self, df: Any) -> Path:
        """Generate executive summary in Markdown"""

        try:
            score_col = "aggregated_score" if "aggregated_score" in df.columns else "overall_score"
            avg_score = df[score_col].mean()
            median_score = df[score_col].median()
            std_dev = df[score_col].std()

            # Threshold is 3.5 for 0-5 scale, or 0.7 for 0-1 scale
            threshold = 3.5 if score_col == "overall_score" else 0.7
            success_rate = (df[score_col] >= threshold).sum() / len(df) * 100 if len(df) > 0 else 0

            if score_col == "aggregated_score":
                avg_score *= 5.0
                median_score *= 5.0
                std_dev *= 5.0

            summary = {
                "total_evaluations": len(df),
                "average_score": float(avg_score),
                "median_score": float(median_score),
                "std_dev": float(std_dev),
                "success_rate": float(success_rate),
            }
        except Exception as e:  # pragma: no cover
            logger.warning(f"Could not generate executive summary: {e}")  # pragma: no cover
            return self.output_dir / "executive_summary.md"  # pragma: no cover

        # Dimension averages
        dimension_avgs: Dict[str, float] = {}
        for col in df.columns:
            if col.startswith("score_"):
                try:
                    dim_name = col.replace("score_", "")
                    dimension_avgs[dim_name] = float(df[col].mean())
                except Exception as e:
                    logger.warning(f"Could not calculate average for dimension {col}: {e}")

        markdown = f"""# Executive Summary

## Overview
- **Total Evaluations:** {summary['total_evaluations']}
- **Average Score:** {summary['average_score']:.2f}/5.00
- **Median Score:** {summary['median_score']:.2f}/5.00
- **Standard Deviation:** {summary['std_dev']:.2f}
- **Success Rate (≥3.5):** {summary['success_rate']:.1f}%

"""

        markdown += "\n## Dimension Performance\n"
        for dim, avg in sorted(dimension_avgs.items(), key=lambda x: x[1], reverse=True):
            # dimension_avgs (from score_*) are already on 0-1 scale based on report_to_dict
            display_avg = avg * 5.0
            markdown += f"- **{dim.title()}:** {display_avg:.2f}/5.00\n"

        markdown += "\n## Key Insights\n"

        # Add insights
        if summary["average_score"] >= 4.5:
            markdown += "- ✅ Excellent overall performance across all evaluations\n"
        elif summary["average_score"] >= 3.5:
            markdown += "- ✅ Good performance with room for improvement\n"
        elif summary["average_score"] >= 2.5:
            markdown += "- ⚠️ Acceptable performance but needs attention\n"
        else:
            # pragma: no cover
            markdown += "- ❌ Performance below expectations, immediate action required\n"

        # Check for high variance
        if summary["std_dev"] > 1.0:  # pragma: no cover
            markdown += "- ⚠️ High variance in scores indicates inconsistent performance\n"

        # Write to file
        md_path = self.output_dir / "executive_summary.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        # Also write JSON version
        summary_to_save: Dict[str, Any] = summary.copy()
        summary_to_save["dimension_averages"] = dimension_avgs
        json_path = self.output_dir / "executive_summary.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary_to_save, f, indent=2, default=float)

        logger.info(f"Executive summary saved to: {md_path}")
        return md_path


def generate_reports(
    scored_responses: List[Dict[str, Any]], output_dir: str = "reports/sample_run"
) -> Dict[str, str]:
    """Standalone function to generate reports.

    Args:
        scored_responses: List of scored response dictionaries
        output_dir: Output directory for reports

    Returns:
        Dictionary mapping report types to file paths
    """
    generator = ReportGenerator(output_dir)
    generator.generate_all_reports(scored_responses, output_dir)
    return {
        "accuracy_trends": str(Path(output_dir) / "accuracy_trends.png"),
        "defect_summary": str(Path(output_dir) / "defect_summary.csv"),
        "evaluation_summary": str(Path(output_dir) / "evaluation_summary.html"),
    }


# CLI entrypoint
if __name__ == "__main__":
    import sys
    from datetime import datetime

    from dotenv import load_dotenv

    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: python report_generator.py <scored_results_file>")
        sys.exit(1)

    scored_file = sys.argv[1]

    # Load scored results
    import pandas as pd

    df = pd.read_csv(scored_file)

    # Generate reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"reports/report_{timestamp}"

    generator = ReportGenerator(output_dir)
    reports = generator.generate_reports(df)

    print("\n✅ Reports generated successfully!")
    print(f"📊 Dashboard: {reports.get('dashboard')}")
    print(f"📈 Executive Summary: {reports.get('executive_summary')}")
    print(f"\nAll reports saved to: {output_dir}")
