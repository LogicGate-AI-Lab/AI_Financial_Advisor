"""Stock data downloader — OHLCV data via yfinance."""

import logging

import pandas as pd
import yfinance as yf

from .market_types import has_volume

logger = logging.getLogger(__name__)


def download_stock_data(symbol: str, period: str = "1y") -> pd.DataFrame:
    """Download OHLCV data for a stock symbol.

    For assets without meaningful volume data (e.g., forex pairs),
    the Volume column is filled with zeros.

    Args:
        symbol: Ticker symbol (e.g., 'AAPL', '600519.SS', 'BTC-USD').
        period: Data period (e.g., '1y', '6mo', '3mo', '1mo').

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume.

    Raises:
        ValueError: If no data is returned for the symbol.
    """
    logger.info("Downloading %s data (period=%s)...", symbol, period)

    df = yf.download(symbol, period=period, interval="1d", progress=False)

    if df.empty:
        raise ValueError(f"No data returned for {symbol} (period={period})")

    # yfinance may return MultiIndex columns for single ticker; flatten
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # For forex and other volume-less assets, ensure Volume column exists
    if "Volume" not in df.columns or not has_volume(symbol):
        df["Volume"] = 0
        logger.info("Volume data unavailable for %s, set to 0.", symbol)

    # Ensure standard column names
    expected_cols = ["Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns for {symbol}: {missing}")

    logger.info("Downloaded %d rows for %s.", len(df), symbol)
    return df
