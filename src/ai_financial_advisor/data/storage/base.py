"""Abstract storage interface."""

from abc import ABC, abstractmethod

from ..news_fetcher import Article


class DataStore(ABC):
    """Abstract base class for article storage backends."""

    @abstractmethod
    def save_articles(self, articles: list[Article]) -> int:
        """Save articles, returning count of newly inserted rows.

        Duplicate URLs should be silently skipped.
        """

    @abstractmethod
    def get_articles_without_content(self) -> list[Article]:
        """Return articles that haven't been scraped yet (content is NULL)."""

    @abstractmethod
    def update_article_content(self, url: str, content: str, author: str) -> None:
        """Update an article's content and author after scraping."""
