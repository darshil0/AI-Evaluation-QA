# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.0] - 2026-06-04

### Fixed
- **Deadlock Bug**: Fixed recursive `acquire()` call inside `async with self.lock` in `evaluation/rate_limiter.py` that would cause deadlocks.
- **Python Built-in Shadowing**: Renamed `format` parameter to `file_format` in `evaluation/prompt_runner.py`'s `save_responses()` to prevent shadowing Python's built-in.
- **Type Hints**: Fixed incorrect `Optional[callable]` hint to `Optional[Callable]` in `evaluation/prompt_runner.py`. Added type hints to `scripts/prompt_loader.py`.
- **Bare Except**: Fixed bare `except:` clause in `evaluation/report_generator.py`'s `calculate_statistics` method.
- **File Encodings**: Added explicit `encoding="utf-8"` to file open calls in `evaluation/report_generator.py` and `scripts/prompt_loader.py` to prevent platform-specific decode errors.
- **Unnecessary Import**: Removed spurious `asyncio` import inside a synchronous method in `evaluation/report_generator.py`.
- **Incomplete Execution Guard**: Fixed incomplete `main()` function in `config/prompt_validator.py` by adding `asyncio.run()` and a proper `if __name__ == "__main__":` guard.
- **Fragile Logging Config**: Removed fragile module-level `logging.basicConfig` guard in `config/config_loader.py` that checked child logger handlers but configured the root logger.
- **Missing Init Files**: Added missing `__init__.py` files to `config/`, `evaluation/clients/`, and `scripts/` directories to ensure proper Python package discovery.
- **Dependency Constraints**: Updated unrealistic, futuristic dependency versions for `numpy`, `pandas`, `jsonschema`, `scipy`, and `matplotlib` across `pyproject.toml`, `setup.py`, and `requirements.txt` to align with stable reality.

## [2.3.8-patch] - 2026-06-02

### Fixed
- **Critical: Dependency Version Conflicts** — Unified conflicting version specifications across `setup.py`, `pyproject.toml`, and `requirements.txt` that would cause installation failures. Standardized on stable versions: `openai>=1.60.0`, `plotly>=5.24.0`, `click>=8.1.0`, `matplotlib>=3.10.0`, `scipy>=1.14.0`, `python-dotenv>=1.0.0`, `aiohttp>=3.10.0`.
- **Critical: Package Discovery Mismatch** — Fixed `setup.py` inadvertently excluding `scripts/` package while `pyproject.toml` attempted to include it. This caused `from scripts.*` imports to fail after installation. Corrected `find_packages()` to include evaluation, config, and scripts packages.
- **Critical: Import Error Handling** — Added try-except blocks to all top-level imports in `main.py` to provide helpful error messages instead of silent crashes when packages are missing. Implemented proper ImportError logging with installation instructions.
- **Major: Documentation Links** — Fixed broken links in `README.md` that pointed to Google search instead of actual files (CONTRIBUTING.md, LICENSE). Updated to relative paths for proper GitHub rendering.
- **Code Quality: setup.py Style** — Replaced awkward `__import__("pathlib")` pattern with clean `from pathlib import Path` import for better maintainability.
- **Configuration: Coverage Config** — Added comprehensive `[tool.coverage.*]` configuration to `pyproject.toml` for proper test coverage exclusion and reporting.
- **Configuration: pyproject.toml Package Discovery** — Added explicit `[tool.setuptools]` section with correct package discovery rules matching setup.py.
- **Documentation: pytest Configuration** — Enhanced `[tool.pytest.ini_options]` with `--strict-markers` flag to catch typos in test markers.
- **Security: Bandit Configuration** — Added `[tool.bandit]` section to exclude tests directory from security scanning.
- **Consistency: All Dependency Specs** — Audit and unified all version specifications across three config files following QA best practices (Given/When/Then validation).
- **Validation: Pre-commit hooks support** — Enhanced `pyproject.toml` isort configuration with `skip_gitignore = true` to work correctly with pre-commit setup.

