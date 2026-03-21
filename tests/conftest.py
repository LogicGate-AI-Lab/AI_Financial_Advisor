"""Shared test fixtures."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_ohlcv() -> pd.DataFrame:
    """Create a synthetic 60-day OHLCV DataFrame for testing."""
    np.random.seed(42)
    n = 60
    dates = pd.bdate_range(start="2025-01-01", periods=n)

    # Generate a simple uptrend with noise
    base_price = 100 + np.cumsum(np.random.randn(n) * 0.5 + 0.1)

    df = pd.DataFrame(
        {
            "Open": base_price + np.random.randn(n) * 0.3,
            "High": base_price + abs(np.random.randn(n) * 0.5),
            "Low": base_price - abs(np.random.randn(n) * 0.5),
            "Close": base_price,
            "Volume": np.random.randint(1_000_000, 10_000_000, size=n).astype(float),
        },
        index=dates,
    )
    return df


@pytest.fixture
def downtrend_ohlcv() -> pd.DataFrame:
    """Create a synthetic 60-day downtrend OHLCV DataFrame."""
    np.random.seed(123)
    n = 60
    dates = pd.bdate_range(start="2025-01-01", periods=n)

    # Accelerating downtrend: flat start then sharp drop
    drift = np.concatenate([np.zeros(30), np.full(30, -2.0)])
    base_price = 150 + np.cumsum(drift + np.random.randn(n) * 0.1)

    df = pd.DataFrame(
        {
            "Open": base_price + np.random.randn(n) * 0.3,
            "High": base_price + abs(np.random.randn(n) * 0.5),
            "Low": base_price - abs(np.random.randn(n) * 0.5),
            "Close": base_price,
            "Volume": np.random.randint(1_000_000, 10_000_000, size=n).astype(float),
        },
        index=dates,
    )
    return df
