"""SQLite storage backend."""

import logging
import sqlite3
from pathlib import Path

from ..news_fetcher import Article
from .base import DataStore

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT,
    author TEXT,
    title TEXT NOT NULL,
    description TEXT,
    url TEXT UNIQUE,
    content TEXT,
    published_at DATETIME,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_published_at ON articles (published_at);
"""


class SQLiteStore(DataStore):
    """SQLite-backed article storage with URL deduplication.

    Args:
        db_path: Path to the SQLite database file.
    """

    def __init__(self, db_path: Path | str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.executescript(_SCHEMA)

    def save_articles(self, articles: list[Article]) -> int:
        """Insert articles, skipping duplicates by URL."""
        if not articles:
            return 0

        inserted = 0
        for article in articles:
            try:
                self._conn.execute(
                    """INSERT INTO articles (source_name, author, title, description, url, content, published_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        article.source_name,
                        article.author,
                        article.title,
                        article.description,
                        article.url,
                        article.content,
                        article.published_at.isoformat() if article.published_at else None,
                    ),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                pass  # Duplicate URL, skip

        self._conn.commit()
        logger.info("Saved %d new articles (%d duplicates skipped).", inserted, len(articles) - inserted)
        return inserted

    def get_articles_without_content(self) -> list[Article]:
        """Return articles where content is NULL."""
        cursor = self._conn.execute(
            "SELECT title, url, source_name, description, published_at, content, author "
            "FROM articles WHERE content IS NULL"
        )
        return [
            Article(
                title=row[0],
                url=row[1],
                source_name=row[2],
                description=row[3] or "",
                published_at=row[4],
                content=row[5],
                author=row[6],
            )
            for row in cursor.fetchall()
        ]

    def update_article_content(self, url: str, content: str, author: str) -> None:
        """Update content and author for a given article URL."""
        self._conn.execute(
            "UPDATE articles SET content = ?, author = ? WHERE url = ?",
            (content, author, url),
        )
        self._conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()