### Changed
- **Refactored**: `setup.py` now uses `find_packages()` with explicit excludes for cleaner, more maintainable package discovery.
- **Improved**: Error messages in `main.py` CLI now include explicit installation instructions (e.g., "Run: pip install -e . or pip install -e .[dev]").
- **Standardized**: All three configuration files (setup.py, pyproject.toml, requirements.txt) now reference identical dependency versions as source of truth.

### Added
- **Documentation**: New `FIXES_SUMMARY.md` with complete QA audit trail including:
  - 11 critical issues mapped to components
  - Given/When/Then validation format
  - Risk matrix and edge cases
  - Deployment checklist
  - Failure modes and mitigation strategies
  - Traceability matrix for all fixes

### Removed
- **Technical Debt**: Removed implicit package discovery ambiguity by making `scripts/` explicit in both setup.py and pyproject.toml.

---

## [2.3.8] - 2026-06-02

### Changed
- **Major Reorganization**: Completely overhauled the project structure. Core logic moved to `evaluation/`, configuration to `config/`, utility scripts to `scripts/`, and all tests to `tests/`.
- **CLI Consolidation**: Integrated all commands from `cli.py` into `main.py`, providing a single entry point `ai-eval`.
- **Dependency Update**: Updated all libraries to their latest stable versions for improved security and performance.
- **Documentation Overhaul**: Updated `README.md`, `CHANGELOG.md`, and `CONTRIBUTING.md` to reflect the new architecture and versioning.

## [2.3.7] - 2026-06-01

### Fixed
- **Evaluation Pipeline Return Type**: Removed redundant second argument passed to `score_response` inside `process_results_async`, ensuring it returns a dictionary rather than a `ScoreReport`. This resolves a mismatch with `pd.json_normalize` that caused pipeline execution failures.
- **DataFrame Trimming Edge Case**: Enhanced `DataValidator.clean_dataframe` to perform safe element-wise string stripping. This prevents actual `NaN` or `None` values from being serialized into string representations.
- **Unit Test Correctness**: Updated `test_audit_findings.py` to assert correct, fixed framework behaviors (proper normalization, correct Markdown JSON parsing, and last-number extraction) rather than checking for obsolete bugs, ensuring a green test suite.

## [2.3.6] - 2026-05-20

### Fixed
- **Scoring Engine Robustness**: Resolved critical bugs in `ScoringEngine` related to score normalization and greedy numeric extraction.
- **Markdown JSON Parsing**: Improved `ScoringEngine` to correctly extract JSON scores from Markdown code blocks.
- **Metric Naming Consistency**: Standardized metric keys (e.g., `accuracy`, `score_accuracy`) across the pipeline to ensure reliable reporting and test stability.
- **100% Test Coverage**: Achieved and enforced 100% test coverage across core modules.
- **Configuration Validation**: Fixed bug in `ConfigLoader` where `max_retries` error message regex was causing test failures.
- **Polymorphic Return Type**: Standardized `score_response` to handle both `ScoreReport` and dictionary returns based on input parameters while maintaining backward compatibility.

### Changed
- **Dependency Hardening**: Updated `requirements.txt` and `setup.py` to hardened v2.3.6 baseline with specific version pins for security and stability.
- **Improved Logging**: Refined logging in `EvaluationPipeline` and `PromptRunner` for better observability during batch runs.

## [2.3.5] - 2026-05-20

### Added
- **Fault-Tolerant Checkpointing**: Implemented a robust checkpointing system in `EvaluationPipeline` that saves raw results to `data/checkpoints/` in real-time as requests complete.
- **XSS Protection**: Enhanced `ReportGenerator` with HTML escaping for all user-controlled data to prevent cross-site scripting vulnerabilities in generated dashboards.

### Fixed
- **Dependency Management**: Updated `setup.py` and `requirements.txt` to resolve potential version conflicts.
- **Reporting Reliability**: Fixed edge cases in `ReportGenerator` where malformed response data could cause dashboard generation failures.

## [2.3.4] - 2026-05-19

