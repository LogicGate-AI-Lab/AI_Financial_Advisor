"""Tests for macroeconomic analysis (pure computation)."""

import pytest

from ai_financial_advisor.analysis.macro import MacroContext, interpret_macro
from ai_financial_advisor.data.macro_data import MacroSnapshot


@pytest.fixture
def expansion_snapshot() -> MacroSnapshot:
    return MacroSnapshot(
        gdp_growth=3.2,
        cpi_yoy=2.5,
        unemployment=3.8,
        fed_funds=4.5,
        treasury_10y=4.2,
        treasury_2y=3.8,
        yield_curve_spread=0.4,
        as_of="2026-03-21",
    )


@pytest.fixture
def contraction_snapshot() -> MacroSnapshot:
    return MacroSnapshot(
        gdp_growth=-1.5,
        cpi_yoy=5.2,
        unemployment=6.1,
        fed_funds=5.5,
        treasury_10y=3.5,
        treasury_2y=4.0,
        yield_curve_spread=-0.5,
        as_of="2026-03-21",
    )


class TestInterpretMacro:
    def test_expansion_regime(self, expansion_snapshot: MacroSnapshot) -> None:
        ctx = interpret_macro(expansion_snapshot)
        assert ctx.regime == "expansion"

    def test_contraction_regime(self, contraction_snapshot: MacroSnapshot) -> None:
        ctx = interpret_macro(contraction_snapshot)
        assert ctx.regime == "contraction"

    def test_transition_regime(self) -> None:
        snap = MacroSnapshot(gdp_growth=1.0, cpi_yoy=2.0, unemployment=4.0,
                             fed_funds=3.0, treasury_10y=3.5, treasury_2y=3.0,
                             yield_curve_spread=0.5)
        ctx = interpret_macro(snap)
        assert ctx.regime == "transition"

    def test_inverted_yield_curve(self, contraction_snapshot: MacroSnapshot) -> None:
        ctx = interpret_macro(contraction_snapshot)
        assert ctx.yield_curve_signal == "inverted"

    def test_normal_yield_curve(self) -> None:
        snap = MacroSnapshot(gdp_growth=2.5, cpi_yoy=2.5, unemployment=4.0,
                             fed_funds=3.0, treasury_10y=4.5, treasury_2y=3.5,
                             yield_curve_spread=1.0)
        ctx = interpret_macro(snap)
        assert ctx.yield_curve_signal == "normal"

    def test_rising_inflation(self, contraction_snapshot: MacroSnapshot) -> None:
        ctx = interpret_macro(contraction_snapshot)
        assert ctx.inflation_trend == "rising"

    def test_stable_inflation(self, expansion_snapshot: MacroSnapshot) -> None:
        ctx = interpret_macro(expansion_snapshot)
        assert ctx.inflation_trend == "stable"

    def test_tightening_rates(self, contraction_snapshot: MacroSnapshot) -> None:
        ctx = interpret_macro(contraction_snapshot)
        assert ctx.rate_environment == "tightening"

    def test_summary_not_empty(self, expansion_snapshot: MacroSnapshot) -> None:
        ctx = interpret_macro(expansion_snapshot)
        assert len(ctx.summary) > 20

    def test_handles_none_values(self) -> None:
        snap = MacroSnapshot(gdp_growth=None, cpi_yoy=None, unemployment=None,
                             fed_funds=None, treasury_10y=None, treasury_2y=None,
                             yield_curve_spread=None)
        ctx = interpret_macro(snap)
        assert ctx.regime == "unknown"
        assert ctx.summary == "Insufficient macro data available."

    def test_returns_macro_context(self, expansion_snapshot: MacroSnapshot) -> None:
        ctx = interpret_macro(expansion_snapshot)
        assert isinstance(ctx, MacroContext)
