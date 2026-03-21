"""Anomaly detection for price and volume data.

Uses Z-score and IQR methods to identify unusual price movements
and volume spikes. Pure computation, no side effects.
"""

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd


@dataclass
class Anomaly:
    """A detected anomaly in price or volume data."""

    date: date
    symbol: str
    type: str          # "price_spike", "price_crash", "volume_surge", "volume_drop"
    severity: str      # "warning", "alert", "critical"
    z_score: float
    description: str


class AnomalyDetector:
    """Detects price and volume anomalies using statistical methods.

    Args:
        z_threshold: Z-score threshold for anomaly detection (default: 2.5).
        lookback: Number of days for rolling statistics (default: 20).
    """

    def __init__(self, z_threshold: float = 2.5, lookback: int = 20) -> None:
        self._z_threshold = z_threshold
        self._lookback = lookback

    def detect_price_anomalies(self, df: pd.DataFrame, symbol: str) -> list[Anomaly]:
        """Detect unusual daily price returns.

        Args:
            df: DataFrame with a 'Close' column and DatetimeIndex.
            symbol: Ticker symbol for the anomaly records.

        Returns:
            List of price anomalies found.
        """
        returns = df["Close"].pct_change().dropna()
        rolling_mean = returns.rolling(window=self._lookback).mean()
        rolling_std = returns.rolling(window=self._lookback).std()

        z_scores = (returns - rolling_mean) / (rolling_std + 1e-9)

        anomalies = []
        for idx, z in z_scores.items():
            z_val = float(z)
            if np.isnan(z_val) or abs(z_val) < self._z_threshold:
                continue

            ret = float(returns.loc[idx])
            dt = idx.date() if hasattr(idx, "date") else idx

            if z_val > 0:
                anomaly_type = "price_spike"
                desc = f"{symbol} surged {ret:+.2%} (z={z_val:+.2f})"
            else:
                anomaly_type = "price_crash"
                desc = f"{symbol} dropped {ret:+.2%} (z={z_val:+.2f})"

            anomalies.append(Anomaly(
                date=dt,
                symbol=symbol,
                type=anomaly_type,
                severity=_classify_severity(abs(z_val), self._z_threshold),
                z_score=round(z_val, 4),
                description=desc,
            ))

        return anomalies

    def detect_volume_anomalies(self, df: pd.DataFrame, symbol: str) -> list[Anomaly]:
        """Detect unusual volume spikes or drops.

        Args:
            df: DataFrame with a 'Volume' column and DatetimeIndex.
            symbol: Ticker symbol.

        Returns:
            List of volume anomalies found.
        """
        if "Volume" not in df.columns or (df["Volume"] <= 0).all():
            return []

        vol = df["Volume"].astype(float)
        rolling_mean = vol.rolling(window=self._lookback).mean()
        rolling_std = vol.rolling(window=self._lookback).std()

        z_scores = (vol - rolling_mean) / (rolling_std + 1e-9)

        anomalies = []
        for idx, z in z_scores.items():
            z_val = float(z)
            if np.isnan(z_val) or abs(z_val) < self._z_threshold:
                continue

            dt = idx.date() if hasattr(idx, "date") else idx
            ratio = float(vol.loc[idx] / (rolling_mean.loc[idx] + 1e-9))

            if z_val > 0:
                anomaly_type = "volume_surge"
                desc = f"{symbol} volume {ratio:.1f}x average (z={z_val:+.2f})"
            else:
                anomaly_type = "volume_drop"
                desc = f"{symbol} volume {ratio:.1f}x average (z={z_val:+.2f})"

            anomalies.append(Anomaly(
                date=dt,
                symbol=symbol,
                type=anomaly_type,
                severity=_classify_severity(abs(z_val), self._z_threshold),
                z_score=round(z_val, 4),
                description=desc,
            ))

        return anomalies

    def detect_all(self, df: pd.DataFrame, symbol: str) -> list[Anomaly]:
        """Run both price and volume anomaly detection.

        Args:
            df: DataFrame with Close (and optionally Volume) columns.
            symbol: Ticker symbol.

        Returns:
            Combined list of anomalies, sorted by date descending.
        """
        anomalies = self.detect_price_anomalies(df, symbol)
        anomalies.extend(self.detect_volume_anomalies(df, symbol))
        anomalies.sort(key=lambda a: a.date, reverse=True)
        return anomalies

    def get_recent_anomalies(
        self, df: pd.DataFrame, symbol: str, days: int = 5
    ) -> list[Anomaly]:
        """Get anomalies from the last N days only.

        Args:
            df: DataFrame with Close/Volume columns.
            symbol: Ticker symbol.
            days: Number of recent days to check.

        Returns:
            Recent anomalies sorted by date descending.
        """
        all_anomalies = self.detect_all(df, symbol)
        if not all_anomalies or df.empty:
            return []

        last_date = df.index[-1]
        if hasattr(last_date, "date"):
            last_date = last_date.date()

        cutoff = pd.Timestamp(last_date) - pd.Timedelta(days=days)
        cutoff_date = cutoff.date()

        return [a for a in all_anomalies if a.date >= cutoff_date]


def _classify_severity(abs_z: float, threshold: float) -> str:
    """Classify anomaly severity based on Z-score magnitude."""
    if abs_z >= threshold * 2:
        return "critical"
    elif abs_z >= threshold * 1.5:
        return "alert"
    return "warning"
