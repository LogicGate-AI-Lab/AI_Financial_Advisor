"""Trend score trading strategy — generates buy/sell/hold signals.

Uses the composite trend score from analysis.trend_score to make
trading decisions based on configurable thresholds.
"""

from dataclasses import dataclass

import pandas as pd

from ..analysis.indicators import compute_all_indicators
from ..analysis.trend_score import calculate_trend_score


@dataclass
class Signal:
    """A trading signal at a point in time."""

    date: object  # pd.Timestamp
    action: str   # "buy", "sell", "hold"
    score: float
    price: float


class TrendScoreStrategy:
    """Generates trading signals based on trend score thresholds.

    Args:
        buy_threshold: Score above which to buy (default: 0.3).
        sell_threshold: Score below which to sell (default: -0.3).
    """

    def __init__(
        self,
        buy_threshold: float = 0.3,
        sell_threshold: float = -0.3,
    ) -> None:
        self._buy_threshold = buy_threshold
        self._sell_threshold = sell_threshold

    def generate_signals(self, df: pd.DataFrame) -> list[Signal]:
        """Generate buy/sell/hold signals from OHLCV data.

        Computes rolling trend scores and produces a signal for each day.

        Args:
            df: DataFrame with OHLCV columns.

        Returns:
            List of Signal objects, one per trading day (after warmup).
        """
        df = compute_all_indicators(df)
        scores = calculate_rolling_trend_scores(df)

        signals = []
        for date, score in scores.items():
            price = float(df.loc[date, "Close"])

            if score > self._buy_threshold:
                action = "buy"
            elif score < self._sell_threshold:
                action = "sell"
            else:
                action = "hold"

            signals.append(Signal(date=date, action=action, score=score, price=price))

        return signals


def calculate_rolling_trend_scores(
    df: pd.DataFrame,
    window: int = 5,
) -> pd.Series:
    """Calculate trend scores for each day using a rolling window.

    Args:
        df: DataFrame with indicator columns (MACD, OBV, MFI, etc.).
        window: Minimum rows needed for a valid score.

    Returns:
        Series of trend scores indexed by date.
    """
    # Need at least 30 rows for stable indicators
    min_rows = max(30, window)
    if len(df) < min_rows:
        return pd.Series(dtype=float)

    scores = {}
    for i in range(min_rows, len(df) + 1):
        subset = df.iloc[:i]
        try:
            result = calculate_trend_score(subset)
            scores[df.index[i - 1]] = result.score
        except Exception:
            continue

    return pd.Series(scores)
