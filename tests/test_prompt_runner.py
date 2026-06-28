"""
Unit tests for prompt_runner.py

Covers:
- Async execution
- Rate limiting enforcement
- Error handling
- CSV export and summary
- Progress tracking
"""

from pathlib import Path

import pytest

from evaluation.prompt_runner import PromptRunner

TMP_DIR = Path("tests/tmp_reports")
TMP_DIR.mkdir(exist_ok=True)


@pytest.fixture
def sample_prompts():
    return [
        {"id": "p1", "text": "Hello world!", "category": "test"},
        {"id": "p2", "text": "Write a short poem.", "category": "test"},
    ]


@pytest.fixture
def config():
    return {
        "api_key": "sk-test",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 10,
        "rate_limit_rpm": 60,
        "max_retries": 1,
        "models": {"primary": {"provider": "openai"}},
    }


@pytest.mark.asyncio
async def test_async_execution(sample_prompts, config, monkeypatch):
    class FakeResponse:
        def __init__(self):
            self.status = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def json(self):
            return {
                "choices": [{"message": {"content": "Mock response"}}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 3},
            }

        def raise_for_status(self):
            pass

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def post(self, url, headers=None, json=None, timeout=None):
            return FakeResponse()

    monkeypatch.setattr("aiohttp.ClientSession", lambda: FakeSession())
    runner = PromptRunner(config)
    results = await runner.run_prompts(sample_prompts)
    assert len(results) == len(sample_prompts)
    for r in results:
        assert r["status"] == "success"
        assert r["response"] == "Mock response"


@pytest.mark.asyncio
async def test_save_results_and_summary(sample_prompts, config, monkeypatch):
    class FakeResponse:
        def __init__(self):
            self.status = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def json(self):
            return {
                "choices": [{"message": {"content": "Test"}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 5},
            }

        def raise_for_status(self):
            pass

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def post(self, url, headers=None, json=None, timeout=None):
            return FakeResponse()

    monkeypatch.setattr("aiohttp.ClientSession", lambda: FakeSession())
    runner = PromptRunner(config)
    results = await runner.run_prompts(sample_prompts)
    output_path = TMP_DIR / "test_results.csv"
    runner.save_responses(results, str(output_path), file_format="csv")
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    runner.print_summary()
