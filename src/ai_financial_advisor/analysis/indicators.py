"""Technical indicator calculations.

This is the single source of truth for all technical indicators used
across the system — CLI, agents, strategies, and web interfaces all
import from here. No duplication.
"""

import numpy as np
import pandas as pd


def calculate_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """Calculate MACD (Moving Average Convergence Divergence).

    Args:
        df: DataFrame with a 'Close' column.
        fast: Fast EMA period.
        slow: Slow EMA period.
        signal: Signal line EMA period.

    Returns:
        DataFrame with added MACD, Signal, and Histogram columns.
    """
    df = df.copy()
    df["EMA_fast"] = df["Close"].ewm(span=fast, adjust=False).mean()
    df["EMA_slow"] = df["Close"].ewm(span=slow, adjust=False).mean()
    df["MACD"] = df["EMA_fast"] - df["EMA_slow"]
    df["Signal"] = df["MACD"].ewm(span=signal, adjust=False).mean()
    df["Histogram"] = df["MACD"] - df["Signal"]
    return df


def calculate_obv(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate OBV (On-Balance Volume).

    Args:
        df: DataFrame with 'Close' and 'Volume' columns.

    Returns:
        DataFrame with added OBV column.
    """
    df = df.copy()
    direction = np.sign(df["Close"].diff().fillna(0))
    df["OBV"] = (direction * df["Volume"]).cumsum()
    return df


def calculate_mfi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Calculate MFI (Money Flow Index).

    Args:
        df: DataFrame with High, Low, Close, and Volume columns.
        period: Lookback window for the MFI calculation.

    Returns:
        DataFrame with added MFI column (0-100 scale).
    """
    df = df.copy()
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    raw_money_flow = typical_price * df["Volume"]
    direction = np.sign(typical_price.diff().fillna(0))

    positive_flow = (raw_money_flow * (direction > 0)).rolling(window=period).sum()
    negative_flow = (raw_money_flow * (direction < 0)).rolling(window=period).sum().abs()

    money_flow_ratio = positive_flow / (negative_flow + 1e-9)
    df["MFI"] = 100 - (100 / (1 + money_flow_ratio))
    return df


def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute MACD, OBV, and MFI indicators in a single pass.

    Args:
        df: DataFrame with OHLCV columns (Open, High, Low, Close, Volume).

    Returns:
        DataFrame with all indicator columns added.
    """
    df = calculate_macd(df)
    df = calculate_obv(df)
    df = calculate_mfi(df)
    return df
