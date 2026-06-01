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
