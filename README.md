# AI Evaluation QA Framework

<p align="center">
  <img src="https://img.shields.io/badge/version-2.5.1-green.svg" alt="Version Badge">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License Badge">
  <img src="https://img.shields.io/badge/coverage-100%25-brightgreen.svg" alt="Test Coverage Badge">
  <img src="https://img.shields.io/badge/python-3.14-blue.svg" alt="Python Version Badge">
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/contributing-welcome-orange.svg" alt="Contributing Badge"></a>
</p>

## Overview

The **AI Evaluation QA Framework** is a production-grade Python library for evaluating, scoring, and comparing AI model responses at scale. It provides a robust pipeline to run structured prompt suites against major LLM providers (OpenAI, Anthropic, Azure OpenAI), score them using customizable rubrics, and generate professional dashboards with analytics and cost telemetry.

**Framework Version**: 2.5.1 (2026-06-28) | **Python**: 3.14 | **License**: MIT

## Key Features

- 🚀 **Multi-Provider Support**: Seamlessly evaluate against OpenAI (GPT-4, GPT-3.5), Anthropic (Claude Opus, Sonnet, Haiku), and Azure OpenAI.
- ⚖️ **Rubric-Based Scoring**: Score responses across Accuracy, Reasoning, Tone, and Completeness dimensions on a 1–5 scale.
- 🔍 **Automated Defect Detection**: Built-in detection for hallucinations (factual inconsistencies), logical flaws (reasoning gaps), redundancy (repetitive content), tone issues (inappropriate voice), and incomplete responses (insufficient coverage).
- 📊 **Rich Analytics & Dashboards**: Interactive HTML dashboards, executive summaries, trend analysis, and CSV exports with filtering and sorting.
- 💰 **Cost Telemetry**: Precision token counting via `tiktoken` and estimated cost tracking per model and run (updated pricing: June 2026).
- 🛡️ **Security & Validation**: Input/output sanitization (XSS prevention via `html.escape()`), filename safety controls (directory traversal prevention), and comprehensive pre-execution checks.
- 🔄 **Fault-Tolerant & Resumable**: Mid-batch checkpointing (every 50 requests by default) ensures no progress is lost on failure.
- ⚡ **Asynchronous & Fast**: Built with `asyncio` for high-concurrency API requests (tested up to 50 concurrent requests).
- 🐳 **Docker & CI/CD Ready**: Includes multi-stage `Dockerfile`, GitHub Actions workflows (test, lint, security), and automated testing pipelines.

## Requirements

