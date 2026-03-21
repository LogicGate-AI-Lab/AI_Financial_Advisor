"""Tests for technical indicator calculations."""

import pandas as pd

from ai_financial_advisor.analysis.indicators import (
    calculate_macd,
    calculate_mfi,
    calculate_obv,
    compute_all_indicators,
)


class TestMACD:
    def test_adds_expected_columns(self, sample_ohlcv: pd.DataFrame) -> None:
        result = calculate_macd(sample_ohlcv)
        assert "MACD" in result.columns
        assert "Signal" in result.columns
        assert "Histogram" in result.columns
        assert "EMA_fast" in result.columns
        assert "EMA_slow" in result.columns

    def test_histogram_equals_macd_minus_signal(self, sample_ohlcv: pd.DataFrame) -> None:
        result = calculate_macd(sample_ohlcv)
        diff = (result["MACD"] - result["Signal"] - result["Histogram"]).abs()
        assert diff.max() < 1e-10

    def test_does_not_mutate_input(self, sample_ohlcv: pd.DataFrame) -> None:
        original_cols = list(sample_ohlcv.columns)
        calculate_macd(sample_ohlcv)
        assert list(sample_ohlcv.columns) == original_cols


class TestOBV:
    def test_adds_obv_column(self, sample_ohlcv: pd.DataFrame) -> None:
        result = calculate_obv(sample_ohlcv)
        assert "OBV" in result.columns

    def test_obv_is_cumulative(self, sample_ohlcv: pd.DataFrame) -> None:
        result = calculate_obv(sample_ohlcv)
        # OBV should have the same length as input
        assert len(result["OBV"]) == len(sample_ohlcv)

    def test_does_not_mutate_input(self, sample_ohlcv: pd.DataFrame) -> None:
        original_cols = list(sample_ohlcv.columns)
        calculate_obv(sample_ohlcv)
        assert list(sample_ohlcv.columns) == original_cols


class TestMFI:
    def test_adds_mfi_column(self, sample_ohlcv: pd.DataFrame) -> None:
        result = calculate_mfi(sample_ohlcv)
        assert "MFI" in result.columns

    def test_mfi_range(self, sample_ohlcv: pd.DataFrame) -> None:
        result = calculate_mfi(sample_ohlcv)
        valid_mfi = result["MFI"].dropna()
        assert valid_mfi.min() >= 0
        assert valid_mfi.max() <= 100

    def test_does_not_mutate_input(self, sample_ohlcv: pd.DataFrame) -> None:
        original_cols = list(sample_ohlcv.columns)
        calculate_mfi(sample_ohlcv)
        assert list(sample_ohlcv.columns) == original_cols


class TestComputeAllIndicators:
    def test_adds_all_indicator_columns(self, sample_ohlcv: pd.DataFrame) -> None:
        result = compute_all_indicators(sample_ohlcv)
        expected = {"MACD", "Signal", "Histogram", "EMA_fast", "EMA_slow", "OBV", "MFI"}
        assert expected.issubset(set(result.columns))

    def test_preserves_original_columns(self, sample_ohlcv: pd.DataFrame) -> None:
        result = compute_all_indicators(sample_ohlcv)
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            assert col in result.columns
