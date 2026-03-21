"""CLI entry point for the AI Financial Advisor.

Usage:
    ai-advisor news run --lang en
    ai-advisor stock score AAPL
    ai-advisor stock scan "AAPL,MSFT,NVDA"
    ai-advisor stock scan --market cn
    ai-advisor stock alerts "AAPL,MSFT,NVDA"
    ai-advisor analyze --report data/reports/NR_2025-07-11.md
    ai-advisor web launch
    ai-advisor config show
"""

import logging
from datetime import date, timedelta

import typer

app = typer.Typer(
    name="ai-advisor",
    help="AI Financial Advisor — data-driven investment insights.",
    no_args_is_help=True,
)

news_app = typer.Typer(help="News agent commands.")
stock_app = typer.Typer(help="Stock analysis commands.")
macro_app = typer.Typer(help="Macroeconomic data commands.")
config_app = typer.Typer(help="Configuration management.")
web_app = typer.Typer(help="Web interface commands.")

backtest_app = typer.Typer(help="Backtesting commands.")
notify_app = typer.Typer(help="Notification commands.")

app.add_typer(news_app, name="news")
app.add_typer(stock_app, name="stock")
app.add_typer(macro_app, name="macro")
app.add_typer(backtest_app, name="backtest")
app.add_typer(notify_app, name="notify")
app.add_typer(config_app, name="config")
app.add_typer(web_app, name="web")


def _setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@news_app.command("run")
def news_run(
    lang: str = typer.Option("en", "--lang", "-l", help="Report language: 'en' or 'cn'."),
    target_date: str | None = typer.Option(None, "--date", "-d", help="Report date (YYYY-MM-DD). Default: yesterday."),
) -> None:
    """Run the full news pipeline: fetch, scrape, analyze, and save report."""
    from .agents.news_agent import NewsAgent
    from .config import get_settings

    settings = get_settings()
    _setup_logging(settings.log_level)

    dt = date.fromisoformat(target_date) if target_date else date.today() - timedelta(days=1)

    agent = NewsAgent(settings)
    result = agent.run(language=lang, target_date=dt)

    if result:
        typer.echo(f"Report saved to: {result}")
    else:
        typer.echo("No report generated. Check logs for details.", err=True)
        raise typer.Exit(code=1)


@stock_app.command("score")
def stock_score(
    symbol: str = typer.Argument(..., help="Stock ticker symbol (e.g., AAPL)."),
    period: str = typer.Option("1y", "--period", "-p", help="Data period (e.g., 1y, 6mo, 3mo)."),
) -> None:
    """Compute the composite trend score for a stock."""
    from .agents.stock_agent import StockAgent

    _setup_logging("INFO")

    agent = StockAgent()
    result = agent.analyze(symbol, period=period)

    typer.echo(f"\n{'=' * 40}")
    typer.echo(f"  {result.symbol} Trend Analysis")
    typer.echo(f"{'=' * 40}")
    typer.echo(f"  Latest Close:  ${result.latest_close:.2f}")
    typer.echo(f"  Trend Score:   {result.trend.score:+.4f}")
    typer.echo(f"  Interpretation: {result.trend.interpretation}")
    typer.echo(f"  MACD Signal:   {result.trend.macd_signal:+.4f}")
    typer.echo(f"  MFI Signal:    {result.trend.mfi_signal:+.4f}")
    typer.echo(f"  OBV Signal:    {result.trend.obv_signal:+.4f}")
    typer.echo(f"{'=' * 40}\n")


