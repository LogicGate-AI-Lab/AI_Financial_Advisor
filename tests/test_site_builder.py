"""Tests for the site builder (financial dashboard generator)."""

from pathlib import Path

import pytest

from ai_financial_advisor.web.site_builder import (
    SiteBuilder,
    StockRow,
    generate_site,
)


@pytest.fixture
def reports_dir(tmp_path: Path) -> Path:
    d = tmp_path / "reports"
    d.mkdir()
    (d / "NR_2026-03-21.md").write_text(
        "# Global News Daily Report (2026-03-21)\n\nTest content here.\n\n- Item 1\n- Item 2\n"
    )
    (d / "NR_2026-03-20.md").write_text(
        "# Global News Daily Report (2026-03-20)\n\nYesterday's report.\n"
    )
    return d


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    return tmp_path / "site"


@pytest.fixture
def sample_market_data() -> dict[str, list[StockRow]]:
    return {
        "US Stocks": [
            StockRow("AAPL", "USD", 247.99, -0.53, "Bearish", -1.0, -0.29, -0.14),
            StockRow("MSFT", "USD", 381.87, -0.27, "Neutral", -0.5, -0.1, -0.05),
        ],
        "Crypto": [
            StockRow("BTC-USD", "USD", 70392.95, 0.28, "Neutral", 0.49, 0.37, -0.1),
        ],
    }


class TestSiteBuilder:
    def test_builds_index(self, reports_dir: Path, output_dir: Path) -> None:
        builder = SiteBuilder(reports_dir, output_dir)
        builder.build()
        assert (output_dir / "index.html").exists()

    def test_builds_reports_index(self, reports_dir: Path, output_dir: Path) -> None:
        builder = SiteBuilder(reports_dir, output_dir)
        builder.build()
        assert (output_dir / "reports" / "index.html").exists()

    def test_builds_individual_reports(self, reports_dir: Path, output_dir: Path) -> None:
        builder = SiteBuilder(reports_dir, output_dir)
        builder.build()
        assert (output_dir / "reports" / "NR_2026-03-21.html").exists()
        assert (output_dir / "reports" / "NR_2026-03-20.html").exists()

    def test_report_contains_content(self, reports_dir: Path, output_dir: Path) -> None:
        builder = SiteBuilder(reports_dir, output_dir)
        builder.build()
        html = (output_dir / "reports" / "NR_2026-03-21.html").read_text()
        assert "Test content here" in html
        assert "Item 1" in html

    def test_builds_market_pages(
        self, reports_dir: Path, output_dir: Path, sample_market_data: dict
    ) -> None:
        builder = SiteBuilder(reports_dir, output_dir)
        builder.build(market_data=sample_market_data)
        assert (output_dir / "market" / "index.html").exists()
        assert (output_dir / "market" / "AAPL.html").exists()
        assert (output_dir / "market" / "BTC-USD.html").exists()

    def test_market_page_has_score(
        self, reports_dir: Path, output_dir: Path, sample_market_data: dict
    ) -> None:
        builder = SiteBuilder(reports_dir, output_dir)
        builder.build(market_data=sample_market_data)
        html = (output_dir / "market" / "AAPL.html").read_text()
        assert "AAPL" in html
        assert "247.99" in html

    def test_copies_css(self, reports_dir: Path, output_dir: Path) -> None:
        builder = SiteBuilder(reports_dir, output_dir)
        builder.build()
        assert (output_dir / "assets" / "style.css").exists()

    def test_empty_reports_dir(self, tmp_path: Path, output_dir: Path) -> None:
        empty_dir = tmp_path / "empty_reports"
        empty_dir.mkdir()
        builder = SiteBuilder(empty_dir, output_dir)
        builder.build()
        assert (output_dir / "index.html").exists()

    def test_dashboard_has_report_links(self, reports_dir: Path, output_dir: Path) -> None:
        builder = SiteBuilder(reports_dir, output_dir)
        builder.build()
        html = (output_dir / "index.html").read_text()
        assert "NR_2026-03-21.html" in html


class TestGenerateSite:
    def test_convenience_function(self, reports_dir: Path, output_dir: Path) -> None:
        result = generate_site(reports_dir, output_dir)
        assert result == output_dir
        assert (output_dir / "index.html").exists()
