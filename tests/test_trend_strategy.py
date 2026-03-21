"""Tests for the trend score trading strategy."""

import numpy as np
import pandas as pd
import pytest

from ai_financial_advisor.analysis.indicators import compute_all_indicators
from ai_financial_advisor.strategies.trend_strategy import (
    Signal,
    TrendScoreStrategy,
    calculate_rolling_trend_scores,
)


def _make_ohlcv(n: int = 60, seed: int = 42) -> pd.DataFrame:
    """Create synthetic OHLCV data for testing."""
    rng = np.random.RandomState(seed)
    dates = pd.bdate_range("2024-01-01", periods=n)
    close = 100 + np.cumsum(rng.randn(n) * 0.5)
    high = close + rng.uniform(0.2, 1.0, n)
    low = close - rng.uniform(0.2, 1.0, n)
    open_ = close + rng.randn(n) * 0.3
    volume = rng.randint(1_000_000, 10_000_000, n).astype(float)

    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )


class TestSignalDataclass:
    def test_signal_fields(self):
        s = Signal(date="2024-01-01", action="buy", score=0.5, price=100.0)
        assert s.action == "buy"
        assert s.score == 0.5
        assert s.price == 100.0

    def test_signal_actions(self):
        for action in ("buy", "sell", "hold"):
            s = Signal(date="2024-01-01", action=action, score=0.0, price=50.0)
            assert s.action == action


class TestCalculateRollingTrendScores:
    def test_returns_series(self):
        df = compute_all_indicators(_make_ohlcv(60))
        scores = calculate_rolling_trend_scores(df)
        assert isinstance(scores, pd.Series)
        assert len(scores) > 0

    def test_too_few_rows_returns_empty(self):
        df = _make_ohlcv(10)
        scores = calculate_rolling_trend_scores(df)
        assert len(scores) == 0

    def test_scores_in_valid_range(self):
        df = compute_all_indicators(_make_ohlcv(80))
        scores = calculate_rolling_trend_scores(df)
        assert (scores >= -1.0).all() and (scores <= 1.0).all()

    def test_custom_window(self):
        df = compute_all_indicators(_make_ohlcv(60))
        scores_5 = calculate_rolling_trend_scores(df, window=5)
        scores_10 = calculate_rolling_trend_scores(df, window=10)
        assert len(scores_5) > 0
        assert len(scores_10) > 0


class TestTrendScoreStrategy:
    def test_generate_signals_returns_list(self):
        df = _make_ohlcv(60)
        strategy = TrendScoreStrategy()
        signals = strategy.generate_signals(df)
        assert isinstance(signals, list)
        assert all(isinstance(s, Signal) for s in signals)

    def test_all_actions_valid(self):
        df = _make_ohlcv(60)
        strategy = TrendScoreStrategy()
        signals = strategy.generate_signals(df)
        for s in signals:
            assert s.action in ("buy", "sell", "hold")

    def test_custom_thresholds(self):
        df = _make_ohlcv(80)
        # Very tight thresholds → more buy/sell signals
        tight = TrendScoreStrategy(buy_threshold=0.05, sell_threshold=-0.05)
        signals_tight = tight.generate_signals(df)

        # Very loose thresholds → more hold signals
        loose = TrendScoreStrategy(buy_threshold=0.9, sell_threshold=-0.9)
        signals_loose = loose.generate_signals(df)

        holds_tight = sum(1 for s in signals_tight if s.action == "hold")
        holds_loose = sum(1 for s in signals_loose if s.action == "hold")
        assert holds_loose >= holds_tight

    def test_signals_have_prices(self):
        df = _make_ohlcv(60)
        strategy = TrendScoreStrategy()
        signals = strategy.generate_signals(df)
        for s in signals:
            assert s.price > 0

    def test_signals_chronological(self):
        df = _make_ohlcv(60)
        strategy = TrendScoreStrategy()
        signals = strategy.generate_signals(df)
        dates = [pd.Timestamp(s.date) for s in signals]
        assert dates == sorted(dates)

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
        strategy = TrendScoreStrategy()
        signals = strategy.generate_signals(df)
        assert signals == []
