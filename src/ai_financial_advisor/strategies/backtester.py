"""Backtesting engine — simulates strategy execution on historical data.

Takes trading signals and simulates portfolio performance including
total return, Sharpe ratio, max drawdown, and win rate.
"""

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .trend_strategy import Signal

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """A completed round-trip trade."""

    buy_date: object
    buy_price: float
    sell_date: object
    sell_price: float
    return_pct: float
    holding_days: int


@dataclass
class BacktestResult:
    """Complete backtesting results."""

    symbol: str
    period: str
    initial_capital: float
    final_value: float
    total_return: float  # as percentage
    annualized_return: float  # as percentage
    sharpe_ratio: float
    max_drawdown: float  # as percentage (negative)
    win_rate: float  # as percentage
    total_trades: int
    trades: list[Trade]
    equity_curve: pd.Series  # daily portfolio value


class Backtester:
    """Simulates trading strategy execution on historical data.

    Args:
        initial_capital: Starting portfolio value (default: 100000).
    """

    def __init__(self, initial_capital: float = 100000) -> None:
        self._initial_capital = initial_capital

    def run(
        self,
        signals: list[Signal],
        symbol: str = "",
        period: str = "",
    ) -> BacktestResult:
        """Execute a backtest from a list of trading signals.

        Simple model: all-in on buy, all-out on sell, no partial positions.

        Args:
            signals: List of Signal objects (must be chronologically ordered).
            symbol: Symbol name for the result.
            period: Period description for the result.

        Returns:
            BacktestResult with performance metrics.
        """
        capital = self._initial_capital
        shares = 0.0
        buy_price = 0.0
        buy_date = None
        trades: list[Trade] = []
        equity_values: dict = {}

        for signal in signals:
            if signal.action == "buy" and shares == 0:
                # Buy: invest all capital
                shares = capital / signal.price
                buy_price = signal.price
                buy_date = signal.date
                capital = 0.0

            elif signal.action == "sell" and shares > 0:
                # Sell: liquidate all shares
                capital = shares * signal.price
                ret = (signal.price - buy_price) / buy_price
                days = (pd.Timestamp(signal.date) - pd.Timestamp(buy_date)).days
                trades.append(
                    Trade(
                        buy_date=buy_date,
                        buy_price=buy_price,
                        sell_date=signal.date,
                        sell_price=signal.price,
                        return_pct=round(ret * 100, 4),
                        holding_days=max(days, 1),
                    )
                )
                shares = 0.0

            # Record equity
            portfolio_value = capital + shares * signal.price
            equity_values[signal.date] = portfolio_value

        # If still holding, mark to market
        if shares > 0 and signals:
            capital = shares * signals[-1].price
            shares = 0.0

        final_value = capital if capital > 0 else self._initial_capital
        equity_curve = pd.Series(equity_values)

        # Metrics
        total_return = (final_value / self._initial_capital - 1) * 100

        # Annualized return
        if len(signals) >= 2:
            days = (pd.Timestamp(signals[-1].date) - pd.Timestamp(signals[0].date)).days
            years = max(days / 365.25, 0.01)
            annualized = ((final_value / self._initial_capital) ** (1 / years) - 1) * 100
        else:
            annualized = 0.0

        # Sharpe ratio (daily returns)
        sharpe = 0.0
        if len(equity_curve) > 1:
            daily_returns = equity_curve.pct_change().dropna()
            if daily_returns.std() > 0:
                sharpe = float(daily_returns.mean() / daily_returns.std() * np.sqrt(252))

        # Max drawdown
        max_drawdown = 0.0
        if len(equity_curve) > 0:
            peak = equity_curve.expanding().max()
            drawdown = (equity_curve - peak) / peak * 100
            max_drawdown = float(drawdown.min())

        # Win rate
        wins = sum(1 for t in trades if t.return_pct > 0)
        win_rate = (wins / len(trades) * 100) if trades else 0.0

        return BacktestResult(
            symbol=symbol,
            period=period,
            initial_capital=self._initial_capital,
            final_value=round(final_value, 2),
            total_return=round(total_return, 4),
            annualized_return=round(annualized, 4),
            sharpe_ratio=round(sharpe, 4),
            max_drawdown=round(max_drawdown, 4),
            win_rate=round(win_rate, 2),
            total_trades=len(trades),
            trades=trades,
            equity_curve=equity_curve,
        )
