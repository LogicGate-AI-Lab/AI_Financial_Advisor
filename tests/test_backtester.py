"""Tests for the backtesting engine."""

import pandas as pd

from ai_financial_advisor.strategies.backtester import (
    Backtester,
    Trade,
)
from ai_financial_advisor.strategies.trend_strategy import Signal


def _make_signals(prices: list[float], actions: list[str]) -> list[Signal]:
    """Create a list of signals from prices and actions."""
    dates = pd.bdate_range("2024-01-01", periods=len(prices))
    return [Signal(date=d, action=a, score=0.0, price=p) for d, a, p in zip(dates, actions, prices)]


class TestTradeDataclass:
    def test_trade_fields(self):
        t = Trade(
            buy_date="2024-01-01",
            buy_price=100.0,
            sell_date="2024-01-10",
            sell_price=110.0,
            return_pct=10.0,
            holding_days=9,
        )
        assert t.return_pct == 10.0
        assert t.holding_days == 9


class TestBacktester:
    def test_empty_signals(self):
        bt = Backtester(initial_capital=100000)
        result = bt.run([], symbol="TEST")
        assert result.total_trades == 0
        assert result.final_value == 100000
        assert result.total_return == 0.0

    def test_single_winning_trade(self):
        signals = _make_signals(
            [100, 100, 110, 110],
            ["hold", "buy", "hold", "sell"],
        )
        bt = Backtester(initial_capital=10000)
        result = bt.run(signals, symbol="WIN")

        assert result.total_trades == 1
        assert result.total_return > 0
        assert result.win_rate == 100.0
        assert result.trades[0].return_pct > 0

    def test_single_losing_trade(self):
        signals = _make_signals(
            [100, 100, 90, 90],
            ["hold", "buy", "hold", "sell"],
        )
        bt = Backtester(initial_capital=10000)
        result = bt.run(signals, symbol="LOSE")

        assert result.total_trades == 1
        assert result.total_return < 0
        assert result.win_rate == 0.0

    def test_multiple_trades(self):
        signals = _make_signals(
            [100, 100, 110, 110, 105, 105, 115, 115],
            ["hold", "buy", "hold", "sell", "hold", "buy", "hold", "sell"],
        )
        bt = Backtester(initial_capital=10000)
        result = bt.run(signals, symbol="MULTI")

        assert result.total_trades == 2
        assert len(result.trades) == 2

    def test_mark_to_market_open_position(self):
        """If still holding at the end, position should be marked to market."""
        signals = _make_signals(
            [100, 100, 120],
            ["hold", "buy", "hold"],
        )
        bt = Backtester(initial_capital=10000)
        result = bt.run(signals, symbol="OPEN")

        # Position is marked to market, so final value reflects the gain
        assert result.final_value > 10000

    def test_hold_only_no_trades(self):
        signals = _make_signals(
            [100, 101, 102, 103],
            ["hold", "hold", "hold", "hold"],
        )
        bt = Backtester(initial_capital=10000)
        result = bt.run(signals, symbol="HOLD")

        assert result.total_trades == 0
        assert result.final_value == 10000

    def test_equity_curve_populated(self):
        signals = _make_signals(
            [100, 100, 110, 110],
            ["hold", "buy", "hold", "sell"],
        )
        bt = Backtester(initial_capital=10000)
        result = bt.run(signals, symbol="EQ")

        assert isinstance(result.equity_curve, pd.Series)
        assert len(result.equity_curve) == len(signals)

    def test_sharpe_ratio_calculated(self):
        signals = _make_signals(
            [100, 100, 105, 110, 108, 112, 112],
            ["hold", "buy", "hold", "hold", "hold", "hold", "sell"],
        )
        bt = Backtester(initial_capital=10000)
        result = bt.run(signals, symbol="SHARPE")

        # With varying equity curve, Sharpe should be non-zero
        assert isinstance(result.sharpe_ratio, float)

    def test_max_drawdown_negative_or_zero(self):
        signals = _make_signals(
            [100, 100, 110, 95, 105, 105],
            ["hold", "buy", "hold", "hold", "hold", "sell"],
        )
        bt = Backtester(initial_capital=10000)
        result = bt.run(signals, symbol="DD")

        assert result.max_drawdown <= 0

    def test_custom_initial_capital(self):
        signals = _make_signals([100, 100, 110, 110], ["hold", "buy", "hold", "sell"])
        bt = Backtester(initial_capital=50000)
        result = bt.run(signals, symbol="CAP")

        assert result.initial_capital == 50000
        assert result.final_value > 50000

    def test_result_metadata(self):
        signals = _make_signals([100], ["hold"])
        bt = Backtester()
        result = bt.run(signals, symbol="META", period="1y")

        assert result.symbol == "META"
        assert result.period == "1y"

    def test_duplicate_buy_signals_ignored(self):
        """Second buy while already holding should be ignored."""
        signals = _make_signals(
            [100, 100, 105, 105, 110, 110],
            ["hold", "buy", "buy", "buy", "hold", "sell"],
        )
        bt = Backtester(initial_capital=10000)
        result = bt.run(signals, symbol="DUP")

        assert result.total_trades == 1

    def test_sell_without_position_ignored(self):
        """Sell signal without a position should be ignored."""
        signals = _make_signals(
            [100, 100, 110],
            ["sell", "sell", "hold"],
        )
        bt = Backtester(initial_capital=10000)
        result = bt.run(signals, symbol="NOSELL")

        assert result.total_trades == 0
        assert result.final_value == 10000
