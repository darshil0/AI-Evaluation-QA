"""Pytest configuration and shared fixtures.

Provides reusable test fixtures for all test modules.

Author: Darshil
Version: 2.0.0
License: MIT
"""

from unittest.mock import MagicMock

import matplotlib.pyplot as plt
import pytest

# Note: Removed sys.path modification. Define project root via pyproject.toml,
# pytest.ini, or by running: python -m pytest


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory path using pytest's native fixture."""
    return str(tmp_path)


@pytest.fixture
def sample_prompts():
    """Provide sample prompt data for testing."""
    return {
        "prompts": [
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
                "expected_characteristics": [
                    "Empathetic response",
                    "Helpful suggestions",
                ],
            },
        ]
    }


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
    """Provide a structured mock OpenAI API response."""
    mock_message = MagicMock()
    mock_message.content = "This is a test response from the AI model."

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
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
    return (
        "prompt_id,category,prompt_text,model_response,timestamp,model\n"
        "test_001,reasoning,What is 2+2?,The answer is 4,2025-01-01T00:00:00,gpt-3.5-turbo\n"
        "test_002,empathy,I am sad,I understand your feelings,2025-01-01T00:01:00,gpt-3.5-turbo\n"
    )


@pytest.fixture
def sample_scored_csv():
    """Provide sample scored CSV content."""
    return (
        "prompt_id,category,model_response,accuracy_score,reasoning_score,tone_score,\
completeness_score,overall_score,defects\n"
        "test_001,reasoning,The answer is 4,5,4,3,3,4.15,None\n"
        "test_002,empathy,I understand,3,3,5,2,3.25,D04\n"
    )


@pytest.fixture(autouse=True)
def reset_matplotlib():
    """Automatically close all matplotlib figures between tests."""
    yield
    plt.close("all")


@pytest.fixture
def mock_file_operations(monkeypatch):
    """Mock common file operations to prevent side effects."""
    monkeypatch.setattr("os.makedirs", lambda path, exist_ok=False: None)


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


def pytest_assertrepr_compare(op, left, right):
    """Provide custom assertion messages for dictionary matching."""
    if isinstance(left, dict) and isinstance(right, dict) and op == "==":
        return [
            "Dictionary comparison failed:",
            f"Left keys:  {set(left.keys())}",
            f"Right keys: {set(right.keys())}",
            f"Difference: {set(left.keys()) ^ set(right.keys())}",
        ]
    return None
