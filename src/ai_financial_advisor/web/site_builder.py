"""Site builder — generates a static financial dashboard from reports and market data.

Produces a complete HTML site with:
- Dashboard (index): market summary, latest reports
- Reports: list + individual report pages
- Market: overview table + individual stock pages with charts
"""

import logging
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_ASSETS_DIR = Path(__file__).parent / "assets"


@dataclass
class ReportInfo:
    """Metadata for a news report."""

    title: str
    date: str
    filename: str
    source_path: Path


@dataclass
class StockRow:
    """Summary row for market tables."""

    symbol: str
    currency: str
    close: float
    score: float
    interpretation: str
    macd_signal: float = 0.0
    mfi_signal: float = 0.0
    obv_signal: float = 0.0


class SiteBuilder:
    """Generates a static financial dashboard site.

    Args:
        reports_dir: Directory containing markdown report files.
        output_dir: Directory to write the generated site.
    """

    def __init__(self, reports_dir: Path, output_dir: Path) -> None:
        self._reports_dir = reports_dir
        self._output_dir = output_dir
        self._env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=True,
        )

    def build(self, market_data: dict[str, list[StockRow]] | None = None) -> Path:
        """Build the complete site.

        Args:
            market_data: Optional dict of market_name → list of StockRow.
                If None, market pages are generated as empty.

        Returns:
            Path to the output directory.
        """
        self._output_dir.mkdir(parents=True, exist_ok=True)

        # Copy assets
        self._copy_assets()

        # Scan reports
        reports = self._scan_reports()

        # Build all pages
        self._build_dashboard(reports, market_data)
        self._build_reports(reports)
        self._build_market(market_data)

        logger.info(
            "Site built at %s (%d reports, %d market sections).",
            self._output_dir,
            len(reports),
            len(market_data) if market_data else 0,
        )
        return self._output_dir

    def _copy_assets(self) -> None:
        """Copy CSS and other static assets."""
        assets_out = self._output_dir / "assets"
        assets_out.mkdir(parents=True, exist_ok=True)
        for src_file in _ASSETS_DIR.iterdir():
            if src_file.is_file():
                shutil.copy2(src_file, assets_out / src_file.name)

    def _scan_reports(self) -> list[ReportInfo]:
        """Scan the reports directory for markdown files."""
        reports = []
        if not self._reports_dir.exists():
            return reports

        for md_file in sorted(self._reports_dir.glob("NR_*.md"), reverse=True):
            # Extract date from filename: NR_2026-03-21.md → 2026-03-21
            match = re.search(r"NR_(\d{4}-\d{2}-\d{2})", md_file.name)
            date_str = match.group(1) if match else "Unknown"

            # Extract title from first line
            first_line = md_file.read_text(encoding="utf-8").split("\n", 1)[0]
            title = first_line.lstrip("# ").strip() or f"Report {date_str}"

            html_name = md_file.stem + ".html"
            reports.append(
                ReportInfo(
                    title=title,
                    date=date_str,
                    filename=html_name,
                    source_path=md_file,
                )
            )

        return reports

    def _build_dashboard(
        self,
        reports: list[ReportInfo],
        market_data: dict[str, list[StockRow]] | None,
    ) -> None:
        """Build the main dashboard page."""
        # Flatten market data for the summary table on dashboard
        market_table = []
        market_summary = []
        if market_data:
            for stocks in market_data.values():
                market_table.extend(stocks)
            # Top-level summary: average score per market
            for name, stocks in market_data.items():
                if stocks:
                    avg_score = sum(s.score for s in stocks) / len(stocks)
                    interp = "Bullish" if avg_score > 0.3 else "Bearish" if avg_score < -0.3 else "Neutral"
                    market_summary.append(
                        {
                            "label": name,
                            "score": avg_score,
                            "interpretation": interp,
                        }
                    )

        template = self._env.get_template("dashboard.html")
        html = template.render(
            root="",
            active="dashboard",
            updated_at=datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
            latest_reports=reports,
            market_table=market_table[:20],
            market_summary=market_summary,
        )
        (self._output_dir / "index.html").write_text(html, encoding="utf-8")

    def _build_reports(self, reports: list[ReportInfo]) -> None:
        """Build the reports index and individual report pages."""
        reports_out = self._output_dir / "reports"
        reports_out.mkdir(parents=True, exist_ok=True)

        # Index page
        index_template = self._env.get_template("reports_index.html")
        html = index_template.render(root="../", active="reports", reports=reports)
        (reports_out / "index.html").write_text(html, encoding="utf-8")

        # Individual report pages
        report_template = self._env.get_template("report.html")
        for report in reports:
            md_text = report.source_path.read_text(encoding="utf-8")
            # Skip the first line (title) as we show it in the template
            lines = md_text.split("\n", 1)
            body = lines[1] if len(lines) > 1 else ""

            html = report_template.render(
                root="../",
                active="reports",
                title=report.title,
                date=report.date,
                content=_markdown_to_html(body),
            )
            (reports_out / report.filename).write_text(html, encoding="utf-8")

    def _build_market(self, market_data: dict[str, list[StockRow]] | None) -> None:
        """Build market overview and individual stock pages."""
        market_out = self._output_dir / "market"
        market_out.mkdir(parents=True, exist_ok=True)

        # Market index
        index_template = self._env.get_template("market_index.html")
        html = index_template.render(
            root="../",
            active="market",
            markets=market_data or {},
        )
        (market_out / "index.html").write_text(html, encoding="utf-8")

        # Individual stock pages
        if market_data:
            detail_template = self._env.get_template("stock_detail.html")
            for stocks in market_data.values():
                for stock in stocks:
                    html = detail_template.render(
                        root="../",
                        active="market",
                        symbol=stock.symbol,
                        currency=stock.currency,
                        close=stock.close,
                        score=stock.score,
                        interpretation=stock.interpretation,
                        macd_signal=stock.macd_signal,
                        mfi_signal=stock.mfi_signal,
                        obv_signal=stock.obv_signal,
                        chart_html=None,
                    )
                    (market_out / f"{stock.symbol}.html").write_text(html, encoding="utf-8")


