# AI Evaluation QA Framework

<p align="center">
  <img src="https://img.shields.io/badge/version-2.4.0-green.svg" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  <img src="https://img.shields.io/badge/coverage-100%25-brightgreen.svg" alt="Coverage">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python">
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/contributing-welcome-orange.svg" alt="Contributing"></a>
</p>

## Overview

The **AI Evaluation QA Framework** is a production-grade Python library designed for evaluating, scoring, and comparing AI model responses at scale. It provides a robust pipeline to run structured prompt suites against major LLM providers (OpenAI, Anthropic, Azure OpenAI), score them using customizable rubrics and heuristics, and generate professional HTML dashboards and executive summaries.

---

## Key Features

* 🚀 **Multi-Provider Support**: Seamlessly evaluate against OpenAI, Anthropic, and Azure OpenAI.
* ⚖️ **Rubric-Based Scoring**: Score responses across dimensions like **Accuracy**, **Reasoning**, **Tone**, and **Completeness** (1–5 scale).
* 🔍 **Automated Defect Detection**: Built-in detection for hallucinations, logical flaws, redundancy, and more.
* 📊 **Rich Analytics**: Generates interactive HTML dashboards, executive summaries, and detailed CSV exports.
* 🛡️ **Security & Sanitization**: Built-in input/output sanitization and filename safety to prevent injection attacks.
* 🛡️ **Robust Validation**: Comprehensive pre-execution checks for environment, configuration, and prompt schemas.
* 💰 **Cost Telemetry**: Precision token counting and cost estimation per model.
* 🔄 **Fault-Tolerant**: Mid-batch checkpointing ensures no progress is lost.
* ⚡ **Asynchronous & Fast**: Built with `asyncio` for high-concurrency API requests.
* 🛠️ **CI/CD Integrated**: Automated testing, security scanning, and regression monitoring.

---

## Documentation

* [Project Skills & Expertise](Skills.MD)
* [Business Logic & Workflow](BUSINESS_LOGIC.MD)
* [Prompt Engineering Architecture](PROMPT_ENGINEERING.MD)
* [Contributing Guide](CONTRIBUTING.md)

---

## Installation

```bash
# Clone the repository
git clone https://github.com/darshil0/AI-Evaluation-QA.git
cd AI-Evaluation-QA

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# For development (includes testing & linting tools)
pip install -e .[dev]
```

---

## Quick Start

### 1. Configure Environment

Create a `.env` file with your API keys:

```env
OPENAI_API_KEY='your-key-here'
ANTHROPIC_API_KEY='your-key-here'
```

### 2. Run Evaluation

```bash
ai-eval evaluate --prompts data/prompts/reasoning_tests.json
```

---

## CLI Reference

The framework provides a unified CLI entry point `ai-eval` (or `python main.py`):

| Command | Description | Example |
| --- | --- | --- |
| `evaluate` | Full pipeline: Run prompts, score, and report | `ai-eval evaluate --prompts tests.json` |
| `score` | Score an existing raw results CSV | `ai-eval score --results raw.csv --output scored.csv` |
| `report` | Generate reports from scored results | `ai-eval report --results scored.csv --output-dir reports/` |
| `check-regression` | Compare current results against a baseline | `ai-eval check-regression current.csv --baseline baseline.csv` |
| `validate` | Validate system configuration and setup | `ai-eval validate` |
| `lint-prompts` | Validate and lint a prompt JSON file | `ai-eval lint-prompts prompts.json` |

---

## Project Structure

* `evaluation/`: Core logic (pipeline, runner, scoring, reporting, sanitization, error handling).
* `config/`: System configuration and strict validation.
* `scripts/`: Utility scripts (data validation, prompt loading, regression checks).
* `tests/`: Comprehensive test suite with 100% coverage.
* `data/`: Sample prompts and execution checkpoints.

---

## Configuration

Configuration is managed via `config/settings.yaml`. Key sections:

* **models**: Provider setup (OpenAI, Anthropic, Azure)
* **scoring**: Rubric definitions and scoring rules
* **execution**: Timeout, retry, and concurrency settings
* **reporting**: Output formats and visualization options

See `CONTRIBUTING.md` for detailed configuration examples.

---

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest --cov=evaluation --cov=config --cov-report=term-missing

# Using Makefile
make test
```

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

* Development setup
* Coding standards and type hints
* Testing requirements (100% coverage)
* Pull request process

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

**Version**: 2.4.0  
**Status**: Production/Stable  
**Python**: 3.9+
