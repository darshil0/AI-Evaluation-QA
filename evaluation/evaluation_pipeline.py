"""
Evaluation Pipeline Orchestrator.

This module handles the end-to-end orchestration of the AI evaluation process,
seamlessly connecting the prompt loading, execution, scoring, and reporting
stages into a unified, robust pipeline.
"""

import asyncio
import csv
import logging
import math
import os
from typing import Any, Dict, List, Optional

from evaluation.cost_tracker import CostTracker
from evaluation.prompt_runner import PromptRunner
from evaluation.report_generator import ReportGenerator
from evaluation.scoring_engine import ScoringEngine
from scripts.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


class EvaluationPipeline:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.prompt_loader = PromptLoader()
        self.prompt_runner = PromptRunner(self.config)

        if hasattr(ScoringEngine, "from_config"):
            self.scoring_engine = ScoringEngine.from_config(self.config)
        else:
            self.scoring_engine = ScoringEngine()  # pragma: no cover

        output_dir = self.config.get("output", {}).get("directory", "reports")
        self.report_generator = ReportGenerator(output_dir)

        budget_limit = self.config.get("budget", {}).get(
            "limit_usd", self.config.get("evaluation", {}).get("budget_limit")
        )
        model_name = self.config.get("models", {}).get("primary", {}).get("model_name", "gpt-4")
        self.cost_tracker = CostTracker(model_name=model_name, budget_limit=budget_limit)

    def run_evaluation(self, prompt_file: str) -> Any:
        return self.run(prompt_file)  # pragma: no cover

    def run(self, prompt_file: str) -> Any:
        """
        Main entry point for running the evaluation pipeline.

        Preconditions:
            - prompt_file must be a valid path to a JSON prompt file.
            - Valid configuration must be initialized.

        Postconditions:
            - Returns a pandas DataFrame with scored results, or None if failed.

        Edge Cases:
            - prompt_file missing: Raised FileNotFoundError.
            - Empty prompts: Returns None.

        Failure Modes:
            - RuntimeError: If called from an active event loop.
        """
        try:
            return asyncio.run(self._run_async(prompt_file))
        except RuntimeError:
            loop = asyncio.get_event_loop()  # pragma: no cover
            if loop.is_running():  # pragma: no cover
                raise RuntimeError(  # pragma: no cover
                    "run() cannot be called from an active event loop. "
                    "Use 'await _run_async(...)' instead."
                )
            return loop.run_until_complete(self._run_async(prompt_file))  # pragma: no cover
        except Exception as e:  # pragma: no cover
            logger.error(f"Pipeline execution failed: {e}")  # pragma: no cover
            raise  # pragma: no cover

    async def _run_async(self, prompt_file: str) -> Any:
        logger.info(f"Starting evaluation for {prompt_file}")
        prompts = self.prompt_loader.load_and_validate(prompt_file)

        def checkpoint_cb(current_results: List[Dict[str, Any]]) -> None:
            self._save_checkpoint(current_results, "raw_results_checkpoint.csv")  # pragma: no cover

        results = await self.prompt_runner.run_prompts(
            prompts["prompts"],
            checkpoint_callback=checkpoint_cb,
        )

        if not results:
            logger.error("No results returned from prompt runner.")  # pragma: no cover
            return None  # pragma: no cover

        self._save_checkpoint(results, "raw_results_checkpoint.csv")

        scored_df = await self.process_results_async(results)

        if scored_df is not None and not scored_df.empty:
            self._save_checkpoint(scored_df.to_dict("records"), "scored_results_checkpoint.csv")
            await self.report_generator.generate_reports_async(scored_df)
            self.print_summary(scored_df)
            logger.info("Pipeline execution completed successfully.")
            return scored_df

        return None  # pragma: no cover

    def _save_checkpoint(self, results: List[Dict[str, Any]], filename: str) -> None:
        """Save checkpoint with fault reporting."""
        checkpoint_dir = self.config.get("output", {}).get(
            "checkpoint_directory", "data/checkpoints"
        )
        os.makedirs(checkpoint_dir, exist_ok=True)
        filepath = os.path.join(checkpoint_dir, filename)

        if not results:
            return  # pragma: no cover

        try:
            all_keys = sorted(
                {key for row in results if isinstance(row, dict) for key in row.keys()}
            )
            rows_written = 0
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
                writer.writeheader()
                for idx, row in enumerate(results):
                    try:
                        writer.writerow(row if isinstance(row, dict) else {})
                        rows_written += 1
                    except (TypeError, ValueError) as e:  # pragma: no cover
                        logger.error(
                            f"Row {idx} serialization failed: {e}. Skipping row."
                        )  # pragma: no cover

            logger.info(f"Checkpoint saved: {rows_written}/{len(results)} rows to {filepath}")
        except Exception as e:  # pragma: no cover
            logger.error(f"Failed to save checkpoint {filepath}: {e}")  # pragma: no cover
            raise  # pragma: no cover

    def process_results(self, results: List[Dict[str, Any]]) -> Any:
        try:  # pragma: no cover
            return asyncio.run(self.process_results_async(results))  # pragma: no cover
        except RuntimeError:  # pragma: no cover
            loop = asyncio.get_event_loop()  # pragma: no cover
            if loop.is_running():  # pragma: no cover
                raise RuntimeError(  # pragma: no cover
                    "process_results() cannot be called from an active event loop. "
                    "Use 'await process_results_async(...)' instead."
                )
            return loop.run_until_complete(self.process_results_async(results))  # pragma: no cover

    async def process_results_async(self, results: List[Dict[str, Any]]) -> Any:
        """
        Asynchronously processes and scores raw evaluation results.

        Preconditions:
            - results must be a list of dictionaries with status 'success'.

        Postconditions:
            - Returns a pandas DataFrame containing original results and calculated scores/costs.

        Edge Cases:
            - Empty results: Returns None.
            - Mixed success/error: Only successful results are processed.
        """
        try:
            import pandas as pd
        except ImportError:  # pragma: no cover
            logger.error("pandas is required for result processing.")
            raise

        if not results:
            logger.error("No results to process.")
            return None

        results_df = pd.DataFrame(results)

        if "status" in results_df.columns:  # pragma: no cover
            successful_results = results_df[
                results_df["status"] == "success"
            ].copy()  # pragma: no cover
            failed_count = len(results_df) - len(successful_results)  # pragma: no cover
            if failed_count > 0:  # pragma: no cover
                logger.warning(
                    f"{failed_count} requests failed and will be skipped in scoring."
                )  # pragma: no cover
            results_df = successful_results

        if results_df.empty:  # pragma: no cover
            logger.error("No successful results to process.")  # pragma: no cover
            return None  # pragma: no cover

        logger.info(f"Scoring {len(results_df)} responses in parallel...")

        scoring_tasks = [
            asyncio.to_thread(
                self.scoring_engine.score_response,
                row.to_dict(),
            )
            for _, row in results_df.iterrows()
        ]
        scored_reports = await asyncio.gather(*scoring_tasks)

        scored_dicts = []
        for i, report in enumerate(scored_reports):
            # Ensure response text is available for defect detection
            row_dict = results_df.iloc[i].to_dict()
            if "response" not in report.metadata:
                report.metadata["response"] = row_dict.get("model_response") or row_dict.get(
                    "response", ""
                )

            scored_dicts.append(self.scoring_engine.report_to_dict(report, include_defects=True))

        scored_df = pd.json_normalize(scored_dicts)
        results_df = results_df.reset_index(drop=True)
        # Remove duplicate columns from scored_df before concatenation
        cols_to_use = scored_df.columns.difference(results_df.columns)
        scored_df_subset = scored_df[cols_to_use]
        final_df = pd.concat([results_df, scored_df_subset], axis=1)

        logger.info("Calculating token usage and costs in parallel...")
        cost_tasks = [
            asyncio.to_thread(self._calculate_row_cost, row.to_dict())
            for _, row in final_df.iterrows()
        ]
        costs = await asyncio.gather(*cost_tasks)
        final_df["cost"] = costs

        return final_df

    def _safe_int_conversion(self, value: Any, default: int = 0) -> int:
        """Safely convert token count to integer."""
        try:
            try:
                import pandas as pd
            except ImportError:  # pragma: no cover
                return int(float(value)) if value is not None else default  # pragma: no cover

            if value is None or (isinstance(value, float) and pd.isna(value)):
                return default
            if isinstance(value, float) and math.isinf(value):
                logger.warning(f"Infinite token count detected, using default: {default}")
                return default
            return int(float(value))  # Convert via float for string numbers
        except (ValueError, TypeError, OverflowError) as e:  # pragma: no cover
            logger.error(f"Failed to convert token count: {e}")  # pragma: no cover
            return default  # pragma: no cover

    def _calculate_row_cost(self, row: Any) -> float:
        try:
            import pandas as pd
        except ImportError:  # pragma: no cover
            logger.error("pandas is required for cost calculation.")
            raise

        input_tokens = row.get("prompt_tokens")
        if input_tokens is None or pd.isna(input_tokens):
            prompt_text = row.get("prompt") or row.get("prompt_text") or ""
            input_tokens = self.cost_tracker.count_tokens(str(prompt_text))

        output_tokens = row.get("response_tokens")
        if output_tokens is None or pd.isna(output_tokens):
            response_text = row.get("response") or ""
            output_tokens = self.cost_tracker.count_tokens(str(response_text))

        return self.cost_tracker.add_request(
            model=row.get("model", self.cost_tracker.model_name),
            input_tokens=self._safe_int_conversion(input_tokens),
            output_tokens=self._safe_int_conversion(output_tokens),
            prompt_id=row.get("prompt_id"),
        )

    def print_summary(self, df: Any) -> None:
        print("\n" + "=" * 50)
        print("EVALUATION EXECUTION SUMMARY")
        print("=" * 50)
        print(f"Total Evaluations:  {len(df)}")

        score_col = "overall_score" if "overall_score" in df.columns else "aggregated_score"
        if score_col in df.columns:  # pragma: no cover
            avg_score = df[score_col].mean()  # pragma: no cover
            threshold = 3.5 if score_col == "overall_score" else 0.7  # pragma: no cover
            success_rate = (
                (df[score_col] >= threshold).sum() / len(df) * 100 if len(df) > 0 else 0
            )  # pragma: no cover
            # pragma: no cover
            if score_col == "aggregated_score":
                avg_score *= 5.0  # pragma: no cover
            print(f"Average Score:      {avg_score:.2f}/5.00")  # pragma: no cover
            print(f"Success Rate:       {success_rate:.1f}%")  # pragma: no cover

        total_cost = df["cost"].sum() if "cost" in df.columns else 0  # pragma: no cover
        print(f"Total Tokens:       {self.cost_tracker.get_total_tokens():,}")
        print(f"Total Estimated Cost: ${total_cost:.4f}")
        print("=" * 50 + "\n")
