"""Tests for composite trend score calculation."""

import pandas as pd

from ai_financial_advisor.analysis.indicators import compute_all_indicators
from ai_financial_advisor.analysis.trend_score import TrendScoreResult, calculate_trend_score


class TestTrendScore:
    def test_returns_result_dataclass(self, sample_ohlcv: pd.DataFrame) -> None:
        df = compute_all_indicators(sample_ohlcv)
        result = calculate_trend_score(df)
        assert isinstance(result, TrendScoreResult)

    def test_score_in_valid_range(self, sample_ohlcv: pd.DataFrame) -> None:
        df = compute_all_indicators(sample_ohlcv)
        result = calculate_trend_score(df)
        assert -1.0 <= result.score <= 1.0

    def test_component_signals_in_range(self, sample_ohlcv: pd.DataFrame) -> None:
        df = compute_all_indicators(sample_ohlcv)
        result = calculate_trend_score(df)
        assert -1.0 <= result.macd_signal <= 1.0
        assert -1.0 <= result.mfi_signal <= 1.0
        assert -1.0 <= result.obv_signal <= 1.0

    def test_uptrend_gives_positive_score(self, sample_ohlcv: pd.DataFrame) -> None:
        df = compute_all_indicators(sample_ohlcv)
        result = calculate_trend_score(df)
        # sample_ohlcv has a slight uptrend built in, so score should be positive
        assert result.score > 0

    def test_downtrend_gives_negative_score(self, downtrend_ohlcv: pd.DataFrame) -> None:
        df = compute_all_indicators(downtrend_ohlcv)
        result = calculate_trend_score(df)
        assert result.score < 0

    def test_interpretation_matches_score(self, sample_ohlcv: pd.DataFrame) -> None:
        df = compute_all_indicators(sample_ohlcv)
        result = calculate_trend_score(df)
        if result.score > 0.3:
            assert result.interpretation == "Bullish"
        elif result.score < -0.3:
            assert result.interpretation == "Bearish"
        else:
            assert result.interpretation == "Neutral"

    def test_custom_weights(self, sample_ohlcv: pd.DataFrame) -> None:
        df = compute_all_indicators(sample_ohlcv)
        # All weight on MACD
        result = calculate_trend_score(df, weights={"macd": 1.0, "mfi": 0.0, "obv": 0.0})
        assert result.score == result.macd_signal
