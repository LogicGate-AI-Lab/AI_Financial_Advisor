"""Composite trend score calculation.

The trend score combines MACD momentum, MFI flow, and OBV volume
signals into a single value between -1 (strongly bearish) and
+1 (strongly bullish).

Formula:
    S = w_macd * tanh(H_t / sigma_H)
      + w_mfi  * clip((MFI_t - 50) / 50, -1, 1)
      + w_obv  * tanh((OBV_t - OBV_{t-N}) / |OBV_{t-N}|)
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class TrendScoreResult:
    """Detailed breakdown of the composite trend score."""

    score: float
    macd_signal: float
    mfi_signal: float
    obv_signal: float
    interpretation: str


_DEFAULT_WEIGHTS = {"macd": 0.4, "mfi": 0.3, "obv": 0.3}


def calculate_trend_score(
    df: pd.DataFrame,
    weights: dict[str, float] | None = None,
    macd_std_window: int = 5,
    obv_slope_window: int = 5,
) -> TrendScoreResult:
    """Calculate the composite trend score from pre-computed indicators.

    Args:
        df: DataFrame that already has Histogram, MFI, and OBV columns
            (output of `compute_all_indicators`).
        weights: Dict with 'macd', 'mfi', 'obv' weights (must sum to 1.0).
        macd_std_window: Lookback for MACD histogram normalization.
        obv_slope_window: Lookback for OBV slope calculation.

    Returns:
        TrendScoreResult with the composite score and component signals.
    """
    w = weights or dict(_DEFAULT_WEIGHTS)

    # Check if volume-dependent indicators are available
    has_mfi = "MFI" in df.columns and not df["MFI"].isna().all()
    has_obv = "OBV" in df.columns and not df["OBV"].isna().all()

    # MACD signal: normalized histogram value
    hist = df["Histogram"]
    hist_std = hist.rolling(window=macd_std_window).std().iloc[-1]
    macd_signal = float(np.tanh(hist.iloc[-1] / (hist_std + 1e-9)))

    # MFI signal: rescaled to [-1, 1]
    if has_mfi:
        mfi_last = float(df["MFI"].iloc[-1])
        mfi_signal = float(np.clip((mfi_last - 50) / 50, -1, 1))
    else:
        mfi_signal = 0.0

    # OBV signal: relative change over the lookback window
    if has_obv:
        obv = df["OBV"]
        obv_start = float(obv.iloc[-obv_slope_window])
        obv_signal = float(np.tanh((obv.iloc[-1] - obv_start) / (abs(obv_start) + 1e-9)))
    else:
        obv_signal = 0.0

    # Redistribute weights if volume indicators are missing (e.g., forex)
    if not has_mfi and not has_obv:
        w = {"macd": 1.0, "mfi": 0.0, "obv": 0.0}
    elif not has_mfi:
        w = {
            "macd": w["macd"] + w["mfi"] / 2,
            "mfi": 0.0,
            "obv": w["obv"] + w["mfi"] / 2,
        }
    elif not has_obv:
        w = {
            "macd": w["macd"] + w["obv"] / 2,
            "mfi": w["mfi"] + w["obv"] / 2,
            "obv": 0.0,
        }

    score = w["macd"] * macd_signal + w["mfi"] * mfi_signal + w["obv"] * obv_signal

    if score > 0.3:
        interpretation = "Bullish"
    elif score < -0.3:
        interpretation = "Bearish"
    else:
        interpretation = "Neutral"

    return TrendScoreResult(
        score=round(score, 4),
        macd_signal=round(macd_signal, 4),
        mfi_signal=round(mfi_signal, 4),
        obv_signal=round(obv_signal, 4),
        interpretation=interpretation,
    )
