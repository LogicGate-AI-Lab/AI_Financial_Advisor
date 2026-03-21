"""News Agent — end-to-end pipeline from fetching to report generation.

Orchestrates the news fetcher, scraper, and LLM to produce
daily global news reports in English or Chinese.
"""

import logging
from datetime import date, timedelta
from pathlib import Path

from jinja2 import Environment, PackageLoader

from ..config import Settings
from ..data.news_fetcher import Article, NewsFetcher
from ..data.news_scraper import scrape_full_text
from ..llm import LLMProvider, get_llm

logger = logging.getLogger(__name__)

_PROMPT_ENV = Environment(
    loader=PackageLoader("ai_financial_advisor.agents", "prompts"),
    trim_blocks=True,
    lstrip_blocks=True,
)

_SYSTEM_PROMPTS = {
    "en": "You are a senior financial analyst.",
    "cn": "你是一位资深的金融分析师。",
}

_TEMPLATE_MAP = {
    "en": "news_report_en.j2",
    "cn": "news_report_cn.j2",
}


class NewsAgent:
    """Fetches news, scrapes full text, and generates LLM-powered reports.

    Args:
        settings: Application settings.
        llm: Optional pre-configured LLM provider. If None, one is
            created from settings.
    """

    def __init__(self, settings: Settings, llm: LLMProvider | None = None) -> None:
        self._settings = settings
        self._fetcher = NewsFetcher(settings.news_api)
        self._llm = llm or get_llm(settings.llm)

    def fetch_and_scrape(self) -> list[Article]:
        """Fetch headlines and scrape full text content.

        Returns:
            List of articles with content populated.
        """
        articles = self._fetcher.fetch_headlines()
        if not articles:
            logger.warning("No articles fetched.")
            return []
        return scrape_full_text(articles)

    def generate_report(
        self,
        articles: list[Article],
        language: str = "en",
    ) -> str:
        """Generate a news report from articles using the LLM.

        Args:
            articles: List of articles with content.
            language: Report language ('en' or 'cn').

        Returns:
            The generated report as a markdown string.
        """
        # Filter out failed scrapes
        valid_articles = [
            a for a in articles
            if a.content and a.content != "SCRAPING_FAILED"
        ]

        if not valid_articles:
            logger.warning("No valid articles to generate report from.")
            return ""

        logger.info("Generating %s report from %d articles...", language, len(valid_articles))

        template_name = _TEMPLATE_MAP.get(language, _TEMPLATE_MAP["en"])
        template = _PROMPT_ENV.get_template(template_name)
        prompt = template.render(articles=valid_articles)

        system_prompt = _SYSTEM_PROMPTS.get(language, _SYSTEM_PROMPTS["en"])

        response = self._llm.complete(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=self._settings.llm.temperature,
            max_tokens=self._settings.llm.max_tokens,
        )

        logger.info("Report generated (%d chars). Provider: %s", len(response.content), self._llm.name)
        return response.content

    def save_report(self, report: str, target_date: date, language: str = "en") -> Path:
        """Save a report to the configured reports directory.

        Args:
            report: The report content as markdown.
            target_date: The date the report covers.
            language: Language code for the filename suffix.

        Returns:
            Path to the saved report file.
        """
        reports_dir = self._settings.storage.reports_dir
        reports_dir.mkdir(parents=True, exist_ok=True)

        date_str = target_date.strftime("%Y-%m-%d")
        suffix = f"_{language.upper()}" if language != "en" else ""
        filename = f"NR_{date_str}{suffix}.md"
        filepath = reports_dir / filename

        title = {
            "en": f"# Global News Daily Report ({date_str})",
            "cn": f"# 全球重要新闻每日快报 ({date_str})",
        }.get(language, f"# News Report ({date_str})")

        filepath.write_text(f"{title}\n\n{report}", encoding="utf-8")
        logger.info("Report saved to %s", filepath)
        return filepath

    def run(self, language: str = "en", target_date: date | None = None) -> Path | None:
        """Execute the full news pipeline: fetch → scrape → report → save.

        Args:
            language: Report language ('en' or 'cn').
            target_date: Date for the report filename. Defaults to yesterday.

        Returns:
            Path to the saved report, or None if pipeline failed.
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        logger.info("Running news pipeline for %s (%s)...", target_date, language)

        articles = self.fetch_and_scrape()
        if not articles:
            return None

        report = self.generate_report(articles, language=language)
        if not report:
            return None

        return self.save_report(report, target_date, language=language)
