.PHONY: help install install-dev test test-quick test-unit test-integration test-parallel test-run coverage lint format check security clean run run-model score report regression validate verify init docs update-deps docker-build docker-run

.DEFAULT_GOAL := help

PYTHON ?= python
PIP ?= pip
PYTEST ?= pytest
BLACK ?= black
ISORT ?= isort
FLAKE8 ?= flake8
MYPY ?= mypy
BANDIT ?= bandit
SAFETY ?= safety
DOCKER ?= docker

MODEL ?= gpt-4
PROMPT_FILE ?= data/prompts/sample_prompts.json
REPORTS_DIR ?= reports
CHECKPOINT_DIR ?= data/checkpoints
DOCKER_IMAGE ?= ai-evaluation-qa:2.6.1

SRC_DIRS := evaluation config scripts
TEST_DIR := tests

# FIX: Use Make's conditional instead of broken shell syntax
TARGET_FILES := main.py
ifneq (,$(wildcard setup.py))
TARGET_FILES += setup.py
endif

help:  ## Show this help message
	@echo "AI Evaluation QA Framework - Available Commands"
	@echo "================================================"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\\033[36m%-20s\\033[0m %s\\n", $$1, $$2}'

install:  ## Install all dependencies
	@echo "Installing dependencies..."
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e .
	@echo "Installation complete!"

install-dev:  ## Install development dependencies
	@echo "Installing dev dependencies..."
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e .[dev]
	@echo "Installing pre-commit..."
	$(PIP) install pre-commit
	pre-commit install || { echo "❌ Pre-commit installation failed"; exit 1; }
	pre-commit run --all-files || true
	@echo "Dev installation complete!"

test:  ## Run all tests with coverage
	@echo "Running tests..."
	PYTHONPATH=. $(PYTEST) $(TEST_DIR) --cov=evaluation --cov=config --cov=scripts --cov-report=html --cov-report=term-missing --cov-fail-under=100 -v

test-quick:  ## Run tests without coverage (faster)
	@echo "Running quick tests..."
	PYTHONPATH=. $(PYTEST) $(TEST_DIR) -v --tb=short

test-unit:  ## Run only unit tests
	@echo "Running unit tests..."
	@PYTHONPATH=. $(PYTEST) $(TEST_DIR) -m unit -v --collect-only 2>/dev/null | grep -q "test" || { echo "⚠️  No unit tests found"; exit 0; }
	PYTHONPATH=. $(PYTEST) $(TEST_DIR) -m unit -v

test-integration:  ## Run only integration tests
	@echo "Running integration tests..."
	@PYTHONPATH=. $(PYTEST) $(TEST_DIR) -m integration -v --collect-only 2>/dev/null | grep -q "test" || { echo "⚠️  No integration tests found"; exit 0; }
	PYTHONPATH=. $(PYTEST) $(TEST_DIR) -m integration -v

test-parallel:  ## Run tests in parallel
	@echo "Running tests in parallel..."
	@$(PYTHON) -c "import pytest_xdist" 2>/dev/null || (echo "pytest-xdist missing. Installing..."; $(PIP) install pytest-xdist)
	PYTHONPATH=. $(PYTEST) $(TEST_DIR) -n auto -v

test-run:  ## Quick sanity test for Docker
	@echo "Running sanity checks..."
	@echo "Python version:" && $(PYTHON) --version
	@echo "Installed packages:" && $(PIP) list | head -10
	@echo "Framework imports:" && $(PYTHON) -c "from evaluation.evaluation_pipeline import EvaluationPipeline; print('EvaluationPipeline import successful')"
	@echo "All sanity checks passed!"

coverage:  ## Generate and open coverage report
	@echo "Generating coverage report..."
	PYTHONPATH=. $(PYTEST) $(TEST_DIR) --cov=evaluation --cov=config --cov=scripts --cov-report=html
	@echo "Coverage report generated in htmlcov/"

lint:  ## Run all linters
	@echo "Running linters..."
	$(BLACK) --check $(SRC_DIRS) $(TEST_DIR) $(TARGET_FILES)
	$(ISORT) --check-only $(SRC_DIRS) $(TEST_DIR) $(TARGET_FILES)
	$(FLAKE8) $(SRC_DIRS) $(TEST_DIR) $(TARGET_FILES) --max-line-length=100 --extend-ignore=E203,W503
	$(MYPY) $(SRC_DIRS) $(TARGET_FILES) --ignore-missing-imports --explicit-package-bases --python-version 3.14 || true
	@echo "Linting complete!"

format:  ## Auto-format code with black and isort
	@echo "Formatting code..."
	$(BLACK) $(SRC_DIRS) $(TEST_DIR) $(TARGET_FILES)
	$(ISORT) $(SRC_DIRS) $(TEST_DIR) $(TARGET_FILES)
	@echo "Formatting complete!"

check:  ## Run format, lint, and test
	@echo "Running full check..."
	@$(MAKE) format
	@$(MAKE) lint
	@$(MAKE) test
	@echo "All checks passed!"

security:  ## Run security checks
	@echo "Running security checks..."
	$(BANDIT) -r $(SRC_DIRS) $(TARGET_FILES) -ll || { echo "⚠️  Bandit found issues"; exit 1; }
	$(SAFETY) check || { echo "⚠️  Safety found known vulnerabilities (review CHANGELOG.md)"; }
	@echo "Security check complete!"

clean:  ## Clean build artifacts and cache
	@echo "Cleaning..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml dist/ build/
	@echo "Cleanup complete!"

run:  ## Run full evaluation pipeline
	@echo "Running evaluation pipeline..."
	$(PYTHON) main.py evaluate --prompts $(PROMPT_FILE)
	@echo "Evaluation complete! Check $(REPORTS_DIR)/ for results"

run-model:  ## Run evaluation with specific model
	@echo "Running evaluation with model: $(MODEL)"
	$(PYTHON) main.py evaluate --prompts $(PROMPT_FILE) --model $(MODEL)

score:  ## Score the latest results
	@echo "Scoring responses..."
	@LATEST=$$(ls -t $(REPORTS_DIR)/run_results_*.csv 2>/dev/null | head -n1); \
	if [ -z "$$LATEST" ]; then \
		echo "No results file found. Run 'make run' first."; \
		exit 1; \
	fi; \
	$(PYTHON) main.py score --results "$$LATEST"

report:  ## Generate reports from latest scored results
	@echo "Generating reports..."
	@LATEST=$$(ls -t $(REPORTS_DIR)/run_results_*_scored.csv 2>/dev/null | head -n1); \
	if [ -z "$$LATEST" ]; then \
		echo "No scored results found. Run 'make score' first."; \
		exit 1; \
	fi; \
	$(PYTHON) main.py report --results "$$LATEST"

regression:  ## Check for performance regression
	@echo "Checking for performance regression..."
	@if [ -f scripts/regression_checker.py ]; then \
		$(PYTHON) scripts/regression_checker.py; \
	else \
		echo "Error: scripts/regression_checker.py is missing."; \
		exit 1; \
	fi

validate:  ## Validate prompt files
	@echo "Validating prompt files..."
	@if [ -d data/prompts ]; then \
		sh -c 'set -e; for file in data/prompts/*.json; do \
			[ -e "$$file" ] || continue; \
			echo "Validating $$file..."; \
			$(PYTHON) -c "import json,sys; json.load(open(sys.argv[1], encoding=\\"utf-8\\"))" "$$file"; \
		done'; \
		echo "All prompts valid!"; \
	else \
		echo "data/prompts directory not found"; \
	fi

verify:  ## Verify installation and configuration
	@echo "Verifying installation..."
	@$(PYTHON) --version
	@$(PIP) --version
	@echo "Checking dependencies..."
	@$(PIP) list | grep -E "pytest|black|isort|mypy|click|openai" || true
	@echo "Checking API keys..."
	@if [ -z "$(OPENAI_API_KEY)" ] && [ -z "$(ANTHROPIC_API_KEY)" ]; then \
		echo "⚠️  No API keys found. Add to .env:"; \
		echo "    OPENAI_API_KEY=your-key-here"; \
		echo "    ANTHROPIC_API_KEY=your-key-here"; \
	else \
		$(PYTHON) -c "import os; print('OpenAI:', 'OK' if os.getenv('OPENAI_API_KEY') else 'MISSING'); print('Anthropic:', 'OK' if os.getenv('ANTHROPIC_API_KEY') else 'MISSING')"; \
	fi
	@echo "Verification complete!"

init:  ## Initialize project (first time setup)
	@echo "Initializing project..."
	@$(MAKE) install-dev
	@echo "Creating directories..."
	@mkdir -p logs $(REPORTS_DIR) data/prompts data/annotations $(CHECKPOINT_DIR)
	@echo "Setting up environment..."
	@if [ ! -f .env ]; then \
		printf "OPENAI_API_KEY=\\nANTHROPIC_API_KEY=\\nLOG_LEVEL=INFO\\n" > .env; \
		echo "Please edit .env and add your API keys"; \
	fi
	@if ! grep -q "^\\.env" .gitignore 2>/dev/null; then \
		echo ".env" >> .gitignore; \
		echo "Added .env to .gitignore"; \
	fi
	@echo "Initializing git hooks..."
	@pre-commit install || true
	@echo "Initialization complete!"



update-deps:  ## Update all dependencies to latest versions
	@echo "Updating dependencies..."
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) list --outdated
	@echo "Review outdated packages above and update requirements.txt or pyproject.toml manually"

docker-build:  ## Build Docker image
	@echo "Building Docker image..."
	$(DOCKER) build --build-arg PYTHON_VERSION=3.14 -t $(DOCKER_IMAGE) -t ai-evaluation-qa:latest .

docker-run:  ## Run evaluation in Docker
	@echo "Running in Docker..."
	$(DOCKER) run --rm \
		-v $(PWD)/reports:/app/reports \
		--env-file .env \
		$(DOCKER_IMAGE) \
		python -c "from evaluation.evaluation_pipeline import EvaluationPipeline; print('EvaluationPipeline import successful')"
