import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

# Composite score formula (unchanged):
# S = w_macd · tanh(H_t / σ_H)
#   + w_mfi  · (MFI_t − 50) / 50
#   + w_obv  · tanh((OBV_t − OBV_{t−N}) / |OBV_{t−N}|)
# where H_t = latest MACD histogram, σ_H = std of last N histograms,
#       MFI_t = latest MFI, OBV_t = latest OBV, OBV_{t−N} = OBV N days ago.

def download_data(symbol: str,
                  period: str = "1y",
                  interval: str = "1d",
                  filename: str = "UNH_data.csv") -> pd.DataFrame:
    df = yf.download(symbol, period=period, interval=interval)
    df.to_csv(filename)
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df_clean = df.copy()
    df_clean.dropna(inplace=True)
    return df_clean

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
    macd_std_window: int = 5,     # one-week lookback for MACD normalization
    obv_slope_window: int = 5     # one-week lookback for OBV slope
) -> float:
    hist = df['Histogram']
    hist_std = hist.rolling(window=macd_std_window).std().iloc[-1]
    macd_signal = np.tanh(hist.iloc[-1] / (hist_std + 1e-9))

    mfi_last = df['MFI'].iloc[-1]
    mfi_signal = np.clip((mfi_last - 50) / 50, -1, 1)

    obv = df['OBV']
    obv_start = obv.iloc[-obv_slope_window]
    obv_signal = np.tanh((obv.iloc[-1] - obv_start) / (abs(obv_start) + 1e-9))

    score = (
        weights['macd'] * macd_signal +
        weights['mfi']  * mfi_signal +
        weights['obv']  * obv_signal
    )
    return score

def plot_trend_scores(dates, scores):
    plt.figure(figsize=(10, 4))
    plt.plot(dates, scores, marker='o')
    plt.axhline(0, color='gray', linestyle='--')
    plt.title('Composite Trend Score Over Past 30 Trading Days')
    plt.xlabel('Date')
    plt.ylabel('Score (-1 to +1)')
    plt.xticks(rotation=45)
    plt.ylim(-1, 1)
    plt.tight_layout()
    plt.show()

def main():
    symbol = "AMD"

    # 1. Download, clean, and compute indicators
    df = clean_data(download_data(symbol))
    df = calculate_macd(df)
    df = calculate_obv(df)
    df = calculate_mfi(df)

    # 2. Compute composite score for each of the past 30 trading days
    scores = []
    dates = df.index[-30:]
    for current_date in dates:
        df_slice = df.loc[:current_date]
        score = calculate_trend_score(df_slice)
        scores.append(score)

    # 3. Plot the 30-day trend score series
    plot_trend_scores(dates, scores)

if __name__ == "__main__":
    main()
