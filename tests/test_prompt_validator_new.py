from config.prompt_validator import PromptValidator


def test_validate_semantic_short_text():
    data = {"prompts": [{"id": "p1", "text": "short", "category": "test"}]}
    valid, warnings = PromptValidator.validate_semantic(data)
    assert valid is True
    assert any("text is very short" in w for w in warnings)


def test_validate_semantic_invalid_token_range():
    data = {
        "prompts": [
            {
                "id": "p1",
                "text": "This is a long enough prompt for testing semantic validation.",
                "category": "test",
                "expected_criteria": {"min_tokens": 100, "max_tokens": 50},
            }
        ]
    }
    valid, warnings = PromptValidator.validate_semantic(data)
    assert valid is True
    assert any("min_tokens > max_tokens" in w for w in warnings)


def test_validate_schema_delegation():
    data = {
        "metadata": {"version": "2.3", "description": "test"},
        "prompts": [
            {"id": "p1", "text": "This is a long enough prompt for testing.", "category": "test"}
        ],
    }
    valid, errors = PromptValidator.validate_schema(data)
    assert valid is True
    assert errors == []
