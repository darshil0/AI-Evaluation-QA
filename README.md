# AI Evaluation QA Framework

<p align="center">
  <img src="https://img.shields.io/badge/version-2.4.1-green.svg" alt="Version Badge">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License Badge">
  <img src="https://img.shields.io/badge/coverage-100%25-brightgreen.svg" alt="Test Coverage Badge">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python Version Badge">
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/contributing-welcome-orange.svg" alt="Contributing Badge"></a>
</p>

## Overview

The **AI Evaluation QA Framework** is a production-grade Python library designed for evaluating, scoring, and comparing AI model responses at scale. It provides a robust pipeline to run structured prompt suites against major LLM providers (OpenAI, Anthropic, Azure OpenAI), score them using customizable rubrics and heuristics, and generate professional HTML dashboards, executive summaries, and detailed analytics.

---

## Key Features

- 🚀 **Multi-Provider Support**: Seamlessly evaluate against OpenAI, Anthropic, and Azure OpenAI.
- ⚖️ **Rubric-Based Scoring**: Score responses across dimensions like Accuracy, Reasoning, Tone, and Completeness (1–5 scale).
- 🔍 **Automated Defect Detection**: Built-in detection for hallucinations, logical flaws, redundancy, poor tone, and incomplete responses.
- 📊 **Rich Analytics & Dashboards**: Interactive HTML dashboards, executive summaries, trend analysis, and detailed CSV exports.
- 💰 **Cost Telemetry**: Precision token counting and estimated cost tracking per model and run.
- 🛡️ **Security & Validation**: Input/output sanitization, filename safety controls, and comprehensive pre-execution checks.
- 🔄 **Fault-Tolerant & Resumable**: Mid-batch checkpointing ensures no progress is lost on failure.
- ⚡ **Asynchronous & Fast**: Built with `asyncio` for high-concurrency API requests.
- 🐳 **Docker & CI/CD Ready**: Includes Dockerfile, GitHub Actions workflows, and automated testing pipelines.

---

## Requirements

- **Python**: 3.9 or higher
- **API Keys**: At least one of the following:
  - OpenAI API key (`OPENAI_API_KEY`)
  - Anthropic API key (`ANTHROPIC_API_KEY`)
  - Azure OpenAI credentials (`AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`)
- **Docker** (optional): For containerized execution

---

## Documentation

