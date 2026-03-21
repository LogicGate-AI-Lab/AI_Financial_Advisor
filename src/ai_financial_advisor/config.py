"""Centralized configuration management using pydantic-settings.

All settings are loaded from environment variables or a .env file.
Switch LLM providers, API keys, and storage backends without changing code.
"""

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProviderType(str, Enum):
    OPENAI = "openai"
    CLAUDE = "claude"
    OLLAMA = "ollama"


class StorageBackend(str, Enum):
    SQLITE = "sqlite"
    GCS = "gcs"


class LLMSettings(BaseSettings):
    """LLM provider configuration.

    Supports OpenAI-compatible APIs (OpenAI, DeepSeek, etc.),
    Anthropic Claude, and local Ollama.
    """

    model_config = SettingsConfigDict(env_prefix="LLM_", env_file=".env", extra="ignore")

    provider: LLMProviderType = LLMProviderType.OPENAI
    model: str = "deepseek-reasoner"
    api_key: str = ""
    base_url: Optional[str] = None
    temperature: float = 0.5
    max_tokens: int = 8192


class NewsAPISettings(BaseSettings):
    """NewsAPI configuration."""

    model_config = SettingsConfigDict(env_prefix="NEWS_API_", env_file=".env", extra="ignore")

    api_key: str = ""
    sources: str = (
        "reuters,bloomberg,the-wall-street-journal,financial-times,"
        "the-economist,business-insider,the-new-york-times,bbc-news,"
        "associated-press,the-washington-post,cnn,abc-news,cbs-news,"
        "nbc-news,the-verge,techcrunch,wired,ars-technica,engadget"
    )
    language: str = "en"
    page_size: int = 100


class StorageSettings(BaseSettings):
    """Data storage configuration."""

    model_config = SettingsConfigDict(env_prefix="STORAGE_", env_file=".env", extra="ignore")

    backend: StorageBackend = StorageBackend.SQLITE
    sqlite_path: Path = Path("data/news.db")
    gcs_bucket: str = ""
    reports_dir: Path = Path("data/reports")


class Settings(BaseSettings):
    """Root application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    llm: LLMSettings = Field(default_factory=LLMSettings)
    news_api: NewsAPISettings = Field(default_factory=NewsAPISettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)

    log_level: str = "INFO"


def get_settings() -> Settings:
    """Create and return the application settings singleton."""
    return Settings()
