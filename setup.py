from setuptools import find_packages, setup

setup(
    name="ai-evaluation-qa",
    version="2.3.8",
    author="Darshil",
    author_email="",
    description="Production-grade framework for evaluating AI model responses",
    long_description=(
        open("README.md", encoding="utf-8").read()
        if __import__("pathlib").Path("README.md").exists()
        else ""
    ),
    long_description_content_type="text/markdown",
    url="https://github.com/darshil0/AI-Evaluation-QA",
    packages=find_packages(exclude=["tests*", "docs", "scripts", "examples"]),
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
    install_requires=[
        "openai>=2.40.0",
        "aiohttp>=3.14.0",
        "jsonschema>=4.26.0",
        "pyyaml>=6.0.3",
        "matplotlib>=3.10.9",
        "plotly>=6.7.0",
        "click>=8.4.1",
        "python-dotenv>=1.2.2",
        "tiktoken>=0.13.0",
        "numpy>=2.4.6",
        "pandas>=3.0.3",
        "scipy>=1.17.1",
    ],
    extras_require={
        "dev": [
            "pytest>=9.0.3",
            "pytest-cov>=7.1.0",
            "pytest-asyncio>=1.4.0",
            "pytest-xdist>=3.8.0",
            "black>=24.0.0",
            "isort>=5.13.0",
            "flake8>=7.0.0",
            "mypy>=1.9.0",
            "pylint>=3.1.0",
            "bandit>=1.7.0",
            "safety>=3.0.0",
            "pre-commit>=3.6.0",
            "coverage>=7.14.1",
            "coverage-badge>=1.1.2",
            "pytest-html>=4.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ai-eval=main:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json"],
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
