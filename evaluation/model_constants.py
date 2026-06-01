"""
Centralized model configuration constants.
Update these when new model versions are released.
"""


class ModelStrings:
    """Latest model strings for supported providers."""

    # Anthropic Models (current as of mid-2026)
    CLAUDE_SONNET_4_6 = "claude-sonnet-4-6"
    CLAUDE_HAIKU_4_5 = "claude-haiku-4-5-20251001"
    CLAUDE_OPUS_4_6 = "claude-opus-4-6"

    # OpenAI Models
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_4 = "gpt-4"
    GPT_3_5_TURBO = "gpt-3.5-turbo"

    @classmethod
    def get_latest_sonnet(cls) -> str:
        """Get the latest Claude Sonnet model string."""
        return cls.CLAUDE_SONNET_4_6

    @classmethod
    def get_latest_haiku(cls) -> str:
        """Get the latest Claude Haiku model string."""
        return cls.CLAUDE_HAIKU_4_5

    @classmethod
    def get_latest_opus(cls) -> str:
        """Get the latest Claude Opus model string."""
        return cls.CLAUDE_OPUS_4_6

    @classmethod
    def get_all_models(cls) -> dict:
        """Get dictionary of all available models."""
        return {
            "claude-sonnet-4.6": cls.CLAUDE_SONNET_4_6,
            "claude-haiku-4.5": cls.CLAUDE_HAIKU_4_5,
            "claude-opus-4.6": cls.CLAUDE_OPUS_4_6,
            "gpt-4": cls.GPT_4,
            "gpt-4-turbo": cls.GPT_4_TURBO,
            "gpt-3.5-turbo": cls.GPT_3_5_TURBO,
        }
