"""Macroeconomic analysis — interprets FRED data into actionable context.

Pure computation, no side effects. Takes a MacroSnapshot and
produces a MacroContext describing the economic environment.
"""

from dataclasses import dataclass

from ..data.macro_data import MacroSnapshot


@dataclass
class MacroContext:
    """Interpreted macroeconomic environment."""

    regime: str                  # "expansion", "contraction", "transition"
    yield_curve_signal: str      # "normal", "flat", "inverted"
    inflation_trend: str         # "rising", "stable", "falling"
    rate_environment: str        # "tightening", "neutral", "easing"
    summary: str                 # Human-readable summary


def interpret_macro(snapshot: MacroSnapshot) -> MacroContext:
    """Interpret a macroeconomic snapshot into investment context.

    Args:
        snapshot: Raw macroeconomic data.

    Returns:
        MacroContext with regime classification and signals.
    """
    # Economic regime
    if snapshot.gdp_growth is not None:
        if snapshot.gdp_growth > 2.0:
            regime = "expansion"
        elif snapshot.gdp_growth < 0:
            regime = "contraction"
        else:
            regime = "transition"
    else:
        regime = "unknown"

    # Yield curve signal
    if snapshot.yield_curve_spread is not None:
        if snapshot.yield_curve_spread < -0.1:
            yield_curve_signal = "inverted"
        elif snapshot.yield_curve_spread < 0.5:
            yield_curve_signal = "flat"
        else:
            yield_curve_signal = "normal"
    else:
        yield_curve_signal = "unknown"

    # Inflation trend
    if snapshot.cpi_yoy is not None:
        if snapshot.cpi_yoy > 3.5:
            inflation_trend = "rising"
        elif snapshot.cpi_yoy < 2.0:
            inflation_trend = "falling"
        else:
            inflation_trend = "stable"
    else:
        inflation_trend = "unknown"

    # Rate environment
    if snapshot.fed_funds is not None:
        if snapshot.fed_funds > 5.0:
            rate_environment = "tightening"
        elif snapshot.fed_funds < 2.0:
            rate_environment = "easing"
        else:
            rate_environment = "neutral"
    else:
        rate_environment = "unknown"

    # Summary
    parts = []
    if regime != "unknown":
        parts.append(f"Economy in {regime} (GDP: {snapshot.gdp_growth:+.1f}%).")
    if inflation_trend != "unknown":
        parts.append(f"Inflation {inflation_trend} (CPI YoY: {snapshot.cpi_yoy:.1f}%).")
    if rate_environment != "unknown":
        parts.append(f"Rate environment: {rate_environment} (Fed funds: {snapshot.fed_funds:.2f}%).")
    if yield_curve_signal != "unknown":
        parts.append(f"Yield curve: {yield_curve_signal} (10y-2y spread: {snapshot.yield_curve_spread:+.2f}%).")
    if snapshot.unemployment is not None:
        parts.append(f"Unemployment: {snapshot.unemployment:.1f}%.")

    summary = " ".join(parts) if parts else "Insufficient macro data available."

    return MacroContext(
        regime=regime,
        yield_curve_signal=yield_curve_signal,
        inflation_trend=inflation_trend,
        rate_environment=rate_environment,
        summary=summary,
    )
