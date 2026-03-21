"""News sentiment analysis module.

Extracts structured sentiment data from news articles or reports
using LLM-based analysis. Outputs a sentiment score and per-sector
breakdown that feeds into the analyst agent.
"""

import json
import logging
from dataclasses import dataclass, field

from ..llm.base import LLMProvider

logger = logging.getLogger(__name__)

_SENTIMENT_PROMPT = """\
Analyze the following news report and extract structured sentiment data.

Return a JSON object with exactly this structure (no other text):
{
    "overall_sentiment": "bullish" | "neutral" | "bearish",
    "confidence": 0.0 to 1.0,
    "market_impact_score": -1.0 to 1.0,
    "key_factors": [
        {"factor": "description", "impact": "positive" | "negative" | "neutral"}
    ],
    "sector_sentiment": {
        "technology": -1.0 to 1.0,
        "financials": -1.0 to 1.0,
        "energy": -1.0 to 1.0,
        "healthcare": -1.0 to 1.0,
        "consumer": -1.0 to 1.0
    },
    "affected_tickers": ["AAPL", "MSFT", ...]
}

News report:
---
{report_text}
---
"""


@dataclass
class SectorSentiment:
    """Sentiment scores by sector."""

    technology: float = 0.0
    financials: float = 0.0
    energy: float = 0.0
    healthcare: float = 0.0
    consumer: float = 0.0


@dataclass
class KeyFactor:
    """A single factor affecting market sentiment."""

    factor: str
    impact: str  # "positive", "negative", "neutral"


@dataclass
class SentimentResult:
    """Complete sentiment analysis result."""

    overall_sentiment: str  # "bullish", "neutral", "bearish"
    confidence: float
    market_impact_score: float
    key_factors: list[KeyFactor] = field(default_factory=list)
    sector_sentiment: SectorSentiment = field(default_factory=SectorSentiment)
    affected_tickers: list[str] = field(default_factory=list)


def analyze_sentiment(report_text: str, llm: LLMProvider) -> SentimentResult:
    """Extract structured sentiment data from a news report.

    Args:
        report_text: The news report markdown text.
        llm: LLM provider to use for analysis.

    Returns:
        SentimentResult with overall and per-sector sentiment.
    """
    logger.info("Analyzing sentiment from report (%d chars)...", len(report_text))

    prompt = _SENTIMENT_PROMPT.format(report_text=report_text[:8000])

    response = llm.complete(
        messages=[
            {
                "role": "system",
                "content": "You are a financial sentiment analysis system. Return only valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=2048,
    )

    try:
        # Extract JSON from response (handle markdown code blocks)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        data = json.loads(content)
    except (json.JSONDecodeError, IndexError) as exc:
        logger.warning("Failed to parse sentiment JSON: %s", exc)
        return SentimentResult(
            overall_sentiment="neutral",
            confidence=0.0,
            market_impact_score=0.0,
        )

    key_factors = [KeyFactor(factor=f["factor"], impact=f["impact"]) for f in data.get("key_factors", [])]

    sector_data = data.get("sector_sentiment", {})
    sector_sentiment = SectorSentiment(
        technology=float(sector_data.get("technology", 0)),
        financials=float(sector_data.get("financials", 0)),
        energy=float(sector_data.get("energy", 0)),
        healthcare=float(sector_data.get("healthcare", 0)),
        consumer=float(sector_data.get("consumer", 0)),
    )

    result = SentimentResult(
        overall_sentiment=data.get("overall_sentiment", "neutral"),
        confidence=float(data.get("confidence", 0)),
        market_impact_score=float(data.get("market_impact_score", 0)),
        key_factors=key_factors,
        sector_sentiment=sector_sentiment,
        affected_tickers=data.get("affected_tickers", []),
    )

    logger.info(
        "Sentiment: %s (confidence=%.2f, impact=%.2f)",
        result.overall_sentiment,
        result.confidence,
        result.market_impact_score,
    )
    return result
