from evaluation.model_constants import ModelStrings


def test_model_strings():
    assert ModelStrings.get_latest_sonnet() == "claude-sonnet-4-6"
    assert ModelStrings.get_latest_haiku() == "claude-haiku-4-5-20251001"
    assert ModelStrings.get_latest_opus() == "claude-opus-4-6"

    all_models = ModelStrings.get_all_models()
    assert "gpt-4" in all_models
    assert all_models["gpt-4"] == "gpt-4"
