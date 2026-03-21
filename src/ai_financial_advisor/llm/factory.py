"""Factory for creating LLM provider instances from configuration."""

from ..config import LLMProviderType, LLMSettings
from .base import LLMProvider
from .claude_provider import ClaudeProvider
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider


def get_llm(settings: LLMSettings) -> LLMProvider:
    """Create an LLM provider based on the given settings.

    Args:
        settings: LLM configuration from the application settings.

    Returns:
        An initialized LLMProvider ready for use.

    Raises:
        ValueError: If the provider type is not recognized.
    """
    if settings.provider == LLMProviderType.CLAUDE:
        return ClaudeProvider(api_key=settings.api_key, model=settings.model)

    if settings.provider == LLMProviderType.OLLAMA:
        return OllamaProvider(
            model=settings.model,
            **({"base_url": settings.base_url} if settings.base_url else {}),
        )

    if settings.provider == LLMProviderType.OPENAI:
        return OpenAIProvider(
            api_key=settings.api_key,
            model=settings.model,
            base_url=settings.base_url,
        )

    raise ValueError(f"Unknown LLM provider: {settings.provider}")
