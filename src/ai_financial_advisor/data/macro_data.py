"""FRED API client — fetches macroeconomic indicators.

Retrieves GDP growth, CPI, unemployment rate, Fed funds rate,
and Treasury yields from the Federal Reserve Economic Data (FRED) API.
"""

import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MacroSnapshot:
    """Point-in-time macroeconomic data snapshot."""

    gdp_growth: float | None         # GDP growth rate (annualized %)
    cpi_yoy: float | None            # CPI year-over-year change (%)
    unemployment: float | None       # Unemployment rate (%)
    fed_funds: float | None          # Federal funds rate (%)
    treasury_10y: float | None       # 10-year Treasury yield (%)
    treasury_2y: float | None        # 2-year Treasury yield (%)
    yield_curve_spread: float | None  # 10y - 2y spread (%)
    as_of: str = ""                  # Date of latest data


# FRED series IDs
_SERIES = {
    "gdp_growth": "A191RL1Q225SBEA",   # Real GDP growth (quarterly, annualized)
    "cpi_yoy": "CPIAUCSL",              # CPI for All Urban Consumers
    "unemployment": "UNRATE",            # Unemployment Rate
    "fed_funds": "FEDFUNDS",             # Federal Funds Effective Rate
    "treasury_10y": "DGS10",             # 10-Year Treasury Constant Maturity
    "treasury_2y": "DGS2",              # 2-Year Treasury Constant Maturity
}


class MacroDataFetcher:
    """Fetches macroeconomic data from the FRED API.

    Args:
        api_key: FRED API key.
    """

    def __init__(self, api_key: str) -> None:
        from fredapi import Fred
        self._fred = Fred(api_key=api_key)

    def fetch_snapshot(self) -> MacroSnapshot:
        """Fetch the latest values for all macro indicators.

        Returns:
            MacroSnapshot with the most recent available data.
        """
        logger.info("Fetching macroeconomic data from FRED...")

        gdp = self._get_latest(_SERIES["gdp_growth"])
        cpi_raw = self._get_series_yoy(_SERIES["cpi_yoy"])
        unemployment = self._get_latest(_SERIES["unemployment"])
        fed_funds = self._get_latest(_SERIES["fed_funds"])
        treasury_10y = self._get_latest(_SERIES["treasury_10y"])
        treasury_2y = self._get_latest(_SERIES["treasury_2y"])

        spread = None
        if treasury_10y is not None and treasury_2y is not None:
            spread = round(treasury_10y - treasury_2y, 4)

        snapshot = MacroSnapshot(
            gdp_growth=gdp,
            cpi_yoy=cpi_raw,
            unemployment=unemployment,
            fed_funds=fed_funds,
            treasury_10y=treasury_10y,
            treasury_2y=treasury_2y,
            yield_curve_spread=spread,
            as_of=datetime.now().strftime("%Y-%m-%d"),
        )

        logger.info("Macro snapshot: GDP=%.2f%%, CPI=%.2f%%, Unemp=%.2f%%, Fed=%.2f%%",
                     gdp or 0, cpi_raw or 0, unemployment or 0, fed_funds or 0)
        return snapshot

    def _get_latest(self, series_id: str) -> float | None:
        """Get the most recent value for a FRED series."""
        try:
            data = self._fred.get_series(series_id)
            if data is not None and not data.empty:
                val = data.dropna().iloc[-1]
                return round(float(val), 4)
        except Exception as exc:
            logger.warning("Failed to fetch %s: %s", series_id, exc)
        return None

    def _get_series_yoy(self, series_id: str) -> float | None:
        """Get year-over-year percentage change for a FRED series."""
        try:
            data = self._fred.get_series(series_id)
            if data is not None and len(data.dropna()) >= 13:
                clean = data.dropna()
                yoy = (clean.iloc[-1] / clean.iloc[-13] - 1) * 100
                return round(float(yoy), 4)
        except Exception as exc:
            logger.warning("Failed to compute YoY for %s: %s", series_id, exc)
        return None
