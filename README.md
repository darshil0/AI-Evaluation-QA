# AI Evaluation QA Framework

<p align="center">
  <img src="https://img.shields.io/badge/version-2.4.0-green.svg" alt="Version Badge">
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

- [Project Skills & Expertise](Skills.md) — Core competencies and architecture.
- [Business Logic & Workflow](BUSINESS_LOGIC.md) — Evaluation pipeline and data flow.
- [Prompt Engineering Architecture](PROMPT_ENGINEERING.md) — Prompt design patterns and best practices.
- [Contributing Guide](CONTRIBUTING.md) — Development setup, testing, and pull request guidelines.
- [Issue Audit & Fixes](FIXES_SUMMARY.md) — Comprehensive QA audit and resolution log.

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

**2.4.0** (Current)
- Foundational Documentation (`Skills.md`, `BUSINESS_LOGIC.md`, `PROMPT_ENGINEERING.md`)
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
