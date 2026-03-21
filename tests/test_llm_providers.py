"""Tests for LLM provider factory and base types."""

from ai_financial_advisor.config import LLMProviderType, LLMSettings
from ai_financial_advisor.llm.base import LLMProvider, LLMResponse
from ai_financial_advisor.llm.factory import get_llm
from ai_financial_advisor.llm.ollama_provider import OllamaProvider
from ai_financial_advisor.llm.openai_provider import OpenAIProvider


class TestLLMResponse:
    def test_response_fields(self) -> None:
        resp = LLMResponse(content="hello", model="test-model")
        assert resp.content == "hello"
        assert resp.model == "test-model"
        assert resp.usage == {}
        assert resp.raw is None


class TestFactory:
    def test_openai_provider(self) -> None:
        settings = LLMSettings(
            provider=LLMProviderType.OPENAI,
            api_key="test-key",
            model="gpt-4o",
        )
        provider = get_llm(settings)
        assert isinstance(provider, OpenAIProvider)
        assert isinstance(provider, LLMProvider)

    def test_ollama_provider(self) -> None:
        settings = LLMSettings(
            provider=LLMProviderType.OLLAMA,
            model="llama3",
        )
        provider = get_llm(settings)
        assert isinstance(provider, OllamaProvider)

    def test_deepseek_via_openai(self) -> None:
        settings = LLMSettings(
            provider=LLMProviderType.OPENAI,
            api_key="sk-deep",
            model="deepseek-reasoner",
            base_url="https://api.deepseek.com",
        )
        provider = get_llm(settings)
        assert isinstance(provider, OpenAIProvider)
        assert "DeepSeek" in provider.name

    def test_provider_name(self) -> None:
        settings = LLMSettings(
            provider=LLMProviderType.OPENAI,
            api_key="key",
            model="gpt-4o",
        )
        provider = get_llm(settings)
        assert "gpt-4o" in provider.name
