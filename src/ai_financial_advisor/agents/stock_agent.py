"""Stock Agent — fetches stock data, computes indicators and trend scores."""

import logging
from dataclasses import dataclass

import pandas as pd

from ..analysis.indicators import compute_all_indicators
from ..analysis.trend_score import TrendScoreResult, calculate_trend_score
from ..data.stock_data import download_stock_data

logger = logging.getLogger(__name__)


@dataclass
class StockAnalysis:
    """Complete analysis result for a single stock."""

    symbol: str
    period: str
    latest_close: float
    trend: TrendScoreResult
    data: pd.DataFrame


class StockAgent:
    """Analyzes stock trends using technical indicators.

    Downloads OHLCV data, computes MACD/OBV/MFI indicators,
    and calculates a composite trend score.
    """

    def analyze(
        self,
        symbol: str,
        period: str = "1y",
    ) -> StockAnalysis:
        """Run full analysis on a stock symbol.

        Args:
            symbol: Ticker symbol (e.g., 'AAPL').
            period: Historical data period (e.g., '1y', '6mo').

        Returns:
            StockAnalysis with trend score and indicator data.
        """
        logger.info("Analyzing %s (period=%s)...", symbol, period)

        df = download_stock_data(symbol, period=period)
        df = compute_all_indicators(df)
        trend = calculate_trend_score(df)

        latest_close = float(df["Close"].iloc[-1])

        logger.info(
            "%s analysis complete: close=%.2f, score=%.4f (%s)",
            symbol, latest_close, trend.score, trend.interpretation,
        )

        return StockAnalysis(
            symbol=symbol,
            period=period,
            latest_close=latest_close,
            trend=trend,
            data=df,
        )

    def analyze_multiple(
        self,
        symbols: list[str],
        period: str = "1y",
    ) -> list[StockAnalysis]:
        """Analyze multiple stocks.

        Args:
            symbols: List of ticker symbols.
            period: Historical data period.

        Returns:
            List of StockAnalysis results (skips symbols that fail).
        """
        results = []
        for symbol in symbols:
            try:
                results.append(self.analyze(symbol, period=period))
            except Exception as exc:
                logger.error("Failed to analyze %s: %s", symbol, exc)
        return results