@stock_app.command("scan")
def stock_scan(
    symbols: str = typer.Argument(
        None,
        help="Comma-separated list of ticker symbols. Ignored if --market is set.",
    ),
    period: str = typer.Option("1y", "--period", "-p", help="Data period."),
    market: str | None = typer.Option(
        None,
        "--market",
        "-m",
        help="Use preset watchlist: us, cn, hk, eu, jp, crypto, forex, commodity.",
    ),
) -> None:
    """Scan multiple stocks and rank by trend score."""
    from .agents.stock_agent import StockAgent
    from .data.market_types import MarketType, get_watchlist

    _setup_logging("WARNING")

    if market:
        try:
            market_type = MarketType(market.lower())
        except ValueError:
            typer.echo(
                f"Unknown market: {market}. "
                f"Options: {', '.join(m.value for m in MarketType if m != MarketType.UNKNOWN)}",
                err=True,
            )
            raise typer.Exit(code=1)
        symbol_list = get_watchlist(market_type)
        if not symbol_list:
            typer.echo(f"No watchlist for market: {market}", err=True)
            raise typer.Exit(code=1)
        typer.echo(f"Scanning {market_type.value.upper()} market ({len(symbol_list)} symbols)...\n")
    elif symbols:
        symbol_list = [s.strip() for s in symbols.split(",")]
    else:
        symbol_list = [
            "AAPL",
            "MSFT",
            "AMZN",
            "GOOG",
            "TSLA",
            "NVDA",
            "META",
            "JPM",
            "NFLX",
            "DIS",
        ]

    agent = StockAgent()
    results = agent.analyze_multiple(symbol_list, period=period)

    # Sort by score descending
    results.sort(key=lambda r: r.trend.score, reverse=True)

    typer.echo(f"\n{'Symbol':<12} {'Currency':>8} {'Close':>12} {'Score':>8} {'Signal':<10}")
    typer.echo("-" * 54)
    for r in results:
        typer.echo(
            f"{r.symbol:<12} {r.currency:>8} {r.latest_close:>12.2f} "
            f"{r.trend.score:>+7.4f} {r.trend.interpretation:<10}"
        )
    typer.echo()


@stock_app.command("alerts")
def stock_alerts(
    symbols: str = typer.Argument(..., help="Comma-separated list of ticker symbols."),
    days: int = typer.Option(5, "--days", "-d", help="Look back N days for recent anomalies."),
    threshold: float = typer.Option(2.5, "--threshold", "-t", help="Z-score threshold for anomaly detection."),
) -> None:
    """Detect price and volume anomalies for given symbols."""
    from .analysis.anomaly import AnomalyDetector
    from .data.stock_data import download_stock_data

    _setup_logging("WARNING")

    detector = AnomalyDetector(z_threshold=threshold)
    symbol_list = [s.strip() for s in symbols.split(",")]

    all_anomalies = []
    for symbol in symbol_list:
        try:
            df = download_stock_data(symbol, period="6mo")
            anomalies = detector.get_recent_anomalies(df, symbol, days=days)
            all_anomalies.extend(anomalies)
        except Exception as exc:
            typer.echo(f"Warning: Failed to check {symbol}: {exc}", err=True)

    if not all_anomalies:
        typer.echo(f"\nNo anomalies detected in the last {days} days for: {', '.join(symbol_list)}")
        typer.echo()
        return

    all_anomalies.sort(key=lambda a: a.date, reverse=True)

    typer.echo(f"\n{'Date':<12} {'Symbol':<10} {'Type':<15} {'Severity':<10} {'Z-Score':>8}")
    typer.echo("-" * 60)
    for a in all_anomalies:
        typer.echo(f"{a.date!s:<12} {a.symbol:<10} {a.type:<15} {a.severity:<10} {a.z_score:>+7.2f}")
    typer.echo(f"\n{len(all_anomalies)} anomalies found.\n")


