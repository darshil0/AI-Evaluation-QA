#!/usr/bin/env python3
"""Verify AI-Evaluation-QA setup and configuration."""

import os
import sys
from pathlib import Path
from typing import Any, Callable


def verify_setup() -> bool:
    """Run all verification checks."""
    checks: dict[str, Callable[[], Any]] = {
        "Config file exists": lambda: Path("config/settings.yaml").exists(),
        "Required directories": lambda: all(
            Path(d).exists() for d in ["data/prompts", "reports", "evaluation"]
        ),
        "Python version": lambda: sys.version_info >= (3, 9),
        "API key set": lambda: bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")),
    }

    print("🔍 Running setup verification...\n")
    all_passed = True

    for check_name, check_func in checks.items():
        try:
            passed = check_func()
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}")
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name}: {str(e)}")
            all_passed = False

    print(f"\n{'✅ Setup verified!' if all_passed else '❌ Setup has issues'}")
    return all_passed


if __name__ == "__main__":
    success = verify_setup()
    sys.exit(0 if success else 1)
