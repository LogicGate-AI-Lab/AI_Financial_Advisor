"""Daily news pipeline entry point for cron jobs / GitHub Actions.

This script runs the full news pipeline and optionally generates
static HTML for GitHub Pages deployment.

Usage:
    python scripts/daily_news_pipeline.py
    python scripts/daily_news_pipeline.py --lang cn
    python scripts/daily_news_pipeline.py --generate-site
"""

import argparse
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

# Add src/ to path so this script works without pip install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ai_financial_advisor.agents.news_agent import NewsAgent
from ai_financial_advisor.config import get_settings
from ai_financial_advisor.web.static_generator import generate_static_site

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run daily news pipeline.")
    parser.add_argument("--lang", default="en", choices=["en", "cn"], help="Report language.")
    parser.add_argument("--date", type=str, default=None, help="Target date (YYYY-MM-DD). Default: yesterday.")
    parser.add_argument("--generate-site", action="store_true", help="Also generate static HTML site.")
    parser.add_argument("--site-output-dir", type=Path, default=Path("docs/site"), help="Static site output directory.")
    args = parser.parse_args()

    settings = get_settings()
    target_date = date.fromisoformat(args.date) if args.date else date.today() - timedelta(days=1)

    logger.info("Starting daily news pipeline for %s (%s)...", target_date, args.lang)

    agent = NewsAgent(settings)
    report_path = agent.run(language=args.lang, target_date=target_date)

    if report_path:
        logger.info("Pipeline complete. Report: %s", report_path)
    else:
        logger.error("Pipeline failed. No report generated.")
        sys.exit(1)

    if args.generate_site:
        logger.info("Generating static HTML site...")
        generate_static_site(settings.storage.reports_dir, args.site_output_dir)
        logger.info("Static site generated at %s", args.site_output_dir)


if __name__ == "__main__":
    main()
