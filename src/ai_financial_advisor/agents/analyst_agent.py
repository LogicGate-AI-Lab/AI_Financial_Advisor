"""Analyst Agent — the system's 'brain' that synthesizes all signals.

Combines news sentiment analysis with stock technical trend scores
to produce comprehensive investment outlook reports.
"""

import logging
from dataclasses import dataclass

from jinja2 import Environment, PackageLoader

from ..analysis.sentiment import SentimentResult, analyze_sentiment
from ..config import Settings
from ..llm import LLMProvider, get_llm
from .stock_agent import StockAgent, StockAnalysis

logger = logging.getLogger(__name__)

_PROMPT_ENV = Environment(
    loader=PackageLoader("ai_financial_advisor.agents", "prompts"),
    trim_blocks=True,
    lstrip_blocks=True,
)


@dataclass
class AnalystReport:
    """Complete analyst report with all source data."""

    report: str
    sentiment: SentimentResult
    stocks: list[StockAnalysis]


class AnalystAgent:
    """Synthesizes news sentiment and stock technicals into investment advice.

    This is the core 'decision engine' of the system. It:
    1. Takes a news report and extracts structured sentiment
    2. Analyzes a set of stocks for technical trend scores
    3. Feeds both into an LLM to produce an investment outlook

    Args:
        settings: Application settings.
        llm: Optional pre-configured LLM provider.
    """

    def __init__(self, settings: Settings, llm: LLMProvider | None = None) -> None:
        self._settings = settings
        self._llm = llm or get_llm(settings.llm)
        self._stock_agent = StockAgent()

    def run(
        self,
        news_report: str,
        symbols: list[str] | None = None,
        period: str = "6mo",
    ) -> AnalystReport:
        """Run the full analyst pipeline.

        Args:
            news_report: The news report text (markdown).
            symbols: Stock symbols to analyze. Defaults to a core watchlist.
            period: Historical data period for stock analysis.

        Returns:
            AnalystReport with the investment outlook.
        """
        if symbols is None:
            symbols = ["AAPL", "MSFT", "AMZN", "GOOG", "NVDA", "META", "TSLA", "JPM", "NFLX", "DIS"]

        # Step 1: Extract sentiment from news
        logger.info("Step 1: Analyzing news sentiment...")
        sentiment = analyze_sentiment(news_report, self._llm)

        # Step 2: Compute stock trend scores
        logger.info("Step 2: Computing trend scores for %d stocks...", len(symbols))
        stocks = self._stock_agent.analyze_multiple(symbols, period=period)

        # Step 3: Generate investment outlook
        logger.info("Step 3: Generating investment outlook report...")
        template = _PROMPT_ENV.get_template("analyst_report.j2")
        prompt = template.render(sentiment=sentiment, stocks=stocks)

        response = self._llm.complete(
            messages=[
                {"role": "system", "content": "You are a senior investment analyst providing data-driven portfolio recommendations."},
                {"role": "user", "content": prompt},
            ],
            temperature=self._settings.llm.temperature,
            max_tokens=self._settings.llm.max_tokens,
        )

        logger.info("Analyst report generated (%d chars).", len(response.content))

        return AnalystReport(
            report=response.content,
            sentiment=sentiment,
            stocks=stocks,
        )