@macro_app.command("show")
def macro_show() -> None:
    """Display current macroeconomic indicators from FRED."""
    from .analysis.macro import interpret_macro
    from .config import get_settings
    from .data.macro_data import MacroDataFetcher

    settings = get_settings()
    _setup_logging(settings.log_level)

    if not settings.fred.enabled or not settings.fred.api_key:
        typer.echo(
            "FRED is not configured. Set FRED_API_KEY and FRED_ENABLED=true in .env",
            err=True,
        )
        raise typer.Exit(code=1)

    fetcher = MacroDataFetcher(api_key=settings.fred.api_key)
    snapshot = fetcher.fetch_snapshot()
    context = interpret_macro(snapshot)

    typer.echo(f"\n{'=' * 50}")
    typer.echo("  Macroeconomic Dashboard")
    typer.echo(f"{'=' * 50}")
    typer.echo(f"  As of:              {snapshot.as_of}")
    typer.echo(f"  Economic Regime:    {context.regime.upper()}")
    typer.echo(
        f"  GDP Growth:         {snapshot.gdp_growth:+.2f}%"
        if snapshot.gdp_growth is not None
        else "  GDP Growth:         N/A"
    )
    typer.echo(
        f"  CPI (YoY):          {snapshot.cpi_yoy:.2f}%"
        if snapshot.cpi_yoy is not None
        else "  CPI (YoY):          N/A"
    )
    typer.echo(
        f"  Unemployment:       {snapshot.unemployment:.1f}%"
        if snapshot.unemployment is not None
        else "  Unemployment:       N/A"
    )
    typer.echo(
        f"  Fed Funds Rate:     {snapshot.fed_funds:.2f}%"
        if snapshot.fed_funds is not None
        else "  Fed Funds Rate:     N/A"
    )
    typer.echo(
        f"  10Y Treasury:       {snapshot.treasury_10y:.2f}%"
        if snapshot.treasury_10y is not None
        else "  10Y Treasury:       N/A"
    )
    typer.echo(
        f"  2Y Treasury:        {snapshot.treasury_2y:.2f}%"
        if snapshot.treasury_2y is not None
        else "  2Y Treasury:        N/A"
    )
    typer.echo(
        f"  Yield Curve (10-2): {snapshot.yield_curve_spread:+.2f}%"
        if snapshot.yield_curve_spread is not None
        else "  Yield Curve:        N/A"
    )
    typer.echo(f"{'=' * 50}")
    typer.echo(f"  Inflation:          {context.inflation_trend}")
    typer.echo(f"  Rate Environment:   {context.rate_environment}")
    typer.echo(f"  Yield Curve Signal: {context.yield_curve_signal}")
    typer.echo(f"{'=' * 50}\n")
    typer.echo(f"  {context.summary}\n")


@config_app.command("show")
def config_show() -> None:
    """Display current configuration (API keys are masked)."""
    from .config import get_settings

    settings = get_settings()

    def mask(key: str) -> str:
        if not key or len(key) < 8:
            return "***" if key else "(not set)"
        return key[:4] + "..." + key[-4:]

    typer.echo(f"\n{'=' * 40}")
    typer.echo("  AI Financial Advisor Configuration")
    typer.echo(f"{'=' * 40}")
    typer.echo(f"  LLM Provider:  {settings.llm.provider.value}")
    typer.echo(f"  LLM Model:     {settings.llm.model}")
    typer.echo(f"  LLM Base URL:  {settings.llm.base_url or '(default)'}")
    typer.echo(f"  LLM API Key:   {mask(settings.llm.api_key)}")
    typer.echo(f"  NewsAPI Key:   {mask(settings.news_api.api_key)}")
    typer.echo(f"  Storage:       {settings.storage.backend.value}")
    typer.echo(f"  Reports Dir:   {settings.storage.reports_dir}")
    typer.echo(f"  Log Level:     {settings.log_level}")
    typer.echo(f"{'=' * 40}\n")


@app.command("analyze")
def analyze(
    report: str = typer.Option(..., "--report", "-r", help="Path to a news report markdown file."),
    symbols: str = typer.Option(
        "AAPL,MSFT,AMZN,GOOG,NVDA,META,TSLA,JPM",
        "--symbols",
        "-s",
        help="Comma-separated stock symbols.",
    ),
    period: str = typer.Option("6mo", "--period", "-p", help="Stock data period."),
) -> None:
    """Run the analyst agent: combine news sentiment + stock trends into investment advice."""
    from pathlib import Path

    from .agents.analyst_agent import AnalystAgent
    from .config import get_settings

    settings = get_settings()
    _setup_logging(settings.log_level)

    report_path = Path(report)
    if not report_path.exists():
        typer.echo(f"Report file not found: {report}", err=True)
        raise typer.Exit(code=1)

    report_text = report_path.read_text(encoding="utf-8")
    symbol_list = [s.strip() for s in symbols.split(",")]

    agent = AnalystAgent(settings)
    result = agent.run(news_report=report_text, symbols=symbol_list, period=period)

    typer.echo(f"\n{'=' * 50}")
    typer.echo("  Investment Outlook Report")
    typer.echo(f"{'=' * 50}\n")
    typer.echo(result.report)


