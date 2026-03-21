"""Tests for configuration management."""

from ai_financial_advisor.config import LLMProviderType, Settings, StorageBackend


class TestSettings:
    def test_default_settings_load(self) -> None:
        settings = Settings()
        assert settings.llm.provider == LLMProviderType.OPENAI
        assert settings.storage.backend == StorageBackend.SQLITE
        assert settings.log_level == "INFO"

    def test_llm_defaults(self) -> None:
        settings = Settings()
        assert settings.llm.model == "deepseek-reasoner"
        assert settings.llm.temperature == 0.5
        assert settings.llm.max_tokens == 8192

    def test_news_api_defaults(self) -> None:
        settings = Settings()
        assert "reuters" in settings.news_api.sources
        assert settings.news_api.language == "en"
        assert settings.news_api.page_size == 100

    def test_storage_defaults(self) -> None:
        settings = Settings()
        assert str(settings.storage.sqlite_path).endswith("news.db")
        assert str(settings.storage.reports_dir).endswith("reports")
