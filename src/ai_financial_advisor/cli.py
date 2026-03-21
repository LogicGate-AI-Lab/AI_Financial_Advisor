"""CLI entry point for the AI Financial Advisor.

Usage:
    ai-advisor news run --lang en
    ai-advisor stock score AAPL
    ai-advisor stock scan "AAPL,MSFT,NVDA"
    ai-advisor analyze --report data/reports/NR_2025-07-11.md
    ai-advisor web launch
    ai-advisor config show
"""

import logging
from datetime import date, timedelta
from typing import Optional

import typer

app = typer.Typer(
    name="ai-advisor",
    help="AI Financial Advisor — data-driven investment insights.",
    no_args_is_help=True,
)

news_app = typer.Typer(help="News agent commands.")
stock_app = typer.Typer(help="Stock analysis commands.")
config_app = typer.Typer(help="Configuration management.")
web_app = typer.Typer(help="Web interface commands.")

app.add_typer(news_app, name="news")
app.add_typer(stock_app, name="stock")
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
    target_date: Optional[str] = typer.Option(None, "--date", "-d", help="Report date (YYYY-MM-DD). Default: yesterday."),
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

    typer.echo(f"\n{'='*40}")
    typer.echo(f"  {result.symbol} Trend Analysis")
    typer.echo(f"{'='*40}")
    typer.echo(f"  Latest Close:  ${result.latest_close:.2f}")
    typer.echo(f"  Trend Score:   {result.trend.score:+.4f}")
    typer.echo(f"  Interpretation: {result.trend.interpretation}")
    typer.echo(f"  MACD Signal:   {result.trend.macd_signal:+.4f}")
    typer.echo(f"  MFI Signal:    {result.trend.mfi_signal:+.4f}")
    typer.echo(f"  OBV Signal:    {result.trend.obv_signal:+.4f}")
    typer.echo(f"{'='*40}\n")


@stock_app.command("scan")
def stock_scan(
    symbols: str = typer.Argument(
        "AAPL,MSFT,AMZN,GOOG,TSLA,NVDA,META,JPM,NFLX,DIS",
        help="Comma-separated list of ticker symbols.",
    ),
    period: str = typer.Option("1y", "--period", "-p", help="Data period."),
) -> None:
    """Scan multiple stocks and rank by trend score."""
    from .agents.stock_agent import StockAgent

    _setup_logging("WARNING")

    agent = StockAgent()
    symbol_list = [s.strip() for s in symbols.split(",")]
    results = agent.analyze_multiple(symbol_list, period=period)

    # Sort by score descending
    results.sort(key=lambda r: r.trend.score, reverse=True)

    typer.echo(f"\n{'Symbol':<8} {'Close':>10} {'Score':>8} {'Signal':<10}")
    typer.echo("-" * 40)
    for r in results:
        typer.echo(
            f"{r.symbol:<8} ${r.latest_close:>9.2f} {r.trend.score:>+7.4f} {r.trend.interpretation:<10}"
        )
    typer.echo()


@config_app.command("show")
def config_show() -> None:
    """Display current configuration (API keys are masked)."""
    from .config import get_settings

    settings = get_settings()

    def mask(key: str) -> str:
        if not key or len(key) < 8:
            return "***" if key else "(not set)"
        return key[:4] + "..." + key[-4:]

    typer.echo(f"\n{'='*40}")
    typer.echo("  AI Financial Advisor Configuration")
    typer.echo(f"{'='*40}")
    typer.echo(f"  LLM Provider:  {settings.llm.provider.value}")
    typer.echo(f"  LLM Model:     {settings.llm.model}")
    typer.echo(f"  LLM Base URL:  {settings.llm.base_url or '(default)'}")
    typer.echo(f"  LLM API Key:   {mask(settings.llm.api_key)}")
    typer.echo(f"  NewsAPI Key:   {mask(settings.news_api.api_key)}")
    typer.echo(f"  Storage:       {settings.storage.backend.value}")
    typer.echo(f"  Reports Dir:   {settings.storage.reports_dir}")
    typer.echo(f"  Log Level:     {settings.log_level}")
    typer.echo(f"{'='*40}\n")


@app.command("analyze")
def analyze(
    report: str = typer.Option(..., "--report", "-r", help="Path to a news report markdown file."),
    symbols: str = typer.Option(
        "AAPL,MSFT,AMZN,GOOG,NVDA,META,TSLA,JPM",
        "--symbols", "-s", help="Comma-separated stock symbols.",
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

    typer.echo(f"\n{'='*50}")
    typer.echo("  Investment Outlook Report")
    typer.echo(f"{'='*50}\n")
    typer.echo(result.report)


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