@backtest_app.command("run")
def backtest_run(
    symbol: str = typer.Argument(..., help="Stock ticker symbol (e.g., AAPL)."),
    period: str = typer.Option("2y", "--period", "-p", help="Data period (e.g., 2y, 1y, 6mo)."),
    buy_threshold: float = typer.Option(0.3, "--buy", "-b", help="Buy threshold for trend score."),
    sell_threshold: float = typer.Option(-0.3, "--sell", "-s", help="Sell threshold for trend score."),
    capital: float = typer.Option(100000, "--capital", "-c", help="Initial capital."),
) -> None:
    """Run a backtest on a single symbol using the trend score strategy."""
    from .data.stock_data import download_stock_data
    from .strategies.backtester import Backtester
    from .strategies.trend_strategy import TrendScoreStrategy

    _setup_logging("WARNING")

    typer.echo(f"Backtesting {symbol} over {period}...")
    df = download_stock_data(symbol, period=period)

    strategy = TrendScoreStrategy(buy_threshold=buy_threshold, sell_threshold=sell_threshold)
    signals = strategy.generate_signals(df)

    if not signals:
        typer.echo("Not enough data to generate signals.", err=True)
        raise typer.Exit(code=1)

    bt = Backtester(initial_capital=capital)
    result = bt.run(signals, symbol=symbol, period=period)

    typer.echo(f"\n{'=' * 45}")
    typer.echo(f"  {result.symbol} Backtest Results ({result.period})")
    typer.echo(f"{'=' * 45}")
    typer.echo(f"  Initial Capital:    ${result.initial_capital:,.2f}")
    typer.echo(f"  Final Value:        ${result.final_value:,.2f}")
    typer.echo(f"  Total Return:       {result.total_return:+.2f}%")
    typer.echo(f"  Annualized Return:  {result.annualized_return:+.2f}%")
    typer.echo(f"  Sharpe Ratio:       {result.sharpe_ratio:.4f}")
    typer.echo(f"  Max Drawdown:       {result.max_drawdown:.2f}%")
    typer.echo(f"  Win Rate:           {result.win_rate:.1f}%")
    typer.echo(f"  Total Trades:       {result.total_trades}")
    typer.echo(f"{'=' * 45}")

    if result.trades:
        typer.echo(f"\n  {'Buy Date':<12} {'Buy $':>10} {'Sell Date':<12} {'Sell $':>10} {'Return':>8} {'Days':>5}")
        typer.echo(f"  {'-' * 60}")
        for t in result.trades:
            typer.echo(
                f"  {str(t.buy_date)[:10]:<12} {t.buy_price:>10.2f} "
                f"{str(t.sell_date)[:10]:<12} {t.sell_price:>10.2f} "
                f"{t.return_pct:>+7.2f}% {t.holding_days:>5}"
            )
    typer.echo()


@backtest_app.command("scan")
def backtest_scan(
    symbols: str = typer.Argument(..., help="Comma-separated list of ticker symbols."),
    period: str = typer.Option("2y", "--period", "-p", help="Data period."),
    buy_threshold: float = typer.Option(0.3, "--buy", "-b", help="Buy threshold."),
    sell_threshold: float = typer.Option(-0.3, "--sell", "-s", help="Sell threshold."),
    capital: float = typer.Option(100000, "--capital", "-c", help="Initial capital."),
) -> None:
    """Backtest multiple symbols and compare results."""
    from .data.stock_data import download_stock_data
    from .strategies.backtester import Backtester
    from .strategies.trend_strategy import TrendScoreStrategy

    _setup_logging("WARNING")

    symbol_list = [s.strip() for s in symbols.split(",")]
    strategy = TrendScoreStrategy(buy_threshold=buy_threshold, sell_threshold=sell_threshold)
    bt = Backtester(initial_capital=capital)

    results = []
    for sym in symbol_list:
        try:
            df = download_stock_data(sym, period=period)
            signals = strategy.generate_signals(df)
            if signals:
                result = bt.run(signals, symbol=sym, period=period)
                results.append(result)
        except Exception as exc:
            typer.echo(f"Warning: {sym} failed: {exc}", err=True)

    if not results:
        typer.echo("No backtest results generated.", err=True)
        raise typer.Exit(code=1)

    results.sort(key=lambda r: r.total_return, reverse=True)

    typer.echo(
        f"\n{'Symbol':<10} {'Return':>10} {'Annual':>10} {'Sharpe':>8} {'MaxDD':>8} {'WinRate':>8} {'Trades':>7}"
    )
    typer.echo("-" * 65)
    for r in results:
        typer.echo(
            f"{r.symbol:<10} {r.total_return:>+9.2f}% {r.annualized_return:>+9.2f}% "
            f"{r.sharpe_ratio:>8.4f} {r.max_drawdown:>7.2f}% {r.win_rate:>7.1f}% {r.total_trades:>7}"
        )
    typer.echo()


