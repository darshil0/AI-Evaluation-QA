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
            logger.error(f"Failed to load data: File not found at {filepath}")
            raise
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

        def get_mean(col_names):
            for col in col_names:
                if col in df.columns:
                    try:
                        return pd.to_numeric(df[col], errors="coerce").mean()
                    except:
                        continue
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
        defect_counts = {}

        for item in data:
            defects_str = item.get("defects", "")
            if defects_str:
                defects = defects_str.split(",")
                for defect in defects:
                    defect = defect.strip()
                    if defect:
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

            table_rows += f"<tr><td>{p_id}</td><td>{p_text}</td><td>{model}</td><td>{score}</td><td>{defects}</td></tr>"

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
        import asyncio

        return await asyncio.to_thread(self.generate_reports, data)

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

        reports = {}

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
        except Exception as e:
            logger.error(f"Failed to generate accuracy chart: {e}")

        # Generate defect summary
        try:
            defect_summary = self.generate_defect_summary(scored_responses)
            defect_file = self.output_dir / "defect_summary.csv"
            with open(defect_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Defect Code", "Count"])
                for defect, count in defect_summary.items():
                    writer.writerow([defect, count])
            reports["defect_summary"] = str(defect_file)
        except Exception as e:
            logger.error(f"Failed to generate defect summary: {e}")

        # Generate HTML report
        try:
            html_file = self.output_dir / "evaluation_summary.html"
            self.generate_html_report(scored_responses, str(html_file))
            reports["html_report"] = str(html_file)
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")

        # Generate executive summary (text-based)
        try:
            summary_path = self._generate_executive_summary(df)
            reports["executive_summary"] = str(summary_path)
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")

        return reports

    def _generate_executive_summary(self, df: Any) -> Path:
        """Generate executive summary in Markdown"""
        import pandas as pd

        try:
            score_col = "aggregated_score" if "aggregated_score" in df.columns else "overall_score"
            summary = {
                "total_evaluations": len(df),
                "average_score": df[score_col].mean(),
                "median_score": df[score_col].median(),
                "std_dev": df[score_col].std(),
                "success_rate": (df[score_col] >= 3.5).sum() / len(df) * 100 if len(df) > 0 else 0,
            }
        except Exception as e:
            logger.warning(f"Could not generate executive summary: {e}")
            return self.output_dir / "executive_summary.md"

        # Dimension averages
        dimension_avgs = {}
        for col in df.columns:
            if col.startswith("score_"):
                try:
                    dim_name = col.replace("score_", "")
                    dimension_avgs[dim_name] = df[col].mean()
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
            markdown += f"- **{dim.title()}:** {avg:.2f}/5.00\n"

        markdown += f"\n## Key Insights\n"

        # Add insights
        if summary["average_score"] >= 4.5:
            markdown += "- ✅ Excellent overall performance across all evaluations\n"
        elif summary["average_score"] >= 3.5:
            markdown += "- ✅ Good performance with room for improvement\n"
        elif summary["average_score"] >= 2.5:
            markdown += "- ⚠️ Acceptable performance but needs attention\n"
        else:
            markdown += "- ❌ Performance below expectations, immediate action required\n"

        # Check for high variance
        if summary["std_dev"] > 1.0:
            markdown += "- ⚠️ High variance in scores indicates inconsistent performance\n"

        # Write to file
        md_path = self.output_dir / "executive_summary.md"
        with open(md_path, "w") as f:
            f.write(markdown)

        # Also write JSON version
        summary["dimension_averages"] = dimension_avgs
        json_path = self.output_dir / "executive_summary.json"
        with open(json_path, "w") as f:
            json.dump(summary, f, indent=2, default=float)

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

    print(f"\n✅ Reports generated successfully!")
    print(f"📊 Dashboard: {reports.get('dashboard')}")
    print(f"📈 Executive Summary: {reports.get('executive_summary')}")
    print(f"\nAll reports saved to: {output_dir}")