### Added
- **Validation Framework**: Introduced `ConfigurationValidator` and `PromptValidator` for comprehensive pre-execution checks.
- **Schema Enforcement**: Added strict JSON schema validation for prompt files to ensure data integrity.
- **Semantic Analysis**: Implemented semantic checks in `PromptValidator` to detect duplicate prompt IDs and insufficient text length.
- **Robust Error Handling**: Introduced `EvaluationErrorHandler` with configurable exponential backoff and retry logic for API requests.
- **Environment Validation**: Added proactive checking of required environment variables and configuration files.

## [2.3.3] - 2026-05-13

### Added
- **Benchmark Suite**: Introduced a new benchmark suite in `scripts/benchmarks/` to measure CLI startup time, scoring throughput, and token caching efficiency.
- **Asynchronous Reporting**: Introduced `generate_reports_async` in `ReportGenerator` using `asyncio.to_thread` to offload blocking file I/O and chart rendering.

### Changed
- **Performance Optimization**: Optimized CLI startup performance (target <300ms) by implementing lazy imports for heavy dependencies such as `pandas`, `matplotlib`, and `tiktoken`.
- **Scoring Engine Enhancements**: Enhanced `ScoringEngine` performance by using pre-compiled regular expressions for heuristic rules and keyword matching.
- **Cost Tracking Efficiency**: Improved `CostTracker` efficiency by applying `functools.lru_cache` to tokenization methods to prevent redundant processing.
- **Reporting Standards**: Standardized executive summary Markdown formatting in `ReportGenerator` to use bold keys for metrics (e.g., `**Total Evaluations:** 5`).

## [2.3.2] - 2026-05-09

### Added
- **Azure Provider Support**: Added Azure OpenAI support to `ConfigLoader` and `PromptRunner`.
- **Security Scans**: Integrated Trivy, TruffleHog, and Safety into the CI pipeline.
- **Logging Configuration**: Centralized logging setup in `main.py` with file persistence to `evaluation.log`.
- **Sanity Check Target**: New `test-run` Makefile target for basic framework verification in Docker environments.

### Changed
- **CLI Robustness**: Improved all CLI command error handling with proper logging and exit codes.
- **Docker Build Process**: Enhanced multi-stage Dockerfile with better error handling for optional source directories and removed silent `|| true` suppressions.
- **Makefile Targets**: Standardized all Make targets with `.PHONY` declarations.
- **Validation Workflow**: Made prompt validation more resilient with directory existence checks.
- **Test Coverage Policy**: Adjusted repository test coverage failure threshold to 100% across all configuration files (`Makefile`, `pytest.ini`, `setup.cfg`).
- **Execution Model**: Integrated `asyncio` event loop into `EvaluationPipeline` for concurrent API request handling.

### Fixed
- **CLI Command Registration**: Fixed missing `@cli.command()` decorators on `score` and `report` functions in `main.py`.
- **Parameter Naming**: Renamed `dir` parameter to `output_dir` in `report()` function to avoid shadowing a Python built-in.
- **Data Validation**: Fixed whitespace stripping and exception handling in `DataValidator.clean_dataframe` to safely handle all string-like columns.
- **API Key Handling**: Improved `PromptRunner.execute_prompt` to prioritize configuration-based API keys and validate variables like `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`.
- **Test Suite & Mocks**: Fixed multiple test failures by adding mock API keys, correcting call count assertions, modernizing OpenAI client mocking, and restoring `print()` statements for summaries to fix broken `sys.stdout` assertions.
- **Dependencies**: Resolved version conflicts in `requirements.txt` and added missing packages (`aiohttp`, `jsonschema`, `scipy`, `isort`, `bandit`, `safety`, `pre-commit`).
- **Dockerfile & Makefile Errors**: Corrected entrypoint commands, fixed `.env.example` referencing, added coverage report opening logic fallbacks, and synchronized version tags.
- **Configuration Migration**: Migrated scoring rules from `scoring.dimensions` to `scoring.criteria` in `config_loader.py` with backward compatibility for legacy schemas.
- **Polymorphic Methods**: Updated `ScoringEngine.save_scores` to support polymorphic signatures for backward compatibility with legacy tests.
- **Module Imports**: Fixed `data_validator.py` path by moving it to the `scripts/` directory and corrected top-level type hint imports (`Optional`, `Union`).
- **Package Initialization**: Added missing `__init__.py` files to `evaluation/` and `config/` while explicitly updating package discovery in `setup.py`.
- **Code Observability**: Replaced hardcoded `print()` statements in core pipeline files with the standard `logging` framework.

