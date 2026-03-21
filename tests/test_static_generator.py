"""Tests for static site generator."""

from pathlib import Path

from ai_financial_advisor.web.static_generator import generate_static_site


class TestStaticGenerator:
    def test_generates_index(self, tmp_path: Path) -> None:
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "NR_2025-07-11.md").write_text("# Report\n\nContent here.", encoding="utf-8")

        output_dir = tmp_path / "site"
        generate_static_site(reports_dir, output_dir)

        assert (output_dir / "index.html").exists()
        assert (output_dir / "NR_2025-07-11.html").exists()

    def test_empty_reports_dir(self, tmp_path: Path) -> None:
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        output_dir = tmp_path / "site"

        generate_static_site(reports_dir, output_dir)

        index = (output_dir / "index.html").read_text(encoding="utf-8")
        assert "No reports available" in index

    def test_html_contains_report_link(self, tmp_path: Path) -> None:
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "NR_2025-07-11.md").write_text("# Test Report\n\nHello world.", encoding="utf-8")

        output_dir = tmp_path / "site"
        generate_static_site(reports_dir, output_dir)

        index = (output_dir / "index.html").read_text(encoding="utf-8")
        assert "NR_2025-07-11.html" in index
