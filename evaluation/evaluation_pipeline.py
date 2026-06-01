"""
Evaluation Pipeline Orchestrator.

This module handles the end-to-end orchestration of the AI evaluation process,
seamlessly connecting the prompt loading, execution, scoring, and reporting
stages into a unified, robust pipeline.
"""

import asyncio
import csv
import logging
import os
from typing import Optional, Dict, Any, List, Union

from evaluation.prompt_runner import PromptRunner
from evaluation.scoring_engine import ScoringEngine
from evaluation.report_generator import ReportGenerator
from scripts.prompt_loader import PromptLoader
from evaluation.cost_tracker import CostTracker

logger = logging.getLogger(__name__)


class EvaluationPipeline:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.prompt_loader = PromptLoader()
        self.prompt_runner = PromptRunner(self.config)

        if hasattr(ScoringEngine, "from_config"):
            self.scoring_engine = ScoringEngine.from_config(self.config)
        else:
            self.scoring_engine = ScoringEngine()

        output_dir = self.config.get("output", {}).get("directory", "reports")
        self.report_generator = ReportGenerator(output_dir)

        budget_limit = self.config.get("evaluation", {}).get("budget_limit")
        model_name = self.config.get("model", "gpt-4")
        self.cost_tracker = CostTracker(model_name=model_name, budget_limit=budget_limit)

    def run_evaluation(self, prompt_file: str) -> Any:
        return self.run(prompt_file)

    def run(self, prompt_file: str) -> Any:
        try:
            return asyncio.run(self._run_async(prompt_file))
        except RuntimeError:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                raise RuntimeError(
                    "run() cannot be called from an active event loop. Use 'await _run_async(...)' instead."
                )
            return loop.run_until_complete(self._run_async(prompt_file))
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            raise

    async def _run_async(self, prompt_file: str) -> Any:
        logger.info(f"Starting evaluation for {prompt_file}")
        prompts = self.prompt_loader.load_and_validate(prompt_file)

        def checkpoint_cb(current_results):
            self._save_checkpoint(current_results, "raw_results_checkpoint.csv")

        results = await self.prompt_runner.run_prompts(
            prompts["prompts"],
            checkpoint_callback=checkpoint_cb,
        )

        if not results:
            logger.error("No results returned from prompt runner.")
            return None

        self._save_checkpoint(results, "raw_results_checkpoint.csv")

        scored_df = await self.process_results_async(results)

        if scored_df is not None and not scored_df.empty:
            self._save_checkpoint(scored_df.to_dict("records"), "scored_results_checkpoint.csv")
            await self.report_generator.generate_reports_async(scored_df)
            self.print_summary(scored_df)
            logger.info("Pipeline execution completed successfully.")
            return scored_df

        return None

    def _save_checkpoint(self, results: List[Dict[str, Any]], filename: str) -> None:
        checkpoint_dir = self.config.get("output", {}).get(
            "checkpoint_directory", "data/checkpoints"
        )
        os.makedirs(checkpoint_dir, exist_ok=True)
        filepath = os.path.join(checkpoint_dir, filename)

        if not results:
            return

        try:
            all_keys = sorted(
                {key for row in results if isinstance(row, dict) for key in row.keys()}
            )
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
                writer.writeheader()
                for row in results:
                    writer.writerow(row if isinstance(row, dict) else {})
            logger.info(f"Checkpoint saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint {filepath}: {e}")

    def process_results(self, results: List[Dict[str, Any]]) -> Any:
        try:
            return asyncio.run(self.process_results_async(results))
        except RuntimeError:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                raise RuntimeError(
                    "process_results() cannot be called from an active event loop. Use 'await process_results_async(...)' instead."
                )
            return loop.run_until_complete(self.process_results_async(results))

    async def process_results_async(self, results: List[Dict[str, Any]]) -> Any:
        try:
            import pandas as pd
        except ImportError:
            logger.error("pandas is required for result processing.")
            raise

        if not results:
            logger.error("No results to process.")
            return None

        results_df = pd.DataFrame(results)

        if "status" in results_df.columns:
            successful_results = results_df[results_df["status"] == "success"].copy()
            failed_count = len(results_df) - len(successful_results)
            if failed_count > 0:
                logger.warning(f"{failed_count} requests failed and will be skipped in scoring.")
            results_df = successful_results

        if results_df.empty:
            logger.error("No successful results to process.")
            return None

        logger.info(f"Scoring {len(results_df)} responses in parallel...")

        scoring_tasks = [
            asyncio.to_thread(
                self.scoring_engine.score_response,
                row.to_dict(),
            )
            for _, row in results_df.iterrows()
        ]
        scored_outputs = await asyncio.gather(*scoring_tasks)

        scored_df = pd.json_normalize(scored_outputs)
        results_df = results_df.reset_index(drop=True)
        final_df = pd.concat([results_df, scored_df], axis=1)

        logger.info("Calculating token usage and costs in parallel...")
        cost_tasks = [
            asyncio.to_thread(self._calculate_row_cost, row) for _, row in final_df.iterrows()
        ]
        costs = await asyncio.gather(*cost_tasks)
        final_df["cost"] = costs

        return final_df

    def _calculate_row_cost(self, row: Any) -> float:
        try:
            import pandas as pd
        except ImportError:
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
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
            prompt_id=row.get("prompt_id"),
        )

    def print_summary(self, df: Any) -> None:
        print("\n" + "=" * 50)
        print("EVALUATION EXECUTION SUMMARY")
        print("=" * 50)
        print(f"Total Evaluations:  {len(df)}")

        score_col = "overall_score" if "overall_score" in df.columns else "aggregated_score"
        if score_col in df.columns:
            avg_score = df[score_col].mean()
            print(f"Average Score:      {avg_score:.2f}/5.00")

        total_cost = df["cost"].sum() if "cost" in df.columns else 0
        print(f"Total Tokens:       {self.cost_tracker.get_total_tokens():,}")
        print(f"Total Estimated Cost: ${total_cost:.4f}")
        print("=" * 50 + "\n")
