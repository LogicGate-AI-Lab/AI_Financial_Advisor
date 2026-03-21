"""Gradio interactive demo for AI Financial Advisor.

Provides a web-based interface with two tabs:
- Stock Trend Analyzer: enter a ticker, see trend score + indicator charts
- News Report Browser: view generated reports by date

Launch locally:
    python -m ai_financial_advisor.web.gradio_app

Deploy to Hugging Face Spaces:
    Copy this file + the src/ package to a Space with `gradio` SDK.
"""

import logging
from datetime import date, timedelta

import gradio as gr
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..agents.stock_agent import StockAgent, StockAnalysis
from ..config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stock analysis tab
# ---------------------------------------------------------------------------

_stock_agent = StockAgent()


def analyze_stock(symbol: str, period: str) -> tuple[str, go.Figure | None]:
    """Run stock analysis and return summary text + chart."""
    if not symbol or not symbol.strip():
        return "Please enter a stock symbol.", None

    symbol = symbol.strip().upper()
    try:
        result = _stock_agent.analyze(symbol, period=period)
    except Exception as exc:
        return f"Error analyzing {symbol}: {exc}", None

    summary = _format_summary(result)
    fig = _build_chart(result)
    return summary, fig


def _format_summary(r: StockAnalysis) -> str:
    trend = r.trend
    return (
        f"## {r.symbol} Trend Analysis\n\n"
        f"| Metric | Value |\n"
        f"|--------|-------|\n"
        f"| Latest Close | ${r.latest_close:.2f} |\n"
        f"| **Trend Score** | **{trend.score:+.4f}** |\n"
        f"| Interpretation | {trend.interpretation} |\n"
        f"| MACD Signal | {trend.macd_signal:+.4f} |\n"
        f"| MFI Signal | {trend.mfi_signal:+.4f} |\n"
        f"| OBV Signal | {trend.obv_signal:+.4f} |\n"
    )


def _build_chart(r: StockAnalysis) -> go.Figure:
    df = r.data.tail(90)  # last 90 trading days
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.4, 0.2, 0.2, 0.2],
        subplot_titles=(f"{r.symbol} Price", "MACD", "MFI", "OBV"),
    )

    # Price candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
        ),
        row=1,
        col=1,
    )

    # MACD
    fig.add_trace(
        go.Scatter(x=df.index, y=df["MACD"], name="MACD", line=dict(color="blue")),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df["Signal"], name="Signal", line=dict(color="orange")),
        row=2,
        col=1,
    )
    colors = ["green" if v >= 0 else "red" for v in df["Histogram"]]
    fig.add_trace(
        go.Bar(x=df.index, y=df["Histogram"], name="Histogram", marker_color=colors),
        row=2,
        col=1,
    )

    # MFI
    fig.add_trace(
        go.Scatter(x=df.index, y=df["MFI"], name="MFI", line=dict(color="purple")),
        row=3,
        col=1,
    )
    fig.add_hline(y=80, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=20, line_dash="dash", line_color="green", row=3, col=1)

    # OBV
    fig.add_trace(
        go.Scatter(x=df.index, y=df["OBV"], name="OBV", line=dict(color="teal")),
        row=4,
        col=1,
    )

    fig.update_layout(
        height=900,
        showlegend=False,
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        title_text=f"{r.symbol} Technical Analysis — Score: {r.trend.score:+.4f} ({r.trend.interpretation})",
    )
    return fig


# ---------------------------------------------------------------------------
# News report browser tab
# ---------------------------------------------------------------------------


def browse_report(date_str: str, language: str) -> str:
    """Load a saved report from the reports directory."""
    settings = get_settings()
    reports_dir = settings.storage.reports_dir

    if not reports_dir.exists():
        return "No reports directory found. Run `ai-advisor news run` first."

    suffix = f"_{language.upper()}" if language != "en" else ""
    filename = f"NR_{date_str}{suffix}.md"
    filepath = reports_dir / filename

    if filepath.exists():
        return filepath.read_text(encoding="utf-8")

    # List available reports
    available = sorted(reports_dir.glob("NR_*.md"))
    if available:
        names = "\n".join(f"- {f.name}" for f in available[-10:])
        return f"Report `{filename}` not found.\n\nAvailable reports:\n{names}"
    return "No reports found. Run `ai-advisor news run` to generate one."


# ---------------------------------------------------------------------------
# App assembly
# ---------------------------------------------------------------------------


def create_app() -> gr.Blocks:
    """Build and return the Gradio app."""
    with gr.Blocks(
        title="AI Financial Advisor",
        theme=gr.themes.Soft(),
    ) as app:
        gr.Markdown("# AI Financial Advisor\nData-driven investment insights powered by technical analysis and AI.")

        with gr.Tab("Stock Trend Analyzer"):
            with gr.Row():
                symbol_input = gr.Textbox(
                    label="Stock Symbol",
                    placeholder="e.g., AAPL, MSFT, NVDA",
                    value="AAPL",
                    scale=2,
                )
                period_input = gr.Dropdown(
                    label="Period",
                    choices=["3mo", "6mo", "1y", "2y"],
                    value="6mo",
                    scale=1,
                )
                analyze_btn = gr.Button("Analyze", variant="primary", scale=1)

            summary_output = gr.Markdown()
            chart_output = gr.Plot()

            analyze_btn.click(
                fn=analyze_stock,
                inputs=[symbol_input, period_input],
                outputs=[summary_output, chart_output],
            )

        with gr.Tab("News Report Browser"):
            with gr.Row():
                date_input = gr.Textbox(
                    label="Date (YYYY-MM-DD)",
                    value=(date.today() - timedelta(days=1)).isoformat(),
                    scale=2,
                )
                lang_input = gr.Dropdown(
                    label="Language",
                    choices=["en", "cn"],
                    value="en",
                    scale=1,
                )
                browse_btn = gr.Button("Load Report", variant="primary", scale=1)

            report_output = gr.Markdown()

            browse_btn.click(
                fn=browse_report,
                inputs=[date_input, lang_input],
                outputs=[report_output],
            )

    return app


def main() -> None:
    """Launch the Gradio app."""
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    app.launch()


if __name__ == "__main__":
    main()
