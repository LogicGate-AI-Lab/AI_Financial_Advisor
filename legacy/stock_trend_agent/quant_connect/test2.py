# region imports
from AlgorithmImports import *
import pandas as pd
import numpy as np

# Composite Trend Score helpers (unchanged)
def calculate_macd(df, fast=12, slow=26, signal=9):
    df = df.copy()
    df['EMA_fast'] = df['Close'].ewm(span=fast, adjust=False).mean()
    df['EMA_slow'] = df['Close'].ewm(span=slow, adjust=False).mean()
    df['MACD'] = df['EMA_fast'] - df['EMA_slow']
    df['Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
    df['Histogram'] = df['MACD'] - df['Signal']
    return df

def calculate_obv(df):
    df = df.copy()
    direction = np.sign(df['Close'].diff().fillna(0))
    df['OBV'] = (direction * df['Volume']).cumsum()
    return df

def calculate_mfi(df, period=14):
    df = df.copy()
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    rmf = tp * df['Volume']
    direction = np.sign(tp.diff().fillna(0))
    pos_mf = (rmf * (direction > 0)).rolling(window=period).sum()
    neg_mf = (rmf * (direction < 0)).rolling(window=period).sum().abs()
    mfr = pos_mf / (neg_mf + 1e-9)
    df['MFI'] = 100 - (100 / (1 + mfr))
    return df

def calculate_trend_score(df, weights=None, macd_std_window=5, obv_slope_window=5):
    if weights is None:
        weights = {'macd': 0.4, 'mfi': 0.3, 'obv': 0.3}
    hist = df['Histogram']
    hist_std = hist.rolling(window=macd_std_window).std().iloc[-1]
    macd_signal = np.tanh(hist.iloc[-1] / (hist_std + 1e-9))
    mfi_last = df['MFI'].iloc[-1]
    mfi_signal = np.clip((mfi_last - 50) / 50, -1, 1)
    obv = df['OBV']
    obv_start = obv.iloc[-obv_slope_window]
    obv_signal = np.tanh((obv.iloc[-1] - obv_start) / (abs(obv_start) + 1e-9))
    return weights['macd']*macd_signal + weights['mfi']*mfi_signal + weights['obv']*obv_signal

class ValueTrendStrategy(QCAlgorithm):
    def Initialize(self):
        # Backtest period: last 6 months
        self.SetStartDate(2025, 2, 4)
        self.SetEndDate(2025, 8, 4)
        self.SetCash(100000)

        # Universe: quality names
        tickers = ["AAPL","MSFT","AMZN","GOOG","TSLA",
                   "NVDA","META","JPM","NFLX","DIS"]
        self.symbols = [self.AddEquity(t, Resolution.Daily).Symbol for t in tickers]

        # Risk & position parameters
        self.max_weight = 0.10       # max 10% per symbol
        self.cash_reserve = 0.20     # keep 20% uninvested
        self.max_adds = 3           # max averaging down per symbol
        self.profit_take_pct = 0.05 # take profit threshold

        # tracking dictionaries
        self.add_counts = {s: 0 for s in self.symbols}
        self.entry_dates = {}

    def OnData(self, data: Slice):
        # Fetch history once
        history = self.History(self.symbols, 60, Resolution.Daily)
        if history.empty:
            return

        # Calculate total invested and enforce cash reserve
        invested_value = sum([self.Portfolio[s].HoldingsValue for s in self.symbols])
        portfolio_value = self.Portfolio.TotalPortfolioValue
        available_cash_pct = (portfolio_value - invested_value) / portfolio_value

        for symbol in self.symbols:
            df = history.loc[symbol]
            if len(df) < 60: continue
            df = df.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'})
            df = calculate_macd(df)
            df = calculate_obv(df)
            df = calculate_mfi(df)
            score = calculate_trend_score(df)

            holding = self.Portfolio[symbol]
            unrealized = holding.UnrealizedProfit / (holding.AveragePrice * holding.Quantity + 1e-9)

            # 1. Entry or add: score > 0, respect cash reserve and max weight
            if score > 0 and available_cash_pct > self.cash_reserve:
                target = min(self.max_weight, holding.HoldingsValue/portfolio_value + 0.05)
                if holding.Quantity == 0 or (unrealized < 0 and self.add_counts[symbol] < self.max_adds):
                    # initial buy or averaging down
                    self.SetHoldings(symbol, target)
                    self.add_counts[symbol] += (1 if unrealized < 0 else 0)
                    self.entry_dates[symbol] = self.Time.date()

            # 2. Profit-taking: if profit > threshold and score < 0
            if holding.Invested and unrealized > self.profit_take_pct and score < 0:
                # partial take profit: reduce to half position
                current_pct = holding.HoldingsValue/portfolio_value
                self.SetHoldings(symbol, current_pct/2)

            # Enforce minimum hold of one week before full exit
            if symbol in self.entry_dates:
                if (self.Time.date() - self.entry_dates[symbol]).days < 7:
                    continue

            # 3. Exit losing positions: never sell at loss, skip
            # (so no code for selling at loss)

            # Update available cash percentage
            invested_value = sum([self.Portfolio[s].HoldingsValue for s in self.symbols])
            available_cash_pct = (portfolio_value - invested_value) / portfolio_value