### Removed
- **Legacy Files**: Cleaned up root-level legacy files including `prompt_runner.py`, redundant patch files, and duplicate test scripts to consolidate logic in `evaluation/`.

## [2.3.1] - 2026-05-09

### Added
- **Security & Build Reliability**: Introduced `.dockerignore` to secure Docker builds and prevent sensitive file leakage.
- **Code Quality Guardrails**: Added `.pre-commit-config.yaml` to automatically enforce formatting (Black, isort) and linting (Flake8) before commits.
- **Strict Typing**: Extended type hinting to the `main.py` CLI interface and core pipeline methods for robust static analysis support.

### Fixed
- **CI/CD Stabilization**: Upgraded all GitHub Actions (`checkout`, `setup-python`, `upload-artifact`, `codecov-action`, `github-script`) to versions v4/v5 across all workflows to resolve Node.js 16 deprecation failures.

## [2.3.0] - 2026-05-09

### Added
- **Contributing Guide**: Added `CONTRIBUTING.md` with detailed instructions for environment setup, testing standards, and PR protocols.
- **Modernized Ecosystem**: Updated `requirements.txt`, `setup.py`, and `pyproject.toml` with 2026-standard library versions.
- **New Dependencies**: Integrated `plotly`, `click`, `tiktoken`, and `python-dotenv` into the core framework.
- **CI/CD Integration**: Migrated and optimized GitHub Actions workflows into `.github/workflows/`.
- **Docker Support**: Added `Dockerfile` with multi-stage builds for containerized deployment and reproducible environments.
- **Developer Tools**: Added `Makefile` with standardized targets for testing, linting, formatting, and Docker execution.

### Changed
- **Major Reorganization**: Complete structural overhaul moving all components into `evaluation/`, `tests/`, `config/`, `data/`, and `scripts/` directories.
- **Documentation Streamlining**: Consolidated 45+ redundant documents into a single, high-performance `README.md`.
- **Package Standards**: Formally upgraded development status to "Production/Stable" in project metadata.

### Fixed
- **Workspace Cleanup**: Removed all malformed and redundant root-level scripts and test files.
- **API Consistency**: Synchronized all internal paths and CLI entry points with the new directory structure.

## [2.2.2] - 2026-05-09

### Added
- **Command Line Interface (CLI)**: Upgraded `main.py` with specialized subcommands: `evaluate`, `score`, and `report`.
- **Execution Telemetry**: Added console-based execution summaries in `EvaluationPipeline` showing scores, tokens, and costs.
- **Standalone Scoring**: New capability to score existing CSV result files without re-running the API pipeline.

### Changed
- **Pipeline Modularity**: Refactored `EvaluationPipeline` to separate execution, scoring, and reporting logic for greater flexibility.
- **Improved Logging**: Centralized logging configuration in the CLI entry point with file-based persistence.

### Fixed
- **API Aliasing**: Ensured `run_evaluation` is properly aliased for consistency with documentation.
- **Telemetry Inconsistencies**: Fixed token counting mismatches in the cost tracker.

## [2.2.1] - 2026-05-09

### Added
- **Token Estimation**: Added automatic token estimation in `EvaluationPipeline` for accurate cost tracking when API usage metrics are unavailable.
- **Robust Statistics**: Enhanced `ReportGenerator` to handle both legacy and modern column names (`accuracy` vs `score_accuracy`) in statistical calculations.
- **Improved Logging**: Added more detailed logging throughout the execution pipeline for better observability.

