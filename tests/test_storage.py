"""Tests for SQLite storage backend."""

from datetime import datetime
from pathlib import Path

import pytest

from ai_financial_advisor.data.news_fetcher import Article
from ai_financial_advisor.data.storage.sqlite_store import SQLiteStore


@pytest.fixture
def store(tmp_path: Path) -> SQLiteStore:
    return SQLiteStore(tmp_path / "test.db")


@pytest.fixture
def sample_articles() -> list[Article]:
    return [
        Article(
            title="Test Article 1",
            url="https://example.com/1",
            source_name="Reuters",
            description="First article",
            published_at=datetime(2025, 7, 11, 10, 0),
        ),
        Article(
            title="Test Article 2",
            url="https://example.com/2",
            source_name="Bloomberg",
            description="Second article",
            published_at=datetime(2025, 7, 11, 12, 0),
        ),
    ]


class TestSQLiteStore:
    def test_save_and_count(self, store: SQLiteStore, sample_articles: list[Article]) -> None:
        inserted = store.save_articles(sample_articles)
        assert inserted == 2

    def test_deduplication(self, store: SQLiteStore, sample_articles: list[Article]) -> None:
        store.save_articles(sample_articles)
        inserted = store.save_articles(sample_articles)
        assert inserted == 0

    def test_empty_list(self, store: SQLiteStore) -> None:
        inserted = store.save_articles([])
        assert inserted == 0

    def test_get_articles_without_content(self, store: SQLiteStore, sample_articles: list[Article]) -> None:
        store.save_articles(sample_articles)
        no_content = store.get_articles_without_content()
        assert len(no_content) == 2

    def test_update_content(self, store: SQLiteStore, sample_articles: list[Article]) -> None:
        store.save_articles(sample_articles)
        store.update_article_content("https://example.com/1", "Full text here", "Author Name")

        no_content = store.get_articles_without_content()
        assert len(no_content) == 1