- **Python**: 3.14
- **API Keys**: At least one of the following:
  - OpenAI API key (`OPENAI_API_KEY`) — [Get key](https://platform.openai.com/account/api-keys)
  - Anthropic API key (`ANTHROPIC_API_KEY`) — [Get key](https://console.anthropic.com/)
  - Azure OpenAI credentials (`AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`) — [Setup guide](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/)
- **Docker** (optional): For containerized execution. Install via [docker.com](https://docs.docker.com/get-docker/)

## Documentation

| Document | Purpose |
|----------|---------|
| [Contributing Guide](CONTRIBUTING.md) | Development setup, testing standards, PR guidelines, and code style (PEP 8, mypy strict, 100% coverage target) |
| [Changelog & Release History](CHANGELOG.md) | Version history, fixes, and breaking changes (v2.4.5 current, v1.0.0 initial) |
| [Configuration Reference](#configuration) | Detailed settings, rubric definition, and environment variables |
| [Troubleshooting Guide](#troubleshooting) | Solutions for common errors and edge cases |

## Installation

### Standard Installation

```bash
# Clone the repository
git clone https://github.com/darshil0/AI-Evaluation-QA.git
cd AI-Evaluation-QA

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install base dependencies
pip install -e .

# For development (includes testing, linting, type-checking, pre-commit hooks)
pip install -e .[dev]

# Verify installation
ai-eval validate
```

**Installation Time**: ~2 minutes (base), ~5 minutes (dev)
**Disk Space**: ~250MB (base), ~450MB (dev with dependencies)

### Docker Installation

```bash
# Build the Docker image
docker build -t ai-eval:latest .

# Create .env file with your API keys
echo "OPENAI_API_KEY=sk-..." > .env
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env

# Run the container with environment variables
docker run --rm \
  --env-file .env \
  -v $(pwd)/results:/app/results \
  ai-eval:latest \
  ai-eval validate

# Full evaluation example with volume mount
docker run --rm \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  ai-eval:latest \
  ai-eval evaluate --prompts /app/data/prompts/reasoning_tests.json \
                   --model claude-opus-4-7
```

**Container Image Size**: ~400MB | **Build Time**: ~3 minutes
**Note**: Volume mounts required to persist results outside container. Use `docker-compose.yml` for persistent state.

## Quick Start (5 Minutes)

### Step 1: Create Environment File

```bash
# Create .env file in project root
cat > .env << EOF
# Required: At least one provider
OPENAI_API_KEY='sk-proj-...'
# ANTHROPIC_API_KEY='sk-ant-...'
# AZURE_OPENAI_API_KEY='...'
# AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'

# Optional: Configuration
LOG_LEVEL='INFO'
OUTPUT_DIR='./results'
CONCURRENT_REQUESTS='10'
MAX_RETRIES='3'
EOF

# Verify .env file exists and is readable
ls -la .env
```

### Step 2: Validate Setup

```bash
# This command validates:
# ✓ Python version (3.14+)
# ✓ API key availability and connectivity
# ✓ Configuration file format
# ✓ Directory permissions for results output
ai-eval validate

# Expected output:
# [2026-06-21 10:23:45] INFO     Validating environment...
# [2026-06-21 10:23:47] INFO     ✓ OpenAI API key is valid
# [2026-06-21 10:23:48] INFO     ✓ Configuration file valid
# [2026-06-21 10:23:48] INFO     ✓ Ready to evaluate
```

**Expected Duration**: 5-10 seconds

### Step 3: Prepare Prompt File

Create a JSON file with test cases (e.g., `data/prompts/reasoning_tests.json`):

```json
[
  {
    "id": "logic_001",
    "category": "reasoning",
    "prompt": "If all mammals breathe air and whales are mammals, do whales breathe air? Explain your reasoning.",
    "expected_answer": "Yes, whales are mammals and all mammals breathe air, so whales breathe air.",
    "weight": 1.0
  },
  {
    "id": "hallucination_001",
    "category": "factual_accuracy",
    "prompt": "Who is the current CEO of OpenAI (as of June 2026)?",
    "expected_answer": "Sam Altman is the CEO of OpenAI.",
    "weight": 1.0
  },
  {
    "id": "tone_001",
    "category": "tone",
    "prompt": "Respond to this customer complaint: 'Your product broke after 2 weeks and customer service was unhelpful.'",
    "expected_tone": "empathetic, professional, solution-focused",
    "weight": 0.8
  }
]
```

**Validation**: Run `ai-eval lint-prompts data/prompts/reasoning_tests.json` to verify schema compliance.

### Step 4: Run Evaluation

```bash
# Dry run first (no API calls, validates pipeline)
ai-eval evaluate --prompts data/prompts/reasoning_tests.json \
                 --model gpt-4-turbo \
                 --dry-run

# Run full evaluation
ai-eval evaluate --prompts data/prompts/reasoning_tests.json \
                 --model gpt-4-turbo \
                 --output-dir ./results

# Run with Anthropic model instead
ai-eval evaluate --prompts data/prompts/reasoning_tests.json \
                 --model claude-opus-4-7 \
                 --output-dir ./results
```

**Expected Duration**:
- 10 prompts: ~30 seconds (with API calls)
- 100 prompts: ~4 minutes
- 1000 prompts: ~35 minutes (batched across concurrent workers)

**Expected Output**:
```
[2026-06-21 10:25:15] INFO     Starting evaluation pipeline...
[2026-06-21 10:25:20] INFO     ✓ Loaded 3 prompts
[2026-06-21 10:25:35] INFO     ✓ Executed 3 prompts (3/3 succeeded, 0 failed)
[2026-06-21 10:25:45] INFO     ✓ Scored responses: accuracy=3.8/5, reasoning=4.1/5
[2026-06-21 10:25:50] INFO     ✓ Generated reports in ./results
[2026-06-21 10:25:50] INFO     Total tokens: 1,234 prompt + 567 completion
[2026-06-21 10:25:50] INFO     Estimated cost: $0.04 (OpenAI gpt-4-turbo)
```

### Step 5: View Reports

Open the generated HTML reports in your browser:

```bash
# Executive summary with key metrics
open results/executive_summary.html

# Interactive dashboard with filtering
open results/detailed_dashboard.html

# CSV files for further analysis
cat results/scored_results.csv
```

## CLI Reference

| Command | Purpose | Example | Exit Code |
|---------|---------|---------|-----------|
| `evaluate` | Full pipeline: validate, execute, score, report | `ai-eval evaluate --prompts tests.json --model gpt-4-turbo` | 0 (success), 1 (failure) |
| `score` | Score raw results from previous run without re-executing | `ai-eval score --results raw_results.csv --output scored.csv` | 0, 1 |
| `report` | Generate HTML dashboards and summaries from scored results | `ai-eval report --results scored.csv --output-dir ./reports` | 0, 1 |
| `check-regression` | Compare current results against baseline, detect performance regressions | `ai-eval check-regression current.csv --baseline baseline.csv` | 0 (no regression), 1 (regression detected) |
| `validate` | Validate environment setup, API keys, configuration, and directory permissions | `ai-eval validate` | 0 (valid), 1 (invalid) |
| `lint-prompts` | Validate prompt JSON file structure, schema compliance, and content quality | `ai-eval lint-prompts prompts.json` | 0 (valid), 1 (invalid) |

### Global Options

```bash
ai-eval [COMMAND] [OPTIONS]

Options:
  --log-level {DEBUG,INFO,WARNING,ERROR}  # Logging verbosity (default: INFO)
  --config PATH                            # Path to custom config file (default: config/settings.yaml)
  --output-dir PATH                        # Output directory for results (default: ./results)
  --dry-run                                # Simulate run without making API calls
  --help                                   # Show help message
  --version                                # Show version (2.4.5)
```

### Example Command Sequences

```bash
# Scenario 1: Complete workflow with GPT-4
ai-eval validate && \
ai-eval evaluate --prompts data/prompts/test.json --model gpt-4-turbo

# Scenario 2: Score existing results without re-running API
ai-eval score --results data/raw_results.csv --output results/scored.csv && \
ai-eval report --results results/scored.csv --output-dir ./reports

# Scenario 3: Compare against baseline to detect regressions
ai-eval check-regression results/current.csv --baseline data/baseline.csv

# Scenario 4: Dry run for testing (no API calls)
ai-eval evaluate --prompts data/prompts/test.json --model gpt-4-turbo --dry-run
```

## Configuration

Configuration is managed via `config/settings.yaml`. Edit this file to customize behavior.

### Complete Configuration Example

```yaml
# ============================================================================
# AI Evaluation QA Framework Configuration
# Version: 2.5.0
# ============================================================================

# Logging Configuration
logging:
  level: INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: evaluation.log           # Log file path
  console: true                  # Print to console?
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Model Configuration
models:
  openai:
    enabled: true
    api_key: ${OPENAI_API_KEY}   # Reads from environment variable
    timeout_seconds: 60
    max_retries: 3
    models:
      - gpt-4-turbo              # Latest stable GPT-4 (128K context)
      - gpt-4                     # Original GPT-4 (8K context)
      - gpt-3.5-turbo             # Fast, affordable baseline

  anthropic:
    enabled: true
    api_key: ${ANTHROPIC_API_KEY}
    timeout_seconds: 60
    max_retries: 3
    models:
      - claude-opus-4-7           # Most capable (200K context)
      - claude-sonnet-4-6         # Balanced (200K context)
      - claude-haiku-4-5          # Fastest, most affordable (200K context)

  azure_openai:
    enabled: false
    api_key: ${AZURE_OPENAI_API_KEY}
    endpoint: ${AZURE_OPENAI_ENDPOINT}
    deployment_name: 'gpt-4-deployment'
    api_version: '2024-06-01'
    timeout_seconds: 60
    max_retries: 3

# Scoring Configuration
scoring:
  rubric_type: 'heuristic'        # 'heuristic' or 'llm-based' (default: heuristic)

  # Define scoring dimensions (each 1-5 scale)
  dimensions:
    - name: accuracy
      weight: 0.30
      description: "Factual correctness and alignment with expected answer"
      min_score: 1
      max_score: 5

    - name: reasoning
      weight: 0.25
      description: "Quality of logical flow, explanation clarity, and structured thinking"
      min_score: 1
      max_score: 5

    - name: tone
      weight: 0.20
      description: "Appropriateness of voice, politeness, and professionalism"
      min_score: 1
      max_score: 5

    - name: completeness
      weight: 0.25
      description: "Coverage of all relevant aspects and response depth"
      min_score: 1
      max_score: 5

  # Heuristic rules for automated scoring
  heuristics:
    accuracy:
      - pattern: 'I (am not sure|don''t know|cannot determine)'
        score_adjustment: -1.0
        reason: 'Uncertainty marker detected'

      - pattern: 'according to|based on|research shows'
        score_adjustment: +0.5
        reason: 'Evidence attribution present'

    reasoning:
      - pattern: '(because|therefore|thus|hence|so that)'
        score_adjustment: +0.5
        reason: 'Logical connectors present'

      - pattern: '(repeat|again|same as)'
        score_adjustment: -1.0
        reason: 'Potential redundancy'

# Execution Configuration
execution:
  timeout_seconds: 60            # Max time per prompt (seconds)
  max_retries: 3                 # Retry attempts on failure
  concurrent_requests: 10        # Parallel API calls (test: max 50)
  checkpoint_interval: 50        # Save progress every N requests
  rate_limit_delay_ms: 100       # Delay between requests (ms)

# Data Processing
data:
  input_format: 'json'           # 'json' or 'csv'
  output_format: 'csv'           # 'csv' or 'parquet'
  chunk_size: 10000              # Rows per batch (for large files)
  validate_encoding: true        # Validate UTF-8 encoding?

# Output & Reporting
output:
  directory: './results'
  formats:
    - 'csv'                       # Scored results spreadsheet
    - 'html'                      # Interactive dashboards
    - 'json'                      # Machine-readable format

  dashboards:
    executive_summary: true       # High-level overview
    detailed_analysis: true       # Full results with filtering
    regression_report: true       # Comparison to baseline

# Security & Validation
security:
  sanitize_output: true          # XSS prevention via HTML escaping
  validate_filenames: true       # Prevent directory traversal
  mask_api_keys: true            # Hide keys in logs
  encryption: false              # (Future) Encrypt sensitive data
```

### Environment Variable Precedence

1. **Environment Variables** (highest priority): `OPENAI_API_KEY=sk-... python main.py`
2. **`.env` File**: Automatically loaded from project root via `python-dotenv`
3. **Configuration File** (`config/settings.yaml`): Hard-coded values
4. **Defaults**: Built-in fallbacks in code

Example:
```bash
# This overrides all config file settings
OPENAI_API_KEY='sk-...' CONCURRENT_REQUESTS=5 ai-eval evaluate --prompts test.json
```

## Output Files

Each evaluation generates the following outputs in `results/` directory:

```
results/
├── raw_results.csv                 # Model responses, tokens, and metadata
├── scored_results.csv              # Raw results + scoring dimensions (1-5)
├── defects.csv                     # Detected issues per response
├── cost_summary.txt                # Token counts and estimated costs
├── execution_summary.txt           # Execution logs and timing metrics
├── executive_summary.html          # High-level overview with key metrics
├── detailed_dashboard.html         # Interactive results with filtering/sorting
└── regression_report.html          # Comparison to baseline (if applicable)

# Example raw_results.csv columns:
# prompt_id,model,response,prompt_tokens,completion_tokens,execution_time_ms

# Example scored_results.csv columns:
# prompt_id,model,response,accuracy_score,reasoning_score,tone_score,completeness_score,overall_score

# Example defects.csv columns:
# prompt_id,model,defect_type,severity,description,evidence
```

## Project Structure

```
ai-evaluation-qa/
├── evaluation/                     # Core evaluation library (84% coverage)
│   ├── __init__.py
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── anthropic_client.py    # Anthropic API wrapper
│   │   └── openai_client.py       # OpenAI/Azure OpenAI wrapper
│   ├── evaluation_pipeline.py      # Main async evaluation workflow
│   ├── prompt_runner.py            # Model API executor with retries
│   ├── scoring_engine.py           # Rubric-based scoring (heuristic + LLM)
│   ├── defect_detector.py          # Hallucination & issue detection
│   ├── report_generator.py         # HTML/CSV report generation
│   ├── cost_tracker.py             # Token counting via tiktoken
│   ├── error_handler.py            # API error handling (retry, backoff)
│   ├── rate_limiter.py             # Concurrency and rate control
│   └── sanitizer.py                # Input/output safety (XSS, traversal)
│
├── config/                         # Configuration management
│   ├── __init__.py
│   ├── settings.yaml               # Main configuration file
│   ├── logging_config.py           # Logging setup
│   ├── validator.py                # Configuration validation
│   ├── config_loader.py            # Load and migrate configurations
│   └── prompt_validator.py         # JSON schema validation for prompts
│
├── scripts/                        # Utility scripts
│   ├── __init__.py
│   ├── regression_checker.py       # Regression detection CLI
│   ├── setup_verifier.py           # Installation verification
│   ├── prompt_loader.py            # Load and validate prompts
│   ├── data_validator.py           # Data cleaning and validation
│   └── setup.sh                    # Environment setup automation
│
├── tests/                          # Test suite (84% coverage, 140+ tests)
│   ├── test_evaluation_pipeline.py
│   ├── test_scoring_engine.py
│   ├── test_defect_detector.py
│   ├── test_clients/
│   ├── test_error_handling.py
│   └── conftest.py
│
├── data/
│   ├── prompts/                    # Sample prompt files
│   │   ├── reasoning_tests.json
│   │   ├── factual_accuracy.json
│   │   └── tone_and_style.json
│   └── baselines/                  # Reference results for regression testing
│
├── main.py                         # CLI entry point (ai-eval command)
├── setup.py                        # Package configuration
├── pyproject.toml                  # Modern Python project config
├── requirements.txt                # Dependencies
├── Dockerfile                      # Container configuration (multi-stage build)
├── docker-compose.yml              # Docker Compose for persistent state
├── Makefile                        # Development automation
├── .pre-commit-config.yaml         # Pre-commit hooks (Black, isort, Flake8)
├── .github/
│   └── workflows/
│       ├── test.yml                # Run tests on push
│       ├── lint.yml                # Linting checks
│       ├── security.yml            # Security scanning (Trivy, Bandit, Safety)
│       └── regression.yml          # Regression detection
├── CONTRIBUTING.md                 # Contribution guidelines
├── CHANGELOG.md                    # Version history and fixes
├── LICENSE                         # MIT License
└── README.md                       # This file
```

## How It Works

The evaluation pipeline follows these stages:

### 1. Validation Phase (5-10 seconds)
- Configuration file syntax and completeness check
- Prompt JSON schema validation (required fields: id, prompt, category)
- API key availability and connectivity test
- Directory permissions verification

### 2. Execution Phase (Variable, see timing below)
- Prompts are dispatched to LLM providers asynchronously
- Rate limiting enforced (default: 10 concurrent requests)
- Exponential backoff retry logic for rate limits (429) and timeouts
- Results saved to checkpoint every 50 requests (configurable)
- Failed requests logged but don't block batch processing

**API-Specific Behavior**:
```
OpenAI:
  - Rate limit: 500 RPM, 90,000 TPM (varies by tier)
  - Retry-After: Respected via exponential backoff
  - Timeout: 60 seconds (configurable)

Anthropic:
  - Rate limit: 50 RPM (standard), 500 RPM (scale tier)
  - Retry-After: Respected via exponential backoff
  - Timeout: 60 seconds (configurable)

Azure OpenAI:
  - Rate limit: Defined per deployment
  - Retry-After: Respected
  - Timeout: 60 seconds (configurable)
```

### 3. Checkpointing Phase (Real-time)
- Raw results saved every N requests (default: 50)
- Enables resumption after crashes with `--resume-from` flag
- Prevents re-execution of completed prompts

### 4. Scoring Phase (2-5 seconds per 100 results)
Responses scored across four dimensions using heuristic rules:

**Accuracy** (0-5 scale):
- +0.5: Evidence attribution ("according to...", "research shows...")
- -1.0: Uncertainty markers ("I don't know...", "I'm not sure...")
- Baseline: Lexical similarity to expected answer

**Reasoning** (0-5 scale):
- +0.5: Logical connectors ("because", "therefore", "hence")
- +0.5: Structured formatting (numbered lists, bullet points)
- -1.0: Redundancy patterns (repetitive content detected)

**Tone** (0-5 scale):
- +0.5: Politeness markers ("please", "thank you", "appreciate")
- -1.0: Harsh language, profanity, aggression
- Context-aware scoring based on prompt category

**Completeness** (0-5 scale):
- Based on response length relative to prompt complexity
- Penalty for incomplete or truncated responses
- Bonus for comprehensive coverage

### 5. Defect Detection Phase (1-2 seconds per 100 results)
Identifies and categorizes issues:

| Defect Type | Detection Method | Example |
|-------------|------------------|---------|
| **Hallucination** | Factual inconsistency check | Claims non-existent facts |
| **Logical Flaw** | Reasoning chain validation | Contradictory statements |
| **Redundancy** | Pattern matching for repetition | Same sentence repeated verbatim |
| **Tone Issue** | Sentiment analysis (TextBlob) | Inappropriate voice for context |
| **Incompleteness** | Coverage analysis | Cuts off mid-sentence |

### 6. Cost Tracking Phase (Instant)
- Token counting via `tiktoken` library
- Cost estimation based on current pricing:
  ```
  OpenAI GPT-4 Turbo:     $0.01/1K prompt tokens, $0.03/1K completion
  OpenAI GPT-3.5 Turbo:   $0.0005/1K prompt tokens, $0.0015/1K completion
  Anthropic Claude Opus:  $0.003/1K prompt tokens, $0.015/1K completion (prices as of June 2026)
  ```
- Provides cost breakdown by model and run

### 7. Reporting Phase (5-30 seconds)
Generates multiple output formats:

- **Executive Summary** (HTML): Key metrics, charts, model comparisons
- **Detailed Dashboard** (HTML): Interactive results with filtering, sorting, exports
- **Regression Report** (HTML): Comparison to baseline, delta analysis
- **CSV Exports**: For spreadsheet analysis, further processing
- **Cost Report** (TXT): Detailed token usage and cost breakdown

### Fault Tolerance Mechanisms

| Mechanism | Trigger | Behavior |
|-----------|---------|----------|
| **Exponential Backoff** | HTTP 429 (rate limit), 503 (service unavailable) | Retry with 2^attempt * base_delay (max 60s) |
| **Checkpointing** | Every 50 requests (configurable) | Save raw results to recovery file |
| **Error Isolation** | Individual API call failure | Log error, continue with remaining prompts |
| **Timeout Handling** | >60 second API response | Retry with backoff, fail after max_retries |
| **Input Sanitization** | XSS attempts in prompts | HTML escape all user-controlled output |
| **Path Validation** | Directory traversal attempts | Validate filenames, reject unsafe paths |

## Performance Benchmarks

**Test Configuration**: 1000 prompts, 5 concurrent workers, GPT-4 Turbo

| Stage | Duration | Notes |
|-------|----------|-------|
| Validation | 8 seconds | Config + schema validation |
| Execution | 45 minutes | ~1000 prompts ÷ 5 workers ÷ 2-3 tokens/sec |
| Scoring | 2 minutes | Heuristic-based, no API calls |
| Reporting | 15 seconds | HTML generation + charting |
| **Total** | **~47.5 minutes** | End-to-end pipeline |

**Token Usage**: ~2.5M tokens prompt + 1.2M tokens completion = $0.35 estimated cost

## Testing

```bash
# Run all tests with coverage report
pytest tests/ --cov=evaluation --cov=config --cov-report=term-missing

# Run specific test file
pytest tests/test_scoring_engine.py -v

# Run tests matching a pattern
pytest tests/ -k "test_accuracy" -v

# Run with specific markers (unit, integration, slow)
pytest tests/ -m "not slow" --tb=short

# Watch mode (auto-rerun on file changes)
ptw tests/

# Using Makefile shortcuts
make test              # Run all tests
make test-cov          # Run with HTML coverage report
make test-fast         # Skip slow tests
make lint              # Run linting (Black, isort, Flake8, mypy)
make lint-fix          # Auto-fix formatting issues
```

**Coverage**: 100% (v2.4.5)
**Test Count**: 140+ tests across 8 modules
**CI/CD**: GitHub Actions (test, lint, security scan) on every push

## Troubleshooting

### API Connection Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `OpenAI API key not found` | Missing or invalid key | Set `OPENAI_API_KEY` in `.env` or environment. Run `ai-eval validate` to check. |
| `401 Unauthorized` | Invalid or expired API key | Verify key format and expiration date via provider dashboard. |
| `429 Too Many Requests` | Rate limit exceeded | Reduce `concurrent_requests` in `config/settings.yaml` (try 5 instead of 10). Framework retries automatically with exponential backoff. |
| `503 Service Unavailable` | Provider temporarily down | Check OpenAI status or Anthropic status page. Retry after 5 minutes. |
| `Timeout after 60 seconds` | Prompt execution too slow | Increase `timeout_seconds` in config or simplify prompts. |

**Debugging**: Run with `--log-level DEBUG` for detailed error traces.

### Scoring Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `No valid responses to score` | All API calls failed or responses are empty | Check prompt JSON format. Run `ai-eval lint-prompts` to validate. Ensure API keys are active. |
| `Rubric dimension missing` | Scoring config incomplete | Verify all 4 dimensions (accuracy, reasoning, tone, completeness) are defined in `config/settings.yaml` under `scoring.dimensions`. |
| `Score calculation failed` | Invalid responses or NaN values | Check `raw_results.csv` for malformed responses. Ensure response text is valid UTF-8. |
| `Regression detection failed` | Baseline file missing or incompatible | Verify baseline CSV path. Ensure baseline has same columns as current results. |

### Execution Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'evaluation'` | Package not installed or venv not activated | Run `pip install -e .` or activate venv: `source venv/bin/activate` |
| `FileNotFoundError: config/settings.yaml` | Config file missing or path incorrect | Config file should be in project root. Check: `ls -la config/settings.yaml` |
| `PermissionError: [Errno 13]` | Output directory not writable | Check directory permissions: `chmod 755 results/` or change output directory in config. |
| `OutOfMemory` | Processing very large dataset | Reduce `chunk_size` in config (try 1000 instead of 10000). Process in batches. |

### Docker Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `docker: command not found` | Docker not installed | Install Docker Desktop or Docker Engine. |
| `API keys not accessible in container` | .env not passed to container | Use `docker run --env-file .env` or set individual: `docker run -e OPENAI_API_KEY=sk-...` |
| `Cannot access volumes` | Incorrect volume mount path | On Windows, use Docker Desktop paths or WSL2. Example: `-v C:/project:/app` |
| `Container exits immediately` | Command error inside container | Check logs: `docker logs <container_id>`. Run with `--rm -it` for interactive debugging. |

**Debugging Docker**:
```bash
# View container logs
docker logs ai-eval-container

# Run with interactive terminal
docker run -it --env-file .env -v $(pwd):/app ai-eval:latest bash

# Inspect image layers
docker history ai-eval:latest
```

## Cost Estimation Examples

### Example 1: Single Model Evaluation

```
Configuration: 100 prompts, GPT-4 Turbo
Execution results:
  100 prompts executed successfully
  Average tokens per prompt: 200 (prompt) + 150 (completion)
  Total: 20,000 prompt tokens + 15,000 completion tokens

Cost calculation:
  Prompt: 20,000 × $0.01 / 1,000 = $0.20
  Completion: 15,000 × $0.03 / 1,000 = $0.45
  Total: $0.65
```

### Example 2: Multi-Model Comparison

```
Configuration: 50 prompts, 3 models (GPT-4, Claude Opus, GPT-3.5)
Execution results:
  GPT-4 Turbo:        150 × 50 = 7,500 prompt + 5,000 completion
  Claude Opus:        150 × 50 = 7,500 prompt + 5,500 completion
  GPT-3.5 Turbo:      150 × 50 = 7,500 prompt + 4,000 completion

Total tokens: 22,500 prompt + 14,500 completion
Total cost: $0.22 + $0.08 + $0.07 = $0.37
```

**Cost Optimization Tips**:
- Use GPT-3.5-turbo or Claude Haiku for initial testing (10x cheaper)
- Batch similar prompts together for better context reuse
- Use shorter prompts to reduce token usage
- Review `cost_summary.txt` after each run

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on:

- **Development Environment Setup**: Virtual environment, dependencies, pre-commit hooks
- **Code Style**: PEP 8, type hints, 100+ character line limit
- **Testing Requirements**: 84% code coverage target, unit + integration tests
- **Pull Request Process**: Fork, branch, test, document, submit PR with description
- **Commit Message Convention**: `type(scope): description` (e.g., `fix(scoring): handle NaN values in heuristics`)

**Quick Contribution Workflow**:
```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/AI-Evaluation-QA.git

# 2. Create feature branch
git checkout -b fix/scoring-nan-bug

# 3. Make changes and test
pip install -e .[dev]
pytest tests/ --cov=evaluation

# 4. Commit with conventional message
git commit -m "fix(scoring): handle NaN values in accuracy dimension"

# 5. Push and create PR
git push origin fix/scoring-nan-bug
```

## License

MIT License — See [LICENSE](LICENSE) file for full text.

---

## Useful Links

| Resource | URL |
|----------|-----|
| **GitHub Repository** | https://github.com/darshil0/AI-Evaluation-QA |
| **Issue Tracker** | https://github.com/darshil0/AI-Evaluation-QA/issues |
| **Documentation** | See CONTRIBUTING.md and CHANGELOG.md in repo |
| **OpenAI API Docs** | https://platform.openai.com/docs |
| **Anthropic API Docs** | https://docs.anthropic.com |
| **Azure OpenAI Docs** | https://learn.microsoft.com/en-us/azure/cognitive-services/openai/ |

---

**Status**: Production / Stable (v2.5.0)
**Python**: 3.14+ | **License**: MIT | **Maintainer**: [@darshil0](https://github.com/darshil0)

**Last Updated**: 2026-06-27 | **Next Release**: TBD
