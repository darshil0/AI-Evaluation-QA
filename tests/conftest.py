"""
Pytest configuration and shared fixtures.
Provides reusable test fixtures for all test modules.

Author: Darshil
Version: 2.0.0
License: MIT
"""

import pytest
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_prompts():
    """Provide sample prompt data for testing."""
    return [
        {
            "id": "test_001",
            "category": "reasoning",
            "text": "What is 2 + 2?",
            "expected_characteristics": ["Correct answer", "Clear explanation"],
        },
        {
            "id": "test_002",
            "category": "empathy",
            "text": "I am feeling sad. Can you help?",
            "expected_characteristics": ["Empathetic response", "Helpful suggestions"],
        },
    ]


@pytest.fixture
def sample_results():
    """Provide sample execution results for testing."""
    return [
        {
            "prompt_id": "test_001",
            "category": "reasoning",
            "prompt_text": "What is 2 + 2?",
            "model_response": "The answer is 4. This is because addition combines quantities.",
            "timestamp": "2025-01-01T00:00:00",
            "model": "gpt-3.5-turbo",
        },
        {
            "prompt_id": "test_002",
            "category": "empathy",
            "prompt_text": "I am feeling sad. Can you help?",
            "model_response": "I understand you're feeling sad. Here are some suggestions...",
            "timestamp": "2025-01-01T00:01:00",
            "model": "gpt-3.5-turbo",
        },
    ]


@pytest.fixture
def sample_scored_results():
    """Provide sample scored results for testing."""
    return [
        {
            "prompt_id": "test_001",
            "category": "reasoning",
            "prompt_text": "What is 2 + 2?",
            "model_response": "The answer is 4.",
            "timestamp": "2025-01-01T00:00:00",
            "model": "gpt-3.5-turbo",
            "accuracy_score": 5,
            "reasoning_score": 4,
            "tone_score": 3,
            "completeness_score": 3,
            "overall_score": 4.15,
            "defects": "None",
        },
        {
            "prompt_id": "test_002",
            "category": "empathy",
            "prompt_text": "I am feeling sad.",
            "model_response": "I understand your feelings.",
            "timestamp": "2025-01-01T00:01:00",
            "model": "gpt-3.5-turbo",
            "accuracy_score": 3,
            "reasoning_score": 3,
            "tone_score": 5,
            "completeness_score": 2,
            "overall_score": 3.25,
            "defects": "D04",
        },
    ]


@pytest.fixture
def mock_openai_response():
    """Provide a mock OpenAI API response."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "This is a test response from the AI model."
    return mock_response


@pytest.fixture
def mock_config():
    """Provide mock configuration data."""
    return {
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 500,
        "system_prompt": "You are a helpful assistant.",
    }


@pytest.fixture
def sample_config_yaml():
    """Provide sample YAML configuration content."""
    return """
model: "gpt-3.5-turbo"
temperature: 0.7
max_tokens: 500
system_prompt: "You are a helpful assistant."
api_timeout: 30
max_retries: 3
"""


@pytest.fixture
def sample_prompts_json():
    """Provide sample JSON prompts content."""
    return """
[
    {
        "id": "test_001",
        "category": "reasoning",
        "text": "What is 2 + 2?",
        "expected_characteristics": ["Correct answer"]
    },
    {
        "id": "test_002",
        "category": "empathy",
        "text": "I am sad.",
        "expected_characteristics": ["Empathetic tone"]
    }
]
"""


@pytest.fixture
def sample_results_csv():
    """Provide sample CSV results content."""
    return """prompt_id,category,prompt_text,model_response,timestamp,model
test_001,reasoning,What is 2+2?,The answer is 4,2025-01-01T00:00:00,gpt-3.5-turbo
test_002,empathy,I am sad,I understand your feelings,2025-01-01T00:01:00,gpt-3.5-turbo
"""


@pytest.fixture
def sample_scored_csv():
    """Provide sample scored CSV content."""
    return """prompt_id,category,model_response,accuracy_score,reasoning_score,tone_score,completeness_score,overall_score,defects
test_001,reasoning,The answer is 4,5,4,3,3,4.15,None
test_002,empathy,I understand,3,3,5,2,3.25,D04
"""


@pytest.fixture(autouse=True)
def reset_matplotlib():
    """Reset matplotlib state between tests."""
    import matplotlib.pyplot as plt

    plt.close("all")
    yield
    plt.close("all")


@pytest.fixture
def mock_file_operations(monkeypatch):
    """Mock common file operations."""

    def mock_makedirs(path, exist_ok=False):
        pass

    monkeypatch.setattr(os, "makedirs", mock_makedirs)


# Test markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


# Custom assertions
def pytest_assertrepr_compare(op, left, right):
    """Provide custom assertion messages."""
    if isinstance(left, dict) and isinstance(right, dict) and op == "==":
        return [
            "Dictionary comparison:",
            f"Left keys: {set(left.keys())}",
            f"Right keys: {set(right.keys())}",
            f"Difference: {set(left.keys()) ^ set(right.keys())}",
        ]
