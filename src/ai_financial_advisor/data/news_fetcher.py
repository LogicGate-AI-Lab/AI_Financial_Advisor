"""NewsAPI client — fetches top headlines from major financial media."""

import logging
from dataclasses import dataclass
from datetime import datetime

from newsapi import NewsApiClient

from ..config import NewsAPISettings

logger = logging.getLogger(__name__)


@dataclass
class Article:
    """A news article with optional full-text content."""

    title: str
    url: str
    source_name: str
    description: str
    published_at: datetime
    content: str | None = None
    author: str | None = None


class NewsFetcher:
    """Fetches top headlines from NewsAPI.

    Args:
        settings: NewsAPI configuration (API key, sources, etc.).
    """

    def __init__(self, settings: NewsAPISettings) -> None:
        self._settings = settings
        self._client = NewsApiClient(api_key=settings.api_key)

    def fetch_headlines(self) -> list[Article]:
        """Fetch top headlines from configured sources.

        Returns:
            List of Article objects (content not yet populated).
        """
        logger.info(
            "Fetching headlines (sources=%s, page_size=%d)...",
            self._settings.sources[:40] + "...",
            self._settings.page_size,
        )

        response = self._client.get_top_headlines(
            sources=self._settings.sources,
            language=self._settings.language,
            page_size=self._settings.page_size,
        )

        if response.get("status") != "ok":
            logger.error("NewsAPI error: %s", response)
            return []

        articles = []
        for item in response.get("articles", []):
            try:
                published_str = item.get("publishedAt", "")
                published_at = (
                    datetime.fromisoformat(published_str.replace("Z", "+00:00")) if published_str else datetime.now()
                )
                articles.append(
                    Article(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        source_name=item.get("source", {}).get("name", "Unknown"),
                        description=item.get("description", "") or "",
                        published_at=published_at,
                        author=item.get("author"),
                    )
                )
            except (ValueError, KeyError) as exc:
                logger.warning("Skipping malformed article: %s", exc)

        logger.info("Fetched %d articles.", len(articles))
        return articles
