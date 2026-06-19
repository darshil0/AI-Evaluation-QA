from unittest.mock import AsyncMock, MagicMock

import pytest

from evaluation.clients.anthropic_client import AnthropicClient


@pytest.mark.asyncio
async def test_anthropic_client_init():
    config = {"api_key": "test_key", "models": {"primary": {"model_name": "claude-test"}}}
    client = AnthropicClient(config)
    assert client.api_key == "test_key"
    assert client.model == "claude-test"


@pytest.mark.asyncio
async def test_anthropic_client_execute_prompt_success():
    config = {"api_key": "test_key"}
    client = AnthropicClient(config)

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value={
            "content": [{"text": "Test response"}],
            "usage": {"input_tokens": 10, "output_tokens": 20},
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
async def test_anthropic_client_execute_prompt_api_error():
    config = {"api_key": "test_key"}
    client = AnthropicClient(config)

    mock_response = AsyncMock()
    mock_response.status = 400
    mock_response.text = AsyncMock(return_value="Bad Request")

    mock_session = MagicMock()
    mock_session.post.return_value.__aenter__.return_value = mock_response

    prompt_data = {"id": "test_001", "text": "Hello"}
    result = await client.execute_prompt(prompt_data, mock_session)

    assert result["status"] == "error"
    assert "API error 400" in result["error"]


@pytest.mark.asyncio
async def test_anthropic_client_execute_prompt_exception():
    config = {"api_key": "test_key"}
    client = AnthropicClient(config)

    mock_session = MagicMock()
    mock_session.post.side_effect = Exception("Network error")

    prompt_data = {"id": "test_001", "text": "Hello"}
    result = await client.execute_prompt(prompt_data, mock_session)

    assert result["status"] == "error"
    assert "Network error" in result["error"]