def _get_notifier():
    """Create a Telegram notifier from config settings."""
    from .config import get_settings
    from .notifications.factory import create_notifier

    settings = get_settings()
    if not settings.notify.enabled:
        typer.echo("Notifications are not enabled. Set NOTIFY_ENABLED=true in .env", err=True)
        raise typer.Exit(code=1)
    if not settings.notify.telegram_bot_token or not settings.notify.telegram_chat_id:
        typer.echo(
            "Telegram not configured. Set NOTIFY_TELEGRAM_BOT_TOKEN and NOTIFY_TELEGRAM_CHAT_ID in .env",
            err=True,
        )
        raise typer.Exit(code=1)
    return create_notifier(
        "telegram",
        bot_token=settings.notify.telegram_bot_token,
        chat_id=settings.notify.telegram_chat_id,
    )


@notify_app.command("test")
def notify_test() -> None:
    """Send a test notification to verify Telegram setup."""
    _setup_logging("INFO")
    notifier = _get_notifier()
    ok = notifier.send("This is a test message from AI Financial Advisor.", title="Test Notification")
    if ok:
        typer.echo("Test notification sent successfully.")
    else:
        typer.echo("Failed to send test notification. Check logs.", err=True)
        raise typer.Exit(code=1)


@notify_app.command("digest")
def notify_digest(
    symbols: str = typer.Option(
        "AAPL,MSFT,AMZN,GOOG,NVDA,META,TSLA,JPM",
        "--symbols",
        "-s",
        help="Comma-separated stock symbols.",
    ),
    period: str = typer.Option("6mo", "--period", "-p", help="Data period."),
) -> None:
    """Send a daily market digest via Telegram."""
    from .notifications.alert_manager import AlertManager

    _setup_logging("WARNING")
    notifier = _get_notifier()
    manager = AlertManager(notifier)

    symbol_list = [s.strip() for s in symbols.split(",")]
    ok = manager.send_digest(symbol_list, period=period)

    if ok:
        typer.echo(f"Digest sent for {len(symbol_list)} symbols.")
    else:
        typer.echo("Failed to send digest.", err=True)
        raise typer.Exit(code=1)


@notify_app.command("alerts")
def notify_alerts(
    symbols: str = typer.Argument(..., help="Comma-separated list of ticker symbols."),
    days: int = typer.Option(5, "--days", "-d", help="Look back N days for anomalies."),
    threshold: float = typer.Option(2.5, "--threshold", "-t", help="Z-score threshold."),
) -> None:
    """Detect anomalies and send alerts via Telegram."""
    from .notifications.alert_manager import AlertManager

    _setup_logging("WARNING")
    notifier = _get_notifier()
    manager = AlertManager(notifier)

    symbol_list = [s.strip() for s in symbols.split(",")]
    count = manager.send_alerts(symbol_list, days=days, threshold=threshold)

    if count:
        typer.echo(f"Sent alerts for {count} anomalies.")
    else:
        typer.echo("No anomalies detected. No alerts sent.")


@web_app.command("launch")
def web_launch(
    share: bool = typer.Option(False, "--share", help="Create a public Gradio share link."),
) -> None:
    """Launch the Gradio interactive demo."""
    from .web.gradio_app import create_app

    _setup_logging("INFO")
    app = create_app()
    app.launch(share=share)


if __name__ == "__main__":
    app()
