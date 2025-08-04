# region imports
from AlgorithmImports import *
import pandas as pd
import numpy as np

# Indicator helpers

def calculate_macd(df: pd.DataFrame,
                   fast: int = 12,
                   slow: int = 26,
                   signal: int = 9) -> pd.DataFrame:
    df = df.copy()
    df['EMA_fast']  = df['Close'].ewm(span=fast, adjust=False).mean()
    df['EMA_slow']  = df['Close'].ewm(span=slow, adjust=False).mean()
    df['MACD']      = df['EMA_fast'] - df['EMA_slow']
    df['Signal']    = df['MACD'].ewm(span=signal, adjust=False).mean()
    df['Histogram'] = df['MACD'] - df['Signal']
    return df


def calculate_obv(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    direction = np.sign(df['Close'].diff().fillna(0))
    df['OBV'] = (direction * df['Volume']).cumsum()
    return df


def calculate_mfi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    df = df.copy()
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    rmf = tp * df['Volume']
    direction = np.sign(tp.diff().fillna(0))
    pos_mf = (rmf * (direction > 0)).rolling(window=period).sum()
    neg_mf = (rmf * (direction < 0)).rolling(window=period).sum().abs()
    mfr = pos_mf / (neg_mf + 1e-9)
    df['MFI'] = 100 - (100 / (1 + mfr))
    return df


def calculate_trend_score(
    df: pd.DataFrame,
    weights: dict = {'macd': 0.4, 'mfi': 0.3, 'obv': 0.3},
    macd_std_window: int = 5,
    obv_slope_window: int = 5
) -> float:
    hist     = df['Histogram']
    hist_std = hist.rolling(window=macd_std_window).std().iloc[-1]
    macd_signal = np.tanh(hist.iloc[-1] / (hist_std + 1e-9))

    mfi_last   = df['MFI'].iloc[-1]
    mfi_signal = np.clip((mfi_last - 50) / 50, -1, 1)

    obv        = df['OBV']
    obv_start  = obv.iloc[-obv_slope_window]
    obv_signal = np.tanh((obv.iloc[-1] - obv_start) / (abs(obv_start) + 1e-9))

    return (
        weights['macd'] * macd_signal +
        weights['mfi']  * mfi_signal +
        weights['obv']  * obv_signal
    )

class CompositeTrendStrategy(QCAlgorithm):
    def Initialize(self):
        # backtest from fixed dates
        self.SetStartDate(2020, 2, 4)
        self.SetEndDate(2025, 8, 4)
        self.SetCash(100000)

        # portfolio of symbols with max 10% each
        self.symbols = [
            "AAPL","MSFT","AMZN","GOOG","TSLA",
            "NVDA","META","JPM","NFLX","DIS"
        ]
        self.equities = [self.AddEquity(t, Resolution.Daily).Symbol for t in self.symbols]

    def OnData(self, data: Slice):
        # fetch 60-day history for all symbols at once
        history = self.History(self.equities, 60, Resolution.Daily)
        if history.empty:
            return

        for symbol in self.equities:
            df = history.loc[symbol]
            if len(df) < 60:
                continue

            df = df.rename(columns={
                'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'
            })

            # compute indicators and score
            macd_df = calculate_macd(df)
            obv_df  = calculate_obv(macd_df)
            full_df = calculate_mfi(obv_df)
            score   = calculate_trend_score(full_df)

            # grab unrealized profit
            holding = self.Portfolio[symbol]
            unrealized = holding.UnrealizedProfit

            # 1) if score > 0, buy up to 10% of portfolio
            if score > 0:
                self.SetHoldings(symbol, 0.1)

            # 2) if unrealized > 0 and score < 0, sell all
            elif unrealized > 0 and score < 0:
                self.Liquidate(symbol)

            # 3) if unrealized < 0 and score > 0, bottom-fish (buy up to 10%)
            elif unrealized < 0 and score > 0:
                self.SetHoldings(symbol, 0.1)
