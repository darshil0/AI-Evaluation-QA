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
        data: List[Dict[str, Any]] = []
        filepath_p = Path(filepath)
        if not filepath_p.exists():
            logger.error(f"Failed to load data: File not found at {filepath}")  # pragma: no cover
            raise FileNotFoundError(filepath)  # pragma: no cover

        try:
            with filepath_p.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
        except Exception as e:
            logger.error(f"Error loading data from {filepath}: {e}")
            return []
        return data

    def calculate_statistics(self, scored_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            import pandas as pd
        except Exception:
            logger.error("pandas is required for calculate_statistics")
            return {}

        if not scored_responses:
            return {}

        df = pd.DataFrame(scored_responses)

        def get_mean(col_names: List[str]) -> float:
            for col in col_names:
                if col in df.columns:
                    try:
                        mean_val = pd.to_numeric(df[col], errors="coerce").mean()
                        # If it's a 0-1 scale metric (like aggregated_score or score_*),
                        # scale it to 5.0 when appropriate
                        if col == "aggregated_score" or col.startswith("score_"):
                            if pd.notna(mean_val):
                                mean_val = float(mean_val) * 5.0
                        return float(mean_val) if pd.notna(mean_val) else 0.0
                    except Exception:
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
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except Exception as e:
            logger.error(f"matplotlib not available, cannot generate chart: {e}")
            return

        scores: List[float] = []
        for r in scored_responses:
            try:
                scores.append(float(r.get("accuracy", 0)))
            except Exception:
                try:
                    # fallback: try score_accuracy scaled
                    scores.append(float(r.get("score_accuracy", 0)) * 5.0)
                except Exception:
                    scores.append(0.0)

        plt.figure(figsize=(10, 6))
        plt.hist(scores, bins=5, edgecolor="black", alpha=0.7)
        plt.xlabel("Accuracy Score")
        plt.ylabel("Frequency")
        plt.title("Accuracy Score Distribution")
        plt.grid(True, alpha=0.3)
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_file, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"Accuracy chart saved to {output_file}")

    def generate_defect_summary(self, data: List[Dict[str, Any]]) -> Dict[str, int]:
        defect_counts: Dict[str, int] = {}

        for item in data:
            defects_str = item.get("defects", "")
            if not defects_str:
                continue
            # Accept list-like or comma-separated string
            if isinstance(defects_str, (list, tuple)):
                defects = [str(d).strip() for d in defects_str if d]
            else:
                defects = [d.strip() for d in str(defects_str).split(",") if d.strip()]
            for defect in defects:
                defect_counts[defect] = defect_counts.get(defect, 0) + 1

        return defect_counts

    def generate_html_report(
        self, scored_responses: List[Dict[str, Any]], output_file: str
    ) -> None:
        stats = self.calculate_statistics(scored_responses)

        plotly_html = ""
        try:
            import pandas as pd
            import plotly.express as px

            df = pd.DataFrame(scored_responses)
            score_col = (
                "overall_score"
                if "overall_score" in df.columns
                else ("aggregated_score" if "aggregated_score" in df.columns else None)
            )
            if score_col is not None and not df[score_col].dropna().empty:
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

        table_rows = ""
        display_results = scored_responses[:100]

        for res in display_results:
            p_id = html.escape(str(res.get("prompt_id", "")))
            prompt_raw = res.get("prompt_text") or res.get("prompt") or ""
            p_text = html.escape(str(prompt_raw))[:100]
            if len(str(prompt_raw)) > 100:
                p_text = p_text + "..."
            model = html.escape(str(res.get("model", "")))
            # try multiple score columns for compatibility
            score_val = 0.0
            for sc in ("overall_score", "aggregated_score", "score_overall"):
                if sc in res and res[sc] not in (None, ""):
                    try:
                        score_val = float(res.get(sc, 0))
                        # scale if necessary (if it's 0-1 aggregated)
                        if sc.startswith("score_") or sc == "aggregated_score":
                            score_val = score_val * 5.0 if score_val <= 1.0 else score_val
                        break
                    except Exception:
                        continue
            score = f"{score_val:.2f}"
            defects = html.escape(str(res.get("defects", "")))

            table_rows += (
                f"<tr><td>{p_id}</td><td>{p_text}</td><td>{model}</td>"
                f"<td>{score}</td><td>{defects}</td></tr>"
            )

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
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

        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"HTML report saved to {output_file}")

    def generate_all_reports(
        self, scored_responses: List[Dict[str, Any]], output_dir: Optional[str] = None
    ) -> None:
        report_dir = Path(output_dir) if output_dir else self.output_dir
        report_dir.mkdir(parents=True, exist_ok=True)

        accuracy_file = report_dir / "accuracy_trends.png"
        self.generate_accuracy_chart(scored_responses, str(accuracy_file))

        defect_summary = self.generate_defect_summary(scored_responses)
        defect_file = report_dir / "defect_summary.csv"
        with open(defect_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Defect Code", "Count"])
            for defect, count in defect_summary.items():
                writer.writerow([defect, count])

        html_file = report_dir / "evaluation_summary.html"
        self.generate_html_report(scored_responses, str(html_file))

        logger.info("All reports generated in %s", str(report_dir))

    async def generate_reports_async(self, data: Any) -> Dict[str, str]:
        # fixed: call the synchronous generate_reports (not missing name)
        return await asyncio.to_thread(self.generate_reports, data)

    def generate_reports(self, data: Any) -> Dict[str, str]:
        try:
            import pandas as pd
        except Exception:
            logger.error("pandas is required for report generation")
            return {}

        if isinstance(data, pd.DataFrame):
            scored_responses = data.to_dict("records")
            df = data
        else:
            scored_responses = data or []
            df = pd.DataFrame(scored_responses)

        reports: Dict[str, str] = {}

        if df.empty:
            logger.error("Cannot generate reports from empty data")
            return reports

        self.output_dir.mkdir(parents=True, exist_ok=True)

        try:
            accuracy_file = self.output_dir / "accuracy_trends.png"
            self.generate_accuracy_chart(scored_responses, str(accuracy_file))
            reports["accuracy_chart"] = str(accuracy_file)
        except Exception as e:
            logger.error(f"Failed to generate accuracy chart: {e}")

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

        try:
            html_file = self.output_dir / "evaluation_summary.html"
            self.generate_html_report(scored_responses, str(html_file))
            reports["html_report"] = str(html_file)
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")

        try:
            summary_path = self._generate_executive_summary(df)
            reports["executive_summary"] = str(summary_path)
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")

        return reports

    def _generate_executive_summary(self, df: Any) -> Path:
        score_col = (
            "aggregated_score"
            if "aggregated_score" in df.columns
            else (
                "overall_score"
                if "overall_score" in df.columns
                else (df.columns[0] if len(df.columns) > 0 else "overall_score")
            )
        )
        # Ensure numeric
        try:
            import pandas as pd

            df_numeric = df.copy()
            if score_col in df_numeric.columns:
                df_numeric[score_col] = pd.to_numeric(df_numeric[score_col], errors="coerce")
            avg_score = df_numeric[score_col].mean() if score_col in df_numeric.columns else 0.0
            median_score = (
                df_numeric[score_col].median() if score_col in df_numeric.columns else 0.0
            )
            std_dev = df_numeric[score_col].std() if score_col in df_numeric.columns else 0.0

            # Determine scaling and threshold
            is_0_1_scale = False
            if score_col == "aggregated_score":
                is_0_1_scale = True
            elif score_col == "overall_score":
                is_0_1_scale = False
            elif avg_score is not None and avg_score <= 1.0:
                is_0_1_scale = True

            threshold = 0.7 if is_0_1_scale else 3.5

            success_rate = (
                (df_numeric[score_col] >= threshold).sum() / len(df_numeric) * 100
                if len(df_numeric) > 0
                else 0
            )

            if is_0_1_scale:
                avg_score = float(avg_score * 5.0) if avg_score is not None else 0.0
                median_score = float(median_score * 5.0) if median_score is not None else 0.0
                std_dev = float(std_dev * 5.0) if std_dev is not None else 0.0
        except Exception as e:
            logger.warning(f"Could not generate executive summary: {e}")
            return self.output_dir / "executive_summary.md"

        summary = {
            "total_evaluations": len(df),
            "average_score": float(avg_score),
            "median_score": float(median_score),
            "std_dev": float(std_dev),
            "success_rate": float(success_rate),
        }

        dimension_avgs: Dict[str, float] = {}
        for col in df.columns:
            if col.startswith("score_"):
                try:
                    dimension_avgs[col.replace("score_", "")] = float(df[col].astype(float).mean())
                except Exception:
                    logger.warning(f"Could not calculate average for dimension {col}")

        markdown = f"""# Executive Summary

## Overview
- **Total Evaluations:** {summary['total_evaluations']}
- **Average Score:** {summary['average_score']:.2f}/5.00
- **Median Score:** {summary['median_score']:.2f}/5.00
- **Standard Deviation:** {summary['std_dev']:.2f}
- **Success Rate (threshold):** {summary['success_rate']:.1f}%

"""

        markdown += "\n## Dimension Performance\n"
        for dim, avg in sorted(dimension_avgs.items(), key=lambda x: x[1], reverse=True):
            display_avg = avg * 5.0 if avg <= 1.0 else avg
            markdown += f"- **{dim.title()}:** {display_avg:.2f}/5.00\n"

        markdown += "\n## Key Insights\n"

        if summary["average_score"] >= 4.5:
            markdown += "- ✅ Excellent overall performance across all evaluations\n"
        elif summary["average_score"] >= 3.5:
            markdown += "- ✅ Good performance with room for improvement\n"
        elif summary["average_score"] >= 2.5:
            markdown += "- ⚠️ Acceptable performance but needs attention\n"
        else:
            markdown += "- ❌ Performance below expectations, immediate action required\n"

        if summary["std_dev"] > 1.0:
            markdown += "- ⚠️ High variance in scores indicates inconsistent performance\n"

        md_path = self.output_dir / "executive_summary.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)

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
    generator = ReportGenerator(output_dir)
    generator.generate_all_reports(scored_responses, output_dir)
    return {
        "accuracy_trends": str(Path(output_dir) / "accuracy_trends.png"),
        "defect_summary": str(Path(output_dir) / "defect_summary.csv"),
        "evaluation_summary": str(Path(output_dir) / "evaluation_summary.html"),
        "executive_summary": str(Path(output_dir) / "executive_summary.md"),
    }


if __name__ == "__main__":
    import sys
    from datetime import datetime

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        # optional dependency
        pass

    if len(sys.argv) < 2:
        print("Usage: python report_generator.py <scored_results_file>")
        sys.exit(1)

    scored_file = sys.argv[1]
    try:
        import pandas as pd
    except Exception:
        logger.error("pandas is required to run as a CLI")
        raise SystemExit(1)

    df = pd.read_csv(scored_file)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"reports/report_{timestamp}"

    generator = ReportGenerator(output_dir)
    reports = generator.generate_reports(df)

    print("\n✅ Reports generated successfully!")
    print(f"📊 Accuracy chart: {reports.get('accuracy_trends')}")
    print(f"📈 Executive Summary: {reports.get('executive_summary')}")
    print(f"\nAll reports saved to: {output_dir}")