- [Project Skills & Expertise](#project-skills--expertise) — Core competencies and architecture.
- [Business Logic & Workflow](#business-logic--workflow-architecture) — Evaluation pipeline and data flow.
- [Prompt Engineering Architecture](CONTRIBUTING.md#reverse-engineered-prompt-engineering) — Prompt design patterns and best practices.
- [Contributing Guide](CONTRIBUTING.md) — Development setup, testing, and pull request guidelines.
- [Issue Audit & Fixes](CHANGELOG.md#historical-fixes-summary-v240--v238-patch) — Comprehensive QA audit and resolution log.

---

## Installation

### Standard Installation

```bash
# Clone the repository
git clone https://github.com/darshil0/AI-Evaluation-QA.git
cd AI-Evaluation-QA

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# For development (includes testing, linting, and type-checking)
pip install -e .[dev]
```

### Docker Installation

```bash
# Build the Docker image
docker build -t ai-eval:latest .

# Run the container
docker run --env-file .env ai-eval:latest ai-eval validate
```

---

## Quick Start

### 1. Configure Environment

Create a `.env` file in the project root with your API keys:

```env
# At least one provider is required
OPENAI_API_KEY='sk-...'
ANTHROPIC_API_KEY='sk-ant-...'
AZURE_OPENAI_API_KEY='your-azure-key'
AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'

# Optional: Logging and output configuration
LOG_LEVEL='INFO'
OUTPUT_DIR='./reports'
```

### 2. Validate Setup

```bash
ai-eval validate
```

This checks environment, API connectivity, and configuration validity.

### 3. Run Evaluation

```bash
ai-eval evaluate --prompts data/prompts/reasoning_tests.json \
                 --model gpt-4-turbo
```

### 4. Generate Reports

Reports are generated automatically during evaluation, but you can regenerate them from existing results:

```bash
ai-eval report --results results/scored_results.csv --output-dir ./reports
```

---

## Example Prompt File

Create a JSON file with your test cases (e.g., `data/prompts/reasoning_tests.json`):

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
    "prompt": "Who is the current CEO of OpenAI (as of January 2026)?",
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

---

## CLI Reference

### Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `evaluate` | Full pipeline: run prompts, score, and generate reports | `ai-eval evaluate --prompts tests.json --model gpt-4` |
| `score` | Score raw results from a previous run | `ai-eval score --results raw_results.csv --output scored.csv` |
| `report` | Generate HTML dashboards and summaries from scored results | `ai-eval report --results scored.csv --output-dir ./reports` |
| `check-regression` | Compare current results against a historical baseline | `ai-eval check-regression current.csv --baseline baseline.csv` |
| `validate` | Validate environment setup, API keys, and configuration | `ai-eval validate` |
| `lint-prompts` | Validate prompt JSON file structure and content | `ai-eval lint-prompts prompts.json` |

### Global Options

```bash
--log-level {DEBUG,INFO,WARNING,ERROR}  # Set logging verbosity (default: INFO)
--config PATH                            # Path to custom config file (default: config/settings.yaml)
--output-dir PATH                        # Output directory for results (default: ./results)
--dry-run                                # Simulate run without API calls
```

---

## Configuration

Configuration is managed via `config/settings.yaml`. Key sections:

### Models
```yaml
models:
  openai:
    enabled: true
    api_key: ${OPENAI_API_KEY}
    models:
      - gpt-4-turbo
      - gpt-3.5-turbo
  anthropic:
    enabled: true
    api_key: ${ANTHROPIC_API_KEY}
    models:
      - claude-opus-4-7
      - claude-sonnet-4-6
```

### Scoring Rubric
```yaml
scoring:
  dimensions:
    - name: accuracy
      weight: 0.3
      description: "Factual correctness and alignment with expected answer"
    - name: reasoning
      weight: 0.25
      description: "Quality of logical flow and explanation"
    - name: tone
      weight: 0.2
      description: "Appropriateness of voice and language"
    - name: completeness
      weight: 0.25
      description: "Coverage of all relevant aspects"
```

### Execution Settings
```yaml
execution:
  timeout_seconds: 60
  max_retries: 3
  concurrent_requests: 10
  checkpoint_interval: 50
```

See `CONTRIBUTING.md` for detailed configuration examples and schema.

---

## Output Files

Each evaluation generates the following outputs:

```
results/
├── raw_results.csv              # Model responses and token counts
├── scored_results.csv           # Raw results + scoring dimensions
├── defects.csv                  # Detected issues per response
├── cost_summary.txt             # Token counts and estimated costs
├── executive_summary.html       # High-level overview with charts
├── detailed_dashboard.html      # Interactive results with filtering
└── regression_report.html       # Comparison to baseline (if applicable)
```

---

## Testing

```bash
# Run all tests with coverage
pytest tests/ --cov=evaluation --cov=config --cov-report=term-missing

# Run specific test file
pytest tests/test_scoring.py -v

# Run with markers (unit, integration, slow)
pytest tests/ -m "not slow"

# Using Makefile
make test          # Run all tests
make test-cov      # Run with coverage report
make lint          # Run linting and type checks
```

---

## Project Structure

```
ai-evaluation-qa/
├── evaluation/              # Core library
│   ├── clients/             # Multi-provider API clients
│   ├── evaluation_pipeline.py # Main evaluation workflow
│   ├── prompt_runner.py     # Model API executor
│   ├── scoring_engine.py    # Rubric-based scoring engine
│   ├── defect_detector.py   # Automated issue detection
│   ├── report_generator.py  # Report generation
│   ├── cost_tracker.py      # Token counting and cost calculation
│   ├── error_handler.py     # API error handling and retries
│   ├── rate_limiter.py      # Concurrency and rate control
│   └── sanitizer.py         # Input/output safety
├── config/
│   ├── settings.yaml        # Main configuration
│   ├── logging_config.py    # Logging configuration
│   ├── validator.py         # Configuration validation
│   ├── config_loader.py     # Configuration loading and migration
│   └── prompt_validator.py  # Prompt schema validation
├── scripts/
│   ├── regression_checker.py # Check for performance regressions
│   ├── setup_verifier.py     # Verify installation and setup
│   ├── prompt_loader.py      # Logic for loading/validating prompts
│   ├── data_validator.py     # Data cleaning and validation utilities
│   └── setup.sh             # Environment setup script
├── tests/                  # 100% coverage test suite
├── data/
│   └── prompts/           # Sample prompt files
├── Dockerfile             # Container configuration
├── Makefile              # Common task automation
├── requirements.txt      # Dependencies
└── README.md            # This file
```

---

## Troubleshooting

### API Connection Issues

**Error**: `OpenAI API key not found`  
**Solution**: Ensure `OPENAI_API_KEY` is set in `.env` or environment variables. Run `ai-eval validate` to verify.

**Error**: `Rate limit exceeded`  
**Solution**: Reduce `concurrent_requests` in `config/settings.yaml` or add delays between batches.

### Scoring Issues

**Error**: `No valid responses to score`  
**Solution**: Check that prompt JSON structure matches the schema. Run `ai-eval lint-prompts` to validate.

**Error**: `Rubric dimension missing`  
**Solution**: Ensure all required scoring dimensions are defined in `config/rubric.json`.

### Docker Issues

**Error**: `docker: command not found`  
**Solution**: Install Docker Desktop or Docker Engine. See [Docker installation guide](https://docs.docker.com/get-docker/).

**Error**: `API keys not accessible in container`  
**Solution**: Pass `.env` file using `docker run --env-file .env` or use `docker-compose.yml`.

---

## Cost Estimation

The framework tracks token usage for cost optimization:

```
Model: gpt-4-turbo
  Prompt tokens:     45,230
  Completion tokens: 18,950
  Total cost:        $1.29
  
Model: claude-opus-4-7
  Prompt tokens:     45,230
  Completion tokens: 21,340
  Total cost:        $0.89
```

Costs are estimated based on current pricing as of January 2026. Verify with your provider for accuracy.

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Development environment setup
- Code style and type hints (PEP 8, mypy strict)
- Testing requirements (100% coverage mandatory)
- Pull request process and review criteria
- Commit message conventions

---

## License

MIT License. See [LICENSE](LICENSE) for full text.

---

## Version History

**2.4.1** (Current)
- Fixed missing `encoding="utf-8"` in `open()` calls across `validator.py`, `cost_tracker.py`, and the test suite for improved cross-platform stability on Windows.

**2.4.0**
- Foundational Documentation (`Skills.MD`, `BUSINESS_LOGIC.MD`, `PROMPT_ENGINEERING.MD`)
- CI/CD Pipeline with automated testing and security scanning
- Enhanced Error Handling and Retry Logic with exponential backoff
- Client-based architecture for LLM providers
- Fixed critical deadlocks and parameter shadowing bugs
- 100% test coverage enforced

**2.3.0**
- Multi-provider support (OpenAI, Anthropic)
- Rubric-based scoring
- CSV export and reporting

**2.0.0**
- Initial production release

---

**Status**: Production / Stable  
**Python**: 3.9+  
**Maintainer**: Darshil ([@darshil0](https://github.com/darshil0))


---


## Project Skills & Expertise

This repository demonstrates a high level of proficiency in modern software engineering, AI integration, and quality assurance practices. The following skills are core to the architecture and implementation of the **AI Evaluation QA Framework**.

## 🏗️ Software Architecture & Design
*   **Modular Design**: Clean separation of concerns between configuration, execution, scoring, and reporting modules.
*   **Asynchronous Programming**: Extensive use of `asyncio` for high-concurrency API interactions, ensuring optimal throughput.
*   **Factory & Strategy Patterns**: Implementation of flexible client architectures to support multiple LLM providers (OpenAI, Anthropic, Azure).
*   **Fault Tolerance**: Robust checkpointing mechanisms and sophisticated retry logic with exponential backoff.

## 🤖 AI & LLM Integration
*   **Multi-Provider Orchestration**: Deep integration with OpenAI, Anthropic, and Azure OpenAI APIs.
*   **Prompt Engineering**: Structured prompt management and validation, including support for complex reasoning and evaluation rubrics.
*   **Tokenomics**: Precise token counting and cost estimation across different model architectures using `tiktoken`.
*   **Model Evaluation**: Advanced heuristics and rubric-based scoring to quantify LLM performance.

## 📊 Data Engineering & Analytics
*   **Pipeline Orchestration**: Building end-to-end data pipelines from raw prompt execution to structured reporting.
*   **Data Validation**: Strict schema enforcement and semantic validation for input/output data.
*   **Automated Reporting**: Generation of professional HTML/CSS dashboards and interactive visualizations using `Plotly` and `Matplotlib`.
*   **Statistical Analysis**: Implementation of regression detection and performance benchmarking.

## 🛡️ Quality Assurance & Security
*   **Test-Driven Development (TDD)**: 100% code coverage policy with a comprehensive suite of unit and integration tests.
*   **CI/CD Mastery**: Automated workflows for testing, linting, security scanning, and regression monitoring.
*   **Security Best Practices**: Implementation of input sanitization, XSS protection, and automated secret detection.
*   **Static Analysis**: Rigorous use of `mypy`, `flake8`, `black`, and `isort` to maintain code quality.

## 🛠️ DevOps & Infrastructure
*   **Containerization**: Professional multi-stage `Dockerfile` for reproducible environments.
*   **Automation**: Advanced `Makefile` for streamlining development, testing, and deployment workflows.
*   **Environment Management**: Sophisticated configuration loading and environment variable management.

---
*This framework serves as a testament to building production-ready AI infrastructure that is scalable, secure, and maintainable.*



---


## Business Logic & Workflow Architecture

The **AI Evaluation QA Framework** is built on a modular architecture that separates data ingestion, model execution, scoring heuristics, and reporting. This document details the internal logic and data flow of the system.

## 1. Core Workflow Pipeline
The evaluation follows a linear but highly optimized pipeline:

1.  **Validation**: Before execution, the `ConfigurationValidator` and `PromptValidator` ensure that the environment is correctly set up, API keys are present, and prompt JSON files adhere to the required schema.
2.  **Prompt Orchestration**: The `EvaluationPipeline` loads prompts and dispatches them to the `PromptRunner`.
3.  **Concurrent Execution**: The `PromptRunner` utilizes `asyncio` to send multiple requests in parallel to LLM providers. It respects rate limits via an internal `RateLimiter` and handles errors using an asynchronous `EvaluationErrorHandler`.
4.  **Checkpointing**: As requests complete, results are saved to `data/checkpoints/` in real-time. This ensures that a network failure or crash doesn't lose progress.
5.  **Scoring & Analytics**: Raw responses are passed to the `ScoringEngine`, which applies a mixture of:
    *   **Heuristic Rules**: Pattern matching for logic, tone, and completeness.
    *   **Judge Models**: (Optional) Using LLMs to score other LLMs.
    *   **Defect Detection**: Identifying hallucinations or redundancies.
6.  **Cost Tracking**: The `CostTracker` calculates token usage and estimated costs using model-specific pricing and `tiktoken` encoding.
7.  **Reporting**: The `ReportGenerator` transforms the scored data into interactive HTML dashboards and executive summaries.

## 2. Scoring Heuristics
The framework scores responses on a 1–5 scale across four primary dimensions:

| Dimension | Logic / Heuristic |
| :--- | :--- |
| **Accuracy** | Checks for uncertainty markers, response length, and specific factual markers. |
| **Reasoning** | Analyzes logical connectors (e.g., "therefore", "consequently") and structured formatting (lists). |
| **Tone** | Monitors for positive/polite language vs. negative or dismissive markers. |
| **Completeness** | Evaluates word count thresholds and the presence of requested structural elements. |

## 3. Fault Tolerance & Error Handling
*   **Exponential Backoff**: When an API rate limit is hit (429 error), the system waits with increasing delays before retrying.
*   **Failed Request Tracking**: Requests that fail after all retries are logged but don't stop the rest of the batch.
*   **Safe Serialization**: The checkpointing logic skips rows that fail to serialize, ensuring the overall file remains valid.

## 4. Security & Sanitization
*   **Filename Safety**: All generated report filenames are sanitized to prevent directory traversal attacks.
*   **HTML Escaping**: User-provided content (prompts/responses) is escaped before being rendered in HTML reports to mitigate XSS risks.
*   **Secret Management**: The framework prevents the accidental logging of API keys or sensitive session data.

---
*This architecture is designed for production environments where reliability, speed, and clear audit trails are paramount.*

