# Contributing to AI Evaluation QA Framework

First off, thank you for considering contributing to the AI Evaluation QA Framework!

---

## 🛠️ Development Setup

We require Python 3.9+ for development. To set up your environment:

### 1. Fork and Clone
Fork the repository on GitHub and clone it locally:
```bash
git clone https://github.com/YOUR_USERNAME/AI-Evaluation-QA.git
cd AI-Evaluation-QA
```

### 2. Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -e .[dev]     # Install development dependencies
```

---

## 🎨 Coding Standards

To maintain a high-quality, professional codebase, please adhere to these standards:

- **Formatting**: Use [Black](https://github.com/psf/black) for code formatting and [isort](https://pycqa.github.io/isort/) for imports.
- **Linting**: Ensure `flake8` and `pylint` pass without errors.
- **Type Safety**: All new functions must include type hints.
- **Sanitization**: Use `DataSanitizer` in `evaluation/sanitizer.py` for any new user-controlled inputs or file outputs.
- **Validation**: Any new core functionality or configuration changes must include corresponding validation logic in `config/`.
- **Documentation**: All public classes and methods must have descriptive Google-style docstrings.

---

## 🧪 Testing Standards

We maintain a strict **100% Code Coverage** policy for all core modules.

### Running Tests
```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest --cov=evaluation --cov=config --cov-report=term-missing

# Using Makefile
make test
```

---

## 🚀 Pull Request Process

1. **Branching**: Create a descriptive branch name (e.g., `feat/add-new-metric`).
2. **Commit Messages**: Use [Conventional Commits](https://www.conventionalcommits.org/).
3. **Local Verification**: Run `make check` to ensure your code passes all linting and tests before pushing.
4. **Submission**: Open a PR against the `main` branch.

---

## ⚖️ Code of Conduct

We are committed to providing a welcoming and inspiring community. Please be respectful and professional in all interactions.

**Thank you for helping us build the future of AI Quality Assurance!**


---


## Reverse-Engineered Prompt Engineering

The **AI Evaluation QA Framework** was architected using a highly structured "System Meta-Prompt." This prompt was designed to guide an AI agent through the creation of a production-grade software system.

## The Architect's Prompt

> **Context**: You are a Lead Software Architect at a top-tier AI lab. You need to build a "Gold Standard" evaluation framework for Large Language Models.
>
> **Core Objective**: Create a Python-based framework that can run thousands of prompts across OpenAI, Anthropic, and Azure, score them automatically, and generate professional reports.
>
> **Constraints**:
> 1. **Reliability**: Must have 100% test coverage and handle API failures gracefully.
> 2. **Speed**: Must be asynchronous (asyncio) to maximize throughput.
> 3. **Observability**: Must track costs, token usage, and provide real-time checkpoints.
> 4. **Quality**: Adhere to the "Darshil Standard"—strict type hints, detailed docstrings, and robust input validation.
>
> **System Components to Build**:
> - A `PromptRunner` that handles concurrent API calls and rate limiting.
> - A `ScoringEngine` that uses heuristics to evaluate Accuracy, Reasoning, Tone, and Completeness.
> - A `ReportGenerator` that creates HTML dashboards with interactive visualizations.
> - A `ConfigLoader` with strict YAML validation.
> - A CLI entry point `main.py` using the `click` library.
>
> **Standards to Enforce**:
> - Use PEP 8 formatting (Black/isort).
> - Implement a `Makefile` for developer experience.
> - Use Multi-stage `Dockerfiles` for deployment.
> - Ensure 100% code coverage across all core modules.
>
> **Task**: Begin by outlining the directory structure, then implement the core execution pipeline, ensuring each module is self-contained and fully tested.

## Why This Prompt Works
1.  **Role Prompting**: Sets a high bar for quality by defining the persona (Lead Software Architect).
2.  **Clear Objective & Constraints**: Provides non-negotiable standards (100% coverage, asyncio).
3.  **Modular Decomposition**: Lists specific components to prevent "monolithic" code generation.
4.  **Standard Enforcement**: Explicitly mentions naming conventions and tooling (Black, Click, Makefile).

---
*By reverse-engineering the intent behind the framework, developers can better understand the "why" behind the code structure.*