### Changed
- **OpenAI API v1+ Upgrade**: Migrated `PromptRunner` to the modern OpenAI client library (v1.0.0+), replacing deprecated `ChatCompletion` calls.
- **API Stabilization**: Unified `ScoringEngine` and `ReportGenerator` interfaces to handle both structured DataFrames and raw List[Dict] formats consistently.
- **Scoring Consistency**: Standardized `ScoringEngine` to always provide both normalized (0-1) and scaled (1-5) scores to ensure compatibility with different reporting modules.

### Fixed
- **ScoringEngine Initialization**: Fixed a critical bug where `ScoringEngine` would fail if initialized without a custom rubric; added a default heuristic-based fallback.
- **Retry Logic**: Corrected the retry mechanism in `PromptRunner` to properly use exponential backoff and track attempts accurately.
- **Test Suite Mocks**: Fixed broken mocks in `test_evaluation_pipeline.py` that were causing failures after the OpenAI API upgrade.
- **Reporting Errors**: Resolved potential crashes in `ReportGenerator` when processing empty datasets or missing dimension columns.

## [2.2.0] - 2025-12-15

### Added
- **100% Code Coverage**: Achieved 100% test coverage across all core modules.
- **Extended Test Suite**: Added 75+ new tests covering edge cases, boundary conditions, and error paths.
- **Coverage Documentation**: Added `COVERAGE_100_GUIDE.md` and `COVERAGE_SUMMARY.md`.

## [2.1.0] - 2025-12-05

### Added
- **Synchronous Execution**: Added `execute_prompt()` and `execute_prompts()` for direct, non-async usage.
- **Batch Processing**: Implemented `score_batch()` for efficient large-scale evaluation.
- **Stand-alone API**: Exposed top-level functions `score_responses()` and `generate_reports()`.
- **API Documentation**: Added `API_REFERENCE.md` and `FIXES_SUMMARY.md`.

## [2.0.0] - 2025-11-20

### Changed
- **Modular Refactor**: Complete codebase reorganization with proper separation of concerns.
- **Type Safety**: Added type hints throughout the entire framework.
- **Enhanced Logic**: Improved heuristics for accuracy and reasoning dimensions.
- **Improved Analytics**: Upgraded Matplotlib/Plotly visualizations for professional reports.

## [1.0.0] - 2025-10-15

### Added
- Initial production release with core pipeline functionality.

[2.4.0]: https://github.com/darshil0/AI-Evaluation-QA/compare/v2.3.8-patch...v2.4.0
[2.3.8-patch]: https://github.com/darshil0/AI-Evaluation-QA/compare/v2.3.8...v2.3.8-patch
[2.3.8]: https://github.com/darshil0/AI-Evaluation-QA/compare/v2.3.7...v2.3.8
[2.3.7]: https://github.com/darshil0/AI-Evaluation-QA/compare/v2.3.6...v2.3.7
[2.3.6]: https://github.com/darshil0/AI-Evaluation-QA/compare/v2.3.5...v2.3.6
[2.3.5]: https://github.com/darshil0/AI-Evaluation-QA/compare/v2.3.4...v2.3.5
[2.3.4]: https://github.com/darshil0/AI-Evaluation-QA/compare/v2.3.3...v2.3.4
[2.3.3]: https://github.com/darshil0/AI-Evaluation-QA/compare/v2.3.2...v2.3.3
[2.3.2]: https://github.com/darshil0/AI-Evaluation-QA/compare/v2.3.1...v2.3.2
[2.3.1]: https://github.com/darshil0/AI-Evaluation-QA/compare/v2.3.0...v2.3.1
[2.3.0]: https://github.com/darshil0/AI-Evaluation-QA/compare/v2.2.2...v2.3.0
[2.2.2]: https://github.com/darshil0/AI-Evaluation-QA/compare/v2.2.1...v2.2.2
[2.2.1]: https://github.com/darshil0/AI-Evaluation-QA/compare/v2.2.0...v2.2.1
[2.2.0]: https://github.com/darshil0/AI-Evaluation-QA/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/darshil0/AI-Evaluation-QA/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/darshil0/AI-Evaluation-QA/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/darshil0/AI-Evaluation-QA/releases/tag/v1.0.0
