"""Setup configuration for AI Evaluation QA Framework."""

from pathlib import Path

from setuptools import find_packages, setup

# Read README
readme_path = Path("README.md")
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="ai-evaluation-qa",
    version="2.4.0",
    author="Darshil",
    author_email="",
    description="Production-grade framework for evaluating AI model responses",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/darshil0/AI-Evaluation-QA",
    # Fixed: Use find_packages to discover all packages correctly
    # Excludes: tests, docs, examples (which don't exist or are unnecessary)
    packages=find_packages(
        exclude=["tests*", "docs*", "examples*", ".github*", ".venv*", "__pycache__*"]
    ),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    # Fixed: Synchronized versions with pyproject.toml and requirements.txt
    install_requires=[
        "openai>=1.60.0",  # Fixed: Was 2.40.0 in setup.py, unified to 1.60.0
        "aiohttp>=3.10.0",  # Fixed: Was 3.14.0, unified to 3.10.0
        "jsonschema>=4.21.0",
        "pyyaml>=6.0.3",
        "matplotlib>=3.8.0",  # Fixed: Was 3.10.9, unified
        "plotly>=5.24.0",  # Fixed: Was 6.7.0, unified to 5.24.0
        "click>=8.1.0",  # Fixed: Was 8.4.1, unified to 8.1.0
        "python-dotenv>=1.0.0",  # Fixed: Was 1.2.2, unified to 1.0.0
        "tiktoken>=0.7.0",  # Fixed: Was 0.13.0, unified
        "numpy>=1.26.0",
        "pandas>=2.2.0",
        "scipy>=1.13.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.3.0",
            "pytest-cov>=5.0.0",
            "pytest-asyncio>=0.24.0",
            "pytest-xdist>=3.6.0",
            "pytest-html>=4.1.0",
            "black>=24.10.0",
            "isort>=5.13.0",
            "flake8>=7.0.0",
            "flake8-bugbear>=24.0.0",
            "mypy>=1.9.0",
            "pylint>=3.1.0",
            "bandit>=1.7.0",
            "safety>=2.3.5",
            "pre-commit>=3.6.0",
            "coverage>=7.6.0",
            "coverage-badge>=1.1.2",
        ],
        "pdf": ["reportlab>=3.6.0", "weasyprint>=54.0"],
        "ml": ["scikit-learn>=1.1.0"],
    },
    entry_points={
        "console_scripts": [
            "ai-eval=main:cli",
        ],
    },
    include_package_data=True,
    # Fixed: Proper package data configuration for all packages
    package_data={
        "evaluation": ["*.yaml", "*.yml", "*.json"],
        "config": ["*.yaml", "*.yml"],
        "scripts": ["*.yaml", "*.yml"],
    },
    zip_safe=False,
    keywords=[
        "ai",
        "evaluation",
        "qa",
        "testing",
        "llm",
        "quality-assurance",
        "prompt-testing",
        "model-evaluation",
    ],
    project_urls={
        "Bug Reports": "https://github.com/darshil0/AI-Evaluation-QA/issues",
        "Source": "https://github.com/darshil0/AI-Evaluation-QA",
        "Documentation": "https://github.com/darshil0/AI-Evaluation-QA/blob/main/docs/",
    },
)
