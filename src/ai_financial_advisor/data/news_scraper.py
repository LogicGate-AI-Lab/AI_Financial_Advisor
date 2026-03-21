"""Full-text scraper — extracts article body using newspaper3k."""

import logging
import time

from newspaper import Article as Newspaper3kArticle

from .news_fetcher import Article

logger = logging.getLogger(__name__)

_MIN_CONTENT_LENGTH = 100
_REQUEST_DELAY = 1.0


def scrape_full_text(articles: list[Article]) -> list[Article]:
    """Scrape full-text content for articles that lack it.

    Uses newspaper3k to download and parse each article URL.
    Articles that fail scraping get content set to "SCRAPING_FAILED".

    Args:
        articles: List of articles (content may be None).

    Returns:
        The same list with content populated where possible.
    """
    scraped_count = 0
    failed_count = 0

    for article in articles:
        if article.content:
            continue

        try:
            np_article = Newspaper3kArticle(article.url)
            np_article.download()
            np_article.parse()

            if len(np_article.text) >= _MIN_CONTENT_LENGTH:
                article.content = np_article.text
                if np_article.authors and not article.author:
                    article.author = ", ".join(np_article.authors)
                scraped_count += 1
            else:
                article.content = "SCRAPING_FAILED"
                failed_count += 1
                logger.warning("Content too short for %s", article.url)

        except Exception as exc:
            article.content = "SCRAPING_FAILED"
            failed_count += 1
            logger.warning("Scraping failed for %s: %s", article.url, exc)

        time.sleep(_REQUEST_DELAY)

    logger.info("Scraped %d articles (%d failed).", scraped_count, failed_count)
    return articles