def _markdown_to_html(text: str) -> str:
    """Convert markdown text to HTML (simple converter).

    Handles headings, lists, paragraphs, bold, code, links, and horizontal rules.
    """
    lines = text.split("\n")
    html_parts: list[str] = []
    in_list = False
    list_type = ""

    for line in lines:
        stripped = line.strip()

        # Blank line
        if not stripped:
            if in_list:
                html_parts.append(f"</{list_type}>")
                in_list = False
            continue

        # Headings
        if stripped.startswith("#"):
            if in_list:
                html_parts.append(f"</{list_type}>")
                in_list = False
            level = min(len(stripped) - len(stripped.lstrip("#")), 6)
            content = stripped[level:].strip()
            html_parts.append(f"<h{level}>{_inline_format(content)}</h{level}>")
            continue

        # Horizontal rule
        if stripped in ("---", "***", "___"):
            if in_list:
                html_parts.append(f"</{list_type}>")
                in_list = False
            html_parts.append("<hr>")
            continue

        # Unordered list
        if stripped.startswith(("- ", "* ")):
            if not in_list or list_type != "ul":
                if in_list:
                    html_parts.append(f"</{list_type}>")
                html_parts.append("<ul>")
                in_list = True
                list_type = "ul"
            html_parts.append(f"<li>{_inline_format(stripped[2:])}</li>")
            continue

        # Ordered list
        if re.match(r"^\d+\.\s", stripped):
            if not in_list or list_type != "ol":
                if in_list:
                    html_parts.append(f"</{list_type}>")
                html_parts.append("<ol>")
                in_list = True
                list_type = "ol"
            content = re.sub(r"^\d+\.\s", "", stripped)
            html_parts.append(f"<li>{_inline_format(content)}</li>")
            continue

        # Paragraph
        if in_list:
            html_parts.append(f"</{list_type}>")
            in_list = False
        html_parts.append(f"<p>{_inline_format(stripped)}</p>")

    if in_list:
        html_parts.append(f"</{list_type}>")

    return "\n".join(html_parts)


def _inline_format(text: str) -> str:
    """Apply inline formatting: bold, code, links."""
    # Code spans
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # Bold
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    # Links
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def generate_site(
    reports_dir: str | Path = "data/reports",
    output_dir: str | Path = "docs/site",
    market_data: dict[str, list[StockRow]] | None = None,
) -> Path:
    """Build the static site (convenience function).

    Args:
        reports_dir: Directory containing NR_*.md report files.
        output_dir: Directory for generated HTML output.
        market_data: Optional market data for dashboard/market pages.

    Returns:
        Path to the output directory.
    """
    builder = SiteBuilder(Path(reports_dir), Path(output_dir))
    return builder.build(market_data=market_data)
