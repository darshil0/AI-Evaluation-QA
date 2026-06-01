"""
AI Evaluation QA Framework - Main CLI Entrypoint.

This module provides the primary command-line interface (CLI) for executing,
scoring, and reporting on AI evaluations. It uses the Click library to expose
commands for full pipeline execution or independent sub-stages.

Usage:
    ai-eval evaluate --prompts <file>
    ai-eval score --results <file> --output <file>
    ai-eval report --results <file> --dir <dir>
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import click

from config.config_loader import ConfigLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("evaluation.log")],
)

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="2.3.8")
def cli() -> None:
    """AI Evaluation QA Framework CLI."""
    pass


@cli.command()
@click.option("--config", default="config/settings.yaml", help="Path to config file")
@click.option("--prompts", required=True, help="Path to prompts JSON file")
@click.option("--model", default=None, help="Model to use (overrides config)")
def evaluate(config: str, prompts: str, model: Optional[str]) -> None:
    """Run the full evaluation pipeline (Execute -> Score -> Report)."""
    from evaluation.evaluation_pipeline import EvaluationPipeline

    try:
        logger.info(f"Starting evaluation with prompts from {prompts}")
        conf = ConfigLoader.load(config) if os.path.exists(config) else {}
        
        if model:
            if "models" not in conf:
                conf["models"] = {"primary": {}}
            if "primary" not in conf["models"]:
                conf["models"]["primary"] = {}
            conf["models"]["primary"]["model_name"] = model
            logger.info(f"Using model override: {model}")

        pipeline = EvaluationPipeline(conf)
        pipeline.run(prompts)
        logger.info("Evaluation completed successfully")
    except FileNotFoundError as e:
        click.echo(f"Error: File not found - {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--config", default="config/settings.yaml", help="Path to config file")
@click.option("--results", required=True, help="Path to raw results CSV file")
@click.option("--output", default="scored_results.csv", help="Output path for scored results")
def score(config: str, results: str, output: str) -> None:
    """Score existing raw results from a CSV file."""
    import pandas as pd

    from evaluation.evaluation_pipeline import EvaluationPipeline

    try:
        logger.info(f"Scoring results from {results}")
        if not os.path.exists(results):
            raise FileNotFoundError(f"Results file not found: {results}")

        conf = ConfigLoader.load(config) if os.path.exists(config) else {}
        pipeline = EvaluationPipeline(conf)

        df = pd.read_csv(results)
        results_list = df.to_dict("records")
        scored_df = pipeline.process_results(results_list)

        if scored_df is not None:
            scored_df.to_csv(output, index=False)
            click.echo(f"Scored results saved to {output}")
            logger.info(f"Results scored and saved to {output}")
            pipeline.print_summary(scored_df)
        else:
            logger.warning("No results to score")
            click.echo("Warning: No results to score", err=True)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except pd.errors.ParserError as e:
        click.echo(f"Error: Failed to parse CSV file - {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Scoring failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--results", required=True, help="Path to scored results CSV file")
@click.option("--output-dir", default="reports", help="Output directory for reports")
def report(results: str, output_dir: str) -> None:
    """Generate reports from scored results."""
    import pandas as pd

    try:
        logger.info(f"Generating reports from {results} to {output_dir}")
        if not os.path.exists(results):
            raise FileNotFoundError(f"Results file not found: {results}")

        from evaluation.report_generator import ReportGenerator

        df = pd.read_csv(results)

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        generator = ReportGenerator(output_dir)
        generator.generate_reports(df)
        click.echo(f"Reports generated in {output_dir}/")
        logger.info(f"Reports successfully generated in {output_dir}/")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except pd.errors.ParserError as e:
        click.echo(f"Error: Failed to parse CSV file - {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("current_results", type=click.Path(exists=True))
@click.option("--baseline", default="reports/baseline.csv", help="Baseline file")
@click.option("--save-baseline", is_flag=True, help="Save current as new baseline")
def check_regression(current_results: str, baseline: str, save_baseline: bool) -> None:
    """Check for performance regressions."""
    import pandas as pd
    from scripts.check_regression import RegressionDetector

    try:
        current_df = pd.read_csv(current_results)
        detector = RegressionDetector(baseline)
        results = detector.check_regression(current_df)

        report_text = detector.generate_regression_report(results)
        click.echo(report_text)

        if save_baseline:
            detector.save_as_baseline(current_df)
            logger.info(f"Saved as new baseline: {baseline}")

        if results.get("has_regression"):
            sys.exit(1)
    except Exception as e:
        logger.error(f"Regression check failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--config", default="config/settings.yaml", help="Path to config file")
def validate(config: str) -> None:
    """Validate configuration and setup."""
    issues = []

    # Check config file
    try:
        ConfigLoader.load(config)
        logger.info("Configuration valid")
    except Exception as e:
        issues.append(f"Configuration error: {str(e)}")

    # Check directories
    required_dirs = ["data/prompts", "reports"]
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            issues.append(f"Missing directory: {dir_path}")
        else:
            logger.info(f"Directory exists: {dir_path}")

    # Check environment variables
    import os
    required_env = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
    env_found = any(os.getenv(env_var) for env_var in required_env)

    if not env_found:
        issues.append(f"Missing at least one API key from: {required_env}")
    else:
        logger.info("API key found in environment")

    if issues:
        click.echo("Validation failed:", err=True)
        for issue in issues:
            click.echo(f"  - {issue}", err=True)
        sys.exit(1)
    else:
        click.echo("All validations passed!")


@cli.command()
@click.argument("prompt_file", type=click.Path(exists=True))
def lint_prompts(prompt_file: str) -> None:
    """Validate and lint prompt file."""
    from scripts.prompt_loader import PromptLoader

    try:
        loader = PromptLoader()
        prompts_data = loader.load_and_validate(prompt_file)

        click.echo("Prompt file is valid")
        click.echo(f"Found {len(prompts_data.get('prompts', []))} prompts")

        # Additional semantic checks could be added here
    except Exception as e:
        logger.error(f"Linting failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
