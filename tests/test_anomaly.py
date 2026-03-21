"""Tests for anomaly detection."""

import numpy as np
import pandas as pd
import pytest

from ai_financial_advisor.analysis.anomaly import Anomaly, AnomalyDetector


@pytest.fixture
def normal_df() -> pd.DataFrame:
    """DataFrame with normal, low-volatility price movement."""
    np.random.seed(42)
    dates = pd.date_range("2025-01-01", periods=60, freq="B")
    close = 100 + np.cumsum(np.random.normal(0, 0.5, 60))
    volume = np.random.normal(1_000_000, 100_000, 60).clip(100_000)
    return pd.DataFrame(
        {"Close": close, "Volume": volume},
        index=dates,
    )


@pytest.fixture
def spike_df() -> pd.DataFrame:
    """DataFrame with a price spike injected."""
    np.random.seed(42)
    dates = pd.date_range("2025-01-01", periods=60, freq="B")
    close = 100 + np.cumsum(np.random.normal(0, 0.5, 60))
    # Inject a huge spike at day 50
    close[50] = close[49] * 1.15  # +15% in one day
    volume = np.random.normal(1_000_000, 100_000, 60).clip(100_000)
    return pd.DataFrame(
        {"Close": close, "Volume": volume},
        index=dates,
    )


@pytest.fixture
def crash_df() -> pd.DataFrame:
    """DataFrame with a price crash injected."""
    np.random.seed(42)
    dates = pd.date_range("2025-01-01", periods=60, freq="B")
    close = 100 + np.cumsum(np.random.normal(0, 0.5, 60))
    close[50] = close[49] * 0.85  # -15% in one day
    volume = np.random.normal(1_000_000, 100_000, 60).clip(100_000)
    return pd.DataFrame(
        {"Close": close, "Volume": volume},
        index=dates,
    )


@pytest.fixture
def volume_surge_df() -> pd.DataFrame:
    """DataFrame with a volume surge injected."""
    np.random.seed(42)
    dates = pd.date_range("2025-01-01", periods=60, freq="B")
    close = 100 + np.cumsum(np.random.normal(0, 0.5, 60))
    volume = np.random.normal(1_000_000, 100_000, 60).clip(100_000)
    volume[50] = 5_000_000  # 5x normal volume
    return pd.DataFrame(
        {"Close": close, "Volume": volume},
        index=dates,
    )


class TestAnomalyDetector:
    def test_no_anomalies_in_normal_data(self, normal_df: pd.DataFrame) -> None:
        detector = AnomalyDetector(z_threshold=3.0)
        anomalies = detector.detect_all(normal_df, "TEST")
        # With a high threshold, normal data should have few or no anomalies
        assert len(anomalies) <= 2

    def test_detects_price_spike(self, spike_df: pd.DataFrame) -> None:
        detector = AnomalyDetector(z_threshold=2.5)
        anomalies = detector.detect_price_anomalies(spike_df, "TEST")
        spike_anomalies = [a for a in anomalies if a.type == "price_spike"]
        assert len(spike_anomalies) >= 1
        assert any(a.z_score > 2.5 for a in spike_anomalies)

    def test_detects_price_crash(self, crash_df: pd.DataFrame) -> None:
        detector = AnomalyDetector(z_threshold=2.5)
        anomalies = detector.detect_price_anomalies(crash_df, "TEST")
        crash_anomalies = [a for a in anomalies if a.type == "price_crash"]
        assert len(crash_anomalies) >= 1
        assert any(a.z_score < -2.5 for a in crash_anomalies)

    def test_detects_volume_surge(self, volume_surge_df: pd.DataFrame) -> None:
        detector = AnomalyDetector(z_threshold=2.5)
        anomalies = detector.detect_volume_anomalies(volume_surge_df, "TEST")
        surge_anomalies = [a for a in anomalies if a.type == "volume_surge"]
        assert len(surge_anomalies) >= 1

    def test_anomaly_has_correct_fields(self, spike_df: pd.DataFrame) -> None:
        detector = AnomalyDetector(z_threshold=2.0)
        anomalies = detector.detect_all(spike_df, "AAPL")
        if anomalies:
            a = anomalies[0]
            assert isinstance(a, Anomaly)
            assert a.symbol == "AAPL"
            assert a.type in (
                "price_spike",
                "price_crash",
                "volume_surge",
                "volume_drop",
            )
            assert a.severity in ("warning", "alert", "critical")
            assert isinstance(a.z_score, float)
            assert isinstance(a.description, str)

    def test_severity_classification(self, spike_df: pd.DataFrame) -> None:
        detector = AnomalyDetector(z_threshold=2.0)
        anomalies = detector.detect_all(spike_df, "TEST")
        for a in anomalies:
            if abs(a.z_score) >= 4.0:
                assert a.severity == "critical"
            elif abs(a.z_score) >= 3.0:
                assert a.severity == "alert"
            else:
                assert a.severity == "warning"

    def test_recent_anomalies_filter(self, spike_df: pd.DataFrame) -> None:
        detector = AnomalyDetector(z_threshold=2.0)
        all_anomalies = detector.detect_all(spike_df, "TEST")
        recent = detector.get_recent_anomalies(spike_df, "TEST", days=5)
        assert len(recent) <= len(all_anomalies)

    def test_no_volume_anomalies_without_volume(self) -> None:
        dates = pd.date_range("2025-01-01", periods=30, freq="B")
        df = pd.DataFrame({"Close": range(100, 130), "Volume": 0}, index=dates)
        detector = AnomalyDetector()
        anomalies = detector.detect_volume_anomalies(df, "FOREX")
        assert len(anomalies) == 0

    def test_results_sorted_by_date_desc(self, spike_df: pd.DataFrame) -> None:
        detector = AnomalyDetector(z_threshold=2.0)
        anomalies = detector.detect_all(spike_df, "TEST")
        if len(anomalies) >= 2:
            dates = [a.date for a in anomalies]
            assert dates == sorted(dates, reverse=True)
