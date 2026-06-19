from unittest.mock import AsyncMock, MagicMock

import pytest

from evaluation.clients.openai_client import OpenAIClient


@pytest.mark.asyncio
async def test_openai_client_init():
    config = {"api_key": "test_key", "models": {"primary": {"model_name": "gpt-test"}}}
    client = OpenAIClient(config)
    assert client.api_key == "test_key"
    assert client.model == "gpt-test"


@pytest.mark.asyncio
async def test_openai_client_execute_prompt_success():
    config = {"api_key": "test_key"}
    client = OpenAIClient(config)

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value={
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        }
    )

    mock_session = MagicMock()
    mock_session.post.return_value.__aenter__.return_value = mock_response

    prompt_data = {"id": "test_001", "text": "Hello"}
    result = await client.execute_prompt(prompt_data, mock_session)

    assert result["status"] == "success"
    assert result["response"] == "Test response"
    assert result["prompt_tokens"] == 10
    assert result["response_tokens"] == 20


@pytest.mark.asyncio
async def test_openai_client_execute_prompt_api_error():
    config = {"api_key": "test_key"}
    client = OpenAIClient(config)

    mock_response = AsyncMock()
    mock_response.status = 401
    mock_response.text = AsyncMock(return_value="Unauthorized")

    mock_session = MagicMock()
    mock_session.post.return_value.__aenter__.return_value = mock_response

    prompt_data = {"id": "test_001", "text": "Hello"}
    result = await client.execute_prompt(prompt_data, mock_session)

    assert result["status"] == "error"
    assert "API error 401" in result["error"]


@pytest.mark.asyncio
async def test_openai_client_execute_prompt_exception():
    config = {"api_key": "test_key"}
    client = OpenAIClient(config)

    mock_session = MagicMock()
    mock_session.post.side_effect = Exception("OpenAI down")

    prompt_data = {"id": "test_001", "text": "Hello"}
    result = await client.execute_prompt(prompt_data, mock_session)

    assert result["status"] == "error"
    assert "OpenAI down" in result["error"]
