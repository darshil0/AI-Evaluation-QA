# Technical Skills & Competencies

The **AI Evaluation QA Framework** demonstrates and requires the following technical competencies:

## Core Technical Stack
- **Python 3.14+**: Leverages the latest Python features and maintains compatibility with upcoming releases.
- **Asynchronous Programming (`asyncio`)**: High-concurrency execution of API requests to maximize throughput and efficiency.
- **Data Engineering**: Robust data processing using `pandas`, `numpy`, and `scipy` for large-scale evaluation results.
- **LLM Integration**: Deep integration with OpenAI, Anthropic, and Azure OpenAI APIs, including advanced exponential backoff, rate limiting, and provider-specific error handling.

## Software Architecture
- **Modular Design**: Clean separation of concerns between execution, scoring, reporting, and configuration.
- **Client-Based Architecture**: Standardized interfaces for multi-provider support.
- **Fault Tolerance**: Implementation of exponential backoff, retries, and mid-batch checkpointing.

## Quality Assurance & DevOps
- **100% Code Coverage**: Strict adherence to full test coverage for core modules using `pytest` and `coverage`, enforced via CI gates.
- **Static Analysis**: Enforced type safety with `mypy` (strict mode) and linting standards with `flake8`, `black`, and `isort`.
- **CI/CD Automation**: Comprehensive GitHub Actions workflows for testing, security scanning, and regression detection.
- **Containerization**: Multi-stage `Dockerfile` for optimized production deployments.

## Security
- **Input/Output Sanitization**: XSS prevention and directory traversal protection.
- **Security Scanning**: Integration of `bandit`, `safety`, and `trivy` in the development lifecycle.
- **API Security**: Secure handling of credentials and sensitive data masking.
