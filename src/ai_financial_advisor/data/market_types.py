"""Market type detection and preset watchlists for global markets."""

from enum import Enum


class MarketType(str, Enum):
    """Supported global market types."""

    US = "us"
    CN = "cn"
    HK = "hk"
    EU = "eu"
    JP = "jp"
    CRYPTO = "crypto"
    FOREX = "forex"
    COMMODITY = "commodity"
    UNKNOWN = "unknown"


# Preset watchlists for each market
WATCHLISTS: dict[MarketType, list[str]] = {
    MarketType.US: [
        "AAPL", "MSFT", "AMZN", "GOOG", "TSLA",
        "NVDA", "META", "JPM", "V", "NFLX",
    ],
    MarketType.CN: [
        "600519.SS",  # 贵州茅台
        "000858.SZ",  # 五粮液
        "601318.SS",  # 中国平安
        "600036.SS",  # 招商银行
        "000333.SZ",  # 美的集团
        "002594.SZ",  # 比亚迪
        "601012.SS",  # 隆基绿能
        "600276.SS",  # 恒瑞医药
        "000001.SZ",  # 平安银行
        "601888.SS",  # 中国中免
    ],
    MarketType.HK: [
        "0700.HK",  # Tencent
        "9988.HK",  # Alibaba
        "0005.HK",  # HSBC
        "1299.HK",  # AIA
        "3690.HK",  # Meituan
        "9999.HK",  # NetEase
        "2318.HK",  # Ping An
        "0941.HK",  # China Mobile
        "1810.HK",  # Xiaomi
        "9618.HK",  # JD.com
    ],
    MarketType.EU: [
        "SAP.DE",   # SAP (Germany)
        "MC.PA",    # LVMH (France)
        "ASML.AS",  # ASML (Netherlands)
        "SIE.DE",   # Siemens (Germany)
        "OR.PA",    # L'Oreal (France)
        "NESN.SW",  # Nestle (Switzerland)
        "NOVO-B.CO",  # Novo Nordisk (Denmark)
        "AZN.L",    # AstraZeneca (UK)
        "SHEL.L",   # Shell (UK)
        "TTE.PA",   # TotalEnergies (France)
    ],
    MarketType.JP: [
        "7203.T",   # Toyota
        "6758.T",   # Sony
        "9984.T",   # SoftBank
        "6861.T",   # Keyence
        "8306.T",   # MUFG
        "6501.T",   # Hitachi
        "9432.T",   # NTT
        "4063.T",   # Shin-Etsu
        "7741.T",   # HOYA
        "6902.T",   # Denso
    ],
    MarketType.CRYPTO: [
        "BTC-USD",  # Bitcoin
        "ETH-USD",  # Ethereum
        "SOL-USD",  # Solana
        "BNB-USD",  # Binance Coin
        "XRP-USD",  # Ripple
        "ADA-USD",  # Cardano
        "DOGE-USD", # Dogecoin
        "AVAX-USD", # Avalanche
        "DOT-USD",  # Polkadot
        "LINK-USD", # Chainlink
    ],
    MarketType.FOREX: [
        "EURUSD=X",  # EUR/USD
        "GBPUSD=X",  # GBP/USD
        "USDJPY=X",  # USD/JPY
        "USDCNY=X",  # USD/CNY
        "USDCAD=X",  # USD/CAD
        "AUDUSD=X",  # AUD/USD
        "USDCHF=X",  # USD/CHF
        "NZDUSD=X",  # NZD/USD
    ],
    MarketType.COMMODITY: [
        "GC=F",   # Gold
        "SI=F",   # Silver
        "CL=F",   # Crude Oil (WTI)
        "BZ=F",   # Brent Crude
        "NG=F",   # Natural Gas
        "HG=F",   # Copper
        "ZC=F",   # Corn
        "ZW=F",   # Wheat
    ],
}

# Currency mapping for display
MARKET_CURRENCIES: dict[MarketType, str] = {
    MarketType.US: "USD",
    MarketType.CN: "CNY",
    MarketType.HK: "HKD",
    MarketType.EU: "EUR",
    MarketType.JP: "JPY",
    MarketType.CRYPTO: "USD",
    MarketType.FOREX: "—",
    MarketType.COMMODITY: "USD",
    MarketType.UNKNOWN: "USD",
}

# Markets where Volume data is not available (skip OBV/MFI)
VOLUME_UNAVAILABLE_MARKETS = {MarketType.FOREX}


def detect_market_type(symbol: str) -> MarketType:
    """Detect market type from a ticker symbol.

    Args:
        symbol: Ticker symbol (e.g., 'AAPL', '600519.SS', 'BTC-USD').

    Returns:
        The detected MarketType.
    """
    s = symbol.upper().strip()

    # Chinese A-shares: ends with .SS (Shanghai) or .SZ (Shenzhen)
    if s.endswith(".SS") or s.endswith(".SZ"):
        return MarketType.CN

    # Hong Kong: ends with .HK
    if s.endswith(".HK"):
        return MarketType.HK

    # Japanese: ends with .T
    if s.endswith(".T"):
        return MarketType.JP

    # European exchanges
    eu_suffixes = (".DE", ".PA", ".AS", ".L", ".SW", ".MI", ".MC", ".CO", ".ST", ".HE")
    if any(s.endswith(suffix) for suffix in eu_suffixes):
        return MarketType.EU

    # Crypto: contains -USD suffix (BTC-USD, ETH-USD, etc.)
    if s.endswith("-USD") and not s.startswith("USD"):
        return MarketType.CRYPTO

    # Forex: ends with =X
    if s.endswith("=X"):
        return MarketType.FOREX

    # Commodity futures: ends with =F
    if s.endswith("=F"):
        return MarketType.COMMODITY

    # Default: US stock (plain symbol like AAPL, MSFT)
    if s.isalpha() and len(s) <= 5:
        return MarketType.US

    return MarketType.UNKNOWN


def get_watchlist(market: MarketType) -> list[str]:
    """Get the preset watchlist for a market.

    Args:
        market: The market type.

    Returns:
        List of ticker symbols for the market.
    """
    return WATCHLISTS.get(market, [])


def get_currency(symbol: str) -> str:
    """Get the display currency for a symbol.

    Args:
        symbol: Ticker symbol.

    Returns:
        Currency code (e.g., 'USD', 'CNY', 'JPY').
    """
    market = detect_market_type(symbol)
    return MARKET_CURRENCIES.get(market, "USD")


def has_volume(symbol: str) -> bool:
    """Check if volume data is available for a symbol.

    Forex pairs typically don't have meaningful volume data.

    Args:
        symbol: Ticker symbol.

    Returns:
        True if volume data is expected to be available.
    """
    return detect_market_type(symbol) not in VOLUME_UNAVAILABLE_MARKETS
