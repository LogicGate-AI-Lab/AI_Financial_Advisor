"""Tests for market type detection and watchlists."""

import pytest

from ai_financial_advisor.data.market_types import (
    MarketType,
    detect_market_type,
    get_currency,
    get_watchlist,
    has_volume,
)


class TestDetectMarketType:
    """Test symbol → market type detection."""

    # US stocks
    @pytest.mark.parametrize("symbol", ["AAPL", "MSFT", "TSLA", "NVDA", "JPM"])
    def test_us_stocks(self, symbol: str) -> None:
        assert detect_market_type(symbol) == MarketType.US

    # Chinese A-shares
    @pytest.mark.parametrize("symbol", ["600519.SS", "000858.SZ", "601318.SS", "000001.SZ"])
    def test_cn_stocks(self, symbol: str) -> None:
        assert detect_market_type(symbol) == MarketType.CN

    # Hong Kong stocks
    @pytest.mark.parametrize("symbol", ["0700.HK", "9988.HK", "0005.HK"])
    def test_hk_stocks(self, symbol: str) -> None:
        assert detect_market_type(symbol) == MarketType.HK

    # Japanese stocks
    @pytest.mark.parametrize("symbol", ["7203.T", "6758.T", "9984.T"])
    def test_jp_stocks(self, symbol: str) -> None:
        assert detect_market_type(symbol) == MarketType.JP

    # European stocks
    @pytest.mark.parametrize("symbol", ["SAP.DE", "MC.PA", "ASML.AS", "AZN.L", "NESN.SW"])
    def test_eu_stocks(self, symbol: str) -> None:
        assert detect_market_type(symbol) == MarketType.EU

    # Crypto
    @pytest.mark.parametrize("symbol", ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"])
    def test_crypto(self, symbol: str) -> None:
        assert detect_market_type(symbol) == MarketType.CRYPTO

    # Forex
    @pytest.mark.parametrize("symbol", ["EURUSD=X", "USDJPY=X", "GBPUSD=X"])
    def test_forex(self, symbol: str) -> None:
        assert detect_market_type(symbol) == MarketType.FOREX

    # Commodities
    @pytest.mark.parametrize("symbol", ["GC=F", "CL=F", "SI=F"])
    def test_commodities(self, symbol: str) -> None:
        assert detect_market_type(symbol) == MarketType.COMMODITY

    def test_case_insensitive(self) -> None:
        assert detect_market_type("aapl") == MarketType.US
        assert detect_market_type("btc-usd") == MarketType.CRYPTO

    def test_unknown_long_symbol(self) -> None:
        assert detect_market_type("VERYLONGSYMBOL") == MarketType.UNKNOWN


class TestWatchlists:
    def test_us_watchlist_not_empty(self) -> None:
        wl = get_watchlist(MarketType.US)
        assert len(wl) >= 10

    def test_cn_watchlist_has_a_shares(self) -> None:
        wl = get_watchlist(MarketType.CN)
        assert any(s.endswith(".SS") for s in wl)
        assert any(s.endswith(".SZ") for s in wl)

    def test_crypto_watchlist_has_btc(self) -> None:
        assert "BTC-USD" in get_watchlist(MarketType.CRYPTO)

    def test_unknown_watchlist_empty(self) -> None:
        assert get_watchlist(MarketType.UNKNOWN) == []


class TestCurrency:
    def test_us_currency(self) -> None:
        assert get_currency("AAPL") == "USD"

    def test_cn_currency(self) -> None:
        assert get_currency("600519.SS") == "CNY"

    def test_jp_currency(self) -> None:
        assert get_currency("7203.T") == "JPY"


class TestHasVolume:
    def test_stocks_have_volume(self) -> None:
        assert has_volume("AAPL") is True

    def test_crypto_has_volume(self) -> None:
        assert has_volume("BTC-USD") is True

    def test_forex_no_volume(self) -> None:
        assert has_volume("EURUSD=X") is False
