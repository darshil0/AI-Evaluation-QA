#!/usr/bin/env python3
"""Wrapper script for running evaluation."""
import os
from main import cli

if __name__ == "__main__":
    # Force default log file to logs/evaluation.log if not set
    if "EVAL_LOG_FILE" not in os.environ:
        os.environ["EVAL_LOG_FILE"] = "logs/evaluation.log"
    cli()
