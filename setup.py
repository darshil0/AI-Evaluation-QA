from pathlib import Path

from setuptools import find_packages, setup

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="ai-evaluation-qa",
    version="2.3.8",
    author="Darshil",
    author_email="",
    description="Production-grade framework for evaluating AI model responses",
    long_description=long_description,
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
    install_requires=requirements,
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
