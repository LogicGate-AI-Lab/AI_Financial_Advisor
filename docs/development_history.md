# Development History

## V0.2: Full Restructuring, 2026

### March 2026

Complete restructuring from standalone scripts into a professional Python package:

- **Package architecture**: `pyproject.toml` + `src/` layout, installable via `pip install -e .`
- **LLM abstraction layer**: Pluggable providers for OpenAI, Claude, DeepSeek, Ollama — switch via `.env`
- **Analysis module**: Extracted MACD/OBV/MFI calculations into a single source of truth (eliminated 3 duplicates)
- **Composite trend score**: Formalized the scoring formula with typed `TrendScoreResult` dataclass
- **News Agent refactored**: Merged EN/CN report scripts, Jinja2 prompt templates, proper logging
- **Stock Agent**: End-to-end analysis with CLI support for single stock and multi-stock scanning
- **Analyst Agent**: New module combining news sentiment + stock technicals → investment outlook
- **Sentiment analysis**: LLM-based structured sentiment extraction (overall + per-sector + affected tickers)
- **Gradio web demo**: Interactive stock analyzer + news browser for Hugging Face Spaces
- **Static site generator**: HTML report builder for GitHub Pages deployment
- **SQLite storage backend**: Abstract DataStore interface with SQLite implementation
- **CLI**: 6 commands across 4 groups (news, stock, analyze, web, config)
- **CI/CD**: GitHub Actions for testing (Python 3.11/3.12/3.13) + daily news pipeline
- **Testing**: 35 tests covering config, indicators, trend score, LLM factory, storage, static generator
- **Documentation**: architecture.md, deployment.md, updated README (EN + CN)

## V0.1: Exploration Period, 2025

### August 2025

- Designed and built stock trend agent with composite scoring formula (MACD + OBV + MFI)
- Tested two quantitative strategies on QuantConnect:
  - Basic trend-following (score > 0 buy, profitable + score < 0 sell)
  - Enhanced with cash reserve, averaging down limits, profit-taking, minimum hold period

### July 2025

- Planned GCS ETL architecture (raw → processed → reports) for production deployment
- Paused development due to interview preparation

### June 2025

- Launched MVP for news agent (V0)
- Three-step pipeline: NewsAPI fetch → newspaper3k scrape → DeepSeek report generation
- Deployed on Google Cloud with daily cron job at UTC 02:00
- Demo published on GitHub Pages
- Created comprehensive financial analyst keyword list for news categorization
