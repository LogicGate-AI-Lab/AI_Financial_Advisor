# AI Financial Advisor

[![CI](https://github.com/jeffliulab/AI_Financial_Advisor/actions/workflows/ci.yml/badge.svg)](https://github.com/jeffliulab/AI_Financial_Advisor/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A data-driven, AI-powered investment advisory system that combines **real-time news analysis**, **technical indicators**, and **market sentiment** to deliver actionable investment insights — all through a clean CLI, interactive web demo, or automated daily reports.

> [中文文档](README_CN.md)

---

## Table of Contents

- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Core Modules](#core-modules)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [LLM Provider Support](#llm-provider-support)
- [Deployment](#deployment)
- [Technical Indicators](#technical-indicators)
- [Development](#development)
- [Technology Stack](#technology-stack)
- [Roadmap](#roadmap)

---

## Key Features

| Feature | Description | Status |
|---------|-------------|--------|
| **News Agent** | Fetches headlines from 18+ financial media, scrapes full text, generates daily market reports via LLM | Ready (needs API keys) |
| **Stock Trend Analyzer** | Computes composite trend score (-1 to +1) using MACD, OBV, MFI for any stock | Fully working |
| **Analyst Agent** | Synthesizes news sentiment + stock technicals into investment outlook reports | Ready (needs API keys) |
| **Pluggable LLM** | Switch between OpenAI, Claude, DeepSeek, or local Ollama via `.env` | Fully working |
| **Gradio Web Demo** | Interactive stock analysis with candlestick charts, deployable to HF Spaces | Ready |
| **Static Site Generator** | Converts markdown reports to HTML for GitHub Pages | Ready |
| **CI/CD Pipelines** | GitHub Actions for automated testing and daily news generation | Ready (activate on push) |

---

## Quick Start

### Prerequisites

- Python 3.11 or higher
- (Optional) API keys for LLM and NewsAPI — stock analysis works without them

### Installation

```bash
git clone https://github.com/jeffliulab/AI_Financial_Advisor.git
cd AI_Financial_Advisor

# Install the package (editable mode for development)
pip install -e .

# Copy the example config and fill in your API keys
cp .env.example .env
```

### Try It Now (No API Keys Needed)

```bash
# Analyze a single stock — works immediately
ai-advisor stock score AAPL

# Scan and rank 10 stocks by trend
ai-advisor stock scan "AAPL,MSFT,AMZN,GOOG,TSLA,NVDA,META,JPM,NFLX,DIS"

# View your current configuration
ai-advisor config show
```

### With API Keys Configured

```bash
# Generate a daily global news report (English)
ai-advisor news run --lang en

# Generate a daily global news report (Chinese)
ai-advisor news run --lang cn

# Run the full analyst pipeline: news sentiment + stock technicals → investment advice
ai-advisor analyze --report data/reports/NR_2025-07-11.md --symbols "AAPL,MSFT,NVDA"

# Launch the interactive Gradio web interface
pip install gradio    # one-time install
ai-advisor web launch
```

### CLI Command Reference

| Command | Description | API Keys Required |
|---------|-------------|:-:|
| `ai-advisor stock score AAPL` | Analyze a single stock's trend | No |
| `ai-advisor stock scan "AAPL,MSFT"` | Scan and rank multiple stocks | No |
| `ai-advisor news run --lang en` | Run news pipeline, generate report | Yes (NewsAPI + LLM) |
| `ai-advisor analyze -r report.md` | Generate investment outlook from report | Yes (LLM) |
| `ai-advisor web launch` | Start Gradio web interface | No (for stock tab) |
| `ai-advisor config show` | Display current configuration | No |

### Example Outputs

**Stock Score:**
```
========================================
  AAPL Trend Analysis
========================================
  Latest Close:  $247.99
  Trend Score:   -0.6458
  Interpretation: Bearish
  MACD Signal:   -1.0000
  MFI Signal:    -0.2869
  OBV Signal:    -0.5326
========================================
```

**Stock Scan:**
```
Symbol      Close    Score  Signal
----------------------------------------
MSFT     $ 381.87  -0.2677 Neutral
TSLA     $ 367.96  -0.5763 Bearish
AAPL     $ 247.99  -0.7027 Bearish
NVDA     $ 172.70  -0.7707 Bearish
META     $ 593.66  -0.8385 Bearish
```

---

## Core Modules

### 1. News Agent

The News Agent automates the entire financial news pipeline:

```
NewsAPI (18+ sources) → Fetch Headlines → Scrape Full Text → LLM Analysis → Markdown Report
```

- **Sources**: Reuters, Bloomberg, WSJ, Financial Times, The Economist, Business Insider, NYT, BBC, AP, Washington Post, CNN, ABC, CBS, NBC, The Verge, TechCrunch, Wired, Ars Technica, Engadget
- **Output**: Professional daily market reports in English or Chinese, covering:
  - Today's news overview with overall sentiment indicator
  - Key news details (10+ items on finance, markets, macro)
  - Affected sectors and companies
  - Signals to watch for future market impact
- **Prompts**: Stored as Jinja2 templates (`agents/prompts/news_report_en.j2`, `news_report_cn.j2`) — easy to customize

### 2. Stock Trend Analyzer

Computes a composite trend score for any stock:

```
Yahoo Finance → OHLCV Data → MACD + OBV + MFI Indicators → Composite Score (-1 to +1)
```

- **Input**: Any stock ticker (e.g., `AAPL`, `MSFT`, `600519.SS`)
- **Indicators**: MACD (momentum), MFI (money flow), OBV (volume trend)
- **Output**: `TrendScoreResult` with score, per-indicator signals, and interpretation (Bullish/Neutral/Bearish)
- **Batch Mode**: `stock scan` command analyzes and ranks multiple stocks at once

### 3. Analyst Agent

The system's "brain" — synthesizes all signals into investment advice:

```
News Report → LLM Sentiment Extraction → Structured SentimentResult
Stock Symbols → Technical Analysis → list[StockAnalysis]
─────────────── Combined via Prompt Template ───────────────
→ LLM → Investment Outlook Report
```

- **Sentiment Analysis**: Extracts overall sentiment, confidence score, per-sector breakdown (Technology, Financials, Energy, Healthcare, Consumer), and affected tickers
- **Synthesis**: Combines sentiment with stock trend scores to identify alignment (e.g., bullish sentiment + bullish technicals = high-conviction opportunity)
- **Output**: Market overview, top opportunities, risk alerts, actionable recommendations, key signals to monitor

### 4. Gradio Web Demo

Interactive web interface with two tabs:

- **Stock Trend Analyzer**: Enter a ticker → see candlestick chart, MACD, MFI, OBV subplots, and trend score (powered by Plotly)
- **News Report Browser**: Browse saved reports by date and language

Deployable to [Hugging Face Spaces](https://huggingface.co/spaces) for free, public portfolio demos.

### 5. Static Site Generator

Converts saved markdown reports into a clean HTML website:

- Index page listing all available reports
- Individual report pages with clean typography
- Deployable to GitHub Pages via the `daily_news.yml` GitHub Action

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                     │
│  CLI (Typer) │ Gradio Demo │ Static HTML │ FastAPI (TBD)│
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                     AGENT LAYER                          │
│     NewsAgent  │  StockAgent  │  AnalystAgent            │
│     (orchestrates data flow and LLM calls)               │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                   ANALYSIS LAYER                         │
│  indicators.py  │  trend_score.py  │  sentiment.py       │
│  (pure computation, no side effects, fully testable)     │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                     DATA LAYER                           │
│  news_fetcher │ news_scraper │ stock_data │ storage/     │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                  INFRASTRUCTURE                          │
│     config.py (pydantic-settings)  │  llm/ (providers)   │
└─────────────────────────────────────────────────────────┘
```

**Key design principles:**
- **Layered**: Each layer only depends on layers below it. No circular dependencies.
- **Pure analysis**: The `analysis/` layer has zero side effects — easy to test and reuse in notebooks or other tools.
- **LLM-agnostic**: All LLM calls go through a `LLMProvider` abstract interface. Switching models is a config change.
- **Lazy loading**: Heavy dependencies (newspaper3k, gradio) are only imported when needed.
- **Prompt-as-data**: LLM prompts are Jinja2 templates stored in `agents/prompts/`, not hardcoded in Python.

See [docs/architecture.md](docs/architecture.md) for detailed design decisions, data flow diagrams, and module dependency graph.

---

## Project Structure

```
AI_Financial_Advisor/
├── pyproject.toml                          # PEP 621 package metadata + dependencies
├── README.md                               # This file (English)
├── README_CN.md                            # Chinese version
├── .env.example                            # Configuration template with all settings
├── .gitignore
│
├── src/ai_financial_advisor/               # ── Main Python Package ──
│   ├── __init__.py                         # Package version
│   ├── config.py                           # Centralized settings (pydantic-settings)
│   ├── cli.py                              # Typer CLI: 6 commands, 4 groups
│   │
│   ├── llm/                                # ── LLM Abstraction Layer ──
│   │   ├── base.py                         # LLMProvider ABC + LLMResponse dataclass
│   │   ├── openai_provider.py              # OpenAI / DeepSeek / any compatible API
│   │   ├── claude_provider.py              # Anthropic Claude
│   │   ├── ollama_provider.py              # Local Ollama (inherits OpenAI provider)
│   │   └── factory.py                      # get_llm(settings) → LLMProvider
│   │
│   ├── data/                               # ── Data Acquisition ──
│   │   ├── news_fetcher.py                 # NewsAPI client → list[Article]
│   │   ├── news_scraper.py                 # newspaper3k full-text scraper
│   │   ├── stock_data.py                   # yfinance OHLCV downloader
│   │   └── storage/                        # Storage backends
│   │       ├── base.py                     # DataStore abstract interface
│   │       └── sqlite_store.py             # SQLite implementation
│   │
│   ├── analysis/                           # ── Pure Computation (no side effects) ──
│   │   ├── indicators.py                   # MACD, OBV, MFI (single source of truth)
│   │   ├── trend_score.py                  # Composite trend score formula
│   │   └── sentiment.py                    # LLM-based sentiment extraction
│   │
│   ├── agents/                             # ── Agent Orchestration ──
│   │   ├── news_agent.py                   # News pipeline: fetch → scrape → report
│   │   ├── stock_agent.py                  # Stock analysis: data → indicators → score
│   │   ├── analyst_agent.py                # Full pipeline: sentiment + technicals → advice
│   │   └── prompts/                        # Jinja2 prompt templates
│   │       ├── news_report_en.j2           # English news report prompt
│   │       ├── news_report_cn.j2           # Chinese news report prompt
│   │       └── analyst_report.j2           # Investment outlook prompt
│   │
│   └── web/                                # ── Web Interfaces ──
│       ├── gradio_app.py                   # Interactive demo (HF Spaces)
│       └── static_generator.py             # HTML report builder (GitHub Pages)
│
├── tests/                                  # ── Test Suite (35 tests) ──
│   ├── conftest.py                         # Shared fixtures (synthetic OHLCV data)
│   ├── test_indicators.py                  # MACD, OBV, MFI unit tests
│   ├── test_trend_score.py                 # Composite score tests (uptrend/downtrend)
│   ├── test_config.py                      # Configuration loading tests
│   ├── test_llm_providers.py               # Provider factory tests
│   ├── test_storage.py                     # SQLite storage CRUD tests
│   └── test_static_generator.py            # HTML generation tests
│
├── scripts/
│   └── daily_news_pipeline.py              # Cron job entry point for GitHub Actions
│
├── docs/
│   ├── architecture.md                     # System design deep-dive
│   ├── deployment.md                       # Step-by-step deployment guide
│   └── development_history.md              # Project evolution from V0.1 to V0.2
│
├── .github/workflows/
│   ├── ci.yml                              # PR checks: pytest + ruff (Python 3.11/3.12/3.13)
│   └── daily_news.yml                      # Daily cron: news pipeline + GitHub Pages deploy
│
└── legacy/                                 # V0 code archive (not imported, for reference)
    ├── news_agent_V0/
    ├── stock_trend_agent/
    └── analyst_agent/
```

---

## LLM Provider Support

Switch providers with **zero code changes** — just edit `.env`:

### DeepSeek (default, low cost)
```ini
LLM_PROVIDER=openai
LLM_MODEL=deepseek-reasoner
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=sk-your-deepseek-key
```

### OpenAI
```ini
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
LLM_API_KEY=sk-your-openai-key
```

### Claude
```ini
LLM_PROVIDER=claude
LLM_MODEL=claude-sonnet-4-6
LLM_API_KEY=sk-ant-your-claude-key
```

### Ollama (fully offline, no API key needed)
```ini
LLM_PROVIDER=ollama
LLM_MODEL=llama3
```
Requires Ollama running locally: `ollama serve`

**How it works**: The `llm/factory.py` reads your `.env` settings and returns the appropriate `LLMProvider` implementation. The `OllamaProvider` inherits from `OpenAIProvider` since Ollama exposes an OpenAI-compatible API. The `ClaudeProvider` handles Anthropic's different message format (system prompts passed separately).

---

## Deployment

| Platform | Purpose | Cost | Setup Effort |
|----------|---------|------|:---:|
| **GitHub Actions + Pages** | Daily news reports, auto-deployed as HTML | Free | Low |
| **Hugging Face Spaces** | Interactive Gradio demo for portfolio showcase | Free | Low |
| **Local CLI + Ollama** | Private use, fully offline | Free | Minimal |
| **Google Cloud Run** | Production API with authentication (future) | ~$5/mo | Medium |

### Quick Deploy: GitHub Actions

1. Push this repo to GitHub
2. Go to **Settings → Secrets → Actions**, add: `LLM_PROVIDER`, `LLM_MODEL`, `LLM_BASE_URL`, `LLM_API_KEY`, `NEWS_API_API_KEY`
3. Enable **GitHub Pages** (Settings → Pages → Source: GitHub Actions)
4. The `daily_news.yml` workflow runs automatically at UTC 02:00, or trigger manually via Actions tab

### Quick Deploy: Hugging Face Spaces

1. Create a new Space on huggingface.co (SDK: Gradio)
2. Upload `src/ai_financial_advisor/` as `ai_financial_advisor/`
3. Add an `app.py`:
   ```python
   from ai_financial_advisor.web.gradio_app import create_app
   app = create_app()
   app.launch()
   ```
4. Add API keys in Space Settings → Secrets

See [docs/deployment.md](docs/deployment.md) for detailed instructions.

---

## Technical Indicators

The composite trend score combines three indicators into a single value from **-1** (strongly bearish) to **+1** (strongly bullish):

| Indicator | Weight | What It Measures | Signal Range |
|-----------|:------:|-----------------|:----:|
| **MACD** (Moving Average Convergence Divergence) | 40% | Momentum: is the trend accelerating or decelerating? | [-1, +1] |
| **MFI** (Money Flow Index) | 30% | Money pressure: is capital flowing in or out? | [-1, +1] |
| **OBV** (On-Balance Volume) | 30% | Volume confirmation: does volume support the price trend? | [-1, +1] |

### Formula

```
Score = w_macd × tanh(H_t / σ_H)
      + w_mfi  × clip((MFI_t - 50) / 50, -1, 1)
      + w_obv  × tanh((OBV_t - OBV_{t-N}) / |OBV_{t-N}|)
```

Where:
- `H_t` = latest MACD histogram value, `σ_H` = std of last 5 histograms
- `MFI_t` = latest Money Flow Index (0-100 scale, rescaled to [-1, +1])
- `OBV_t` = latest On-Balance Volume, `OBV_{t-N}` = OBV from N days ago

### Interpretation

| Score Range | Interpretation | Suggested Action |
|:-----------:|:--------------:|:----------------:|
| +0.3 to +1.0 | **Bullish** | Consider increasing position |
| -0.3 to +0.3 | **Neutral** | Hold, monitor for changes |
| -1.0 to -0.3 | **Bearish** | Consider reducing exposure |

---

## Development

### Setup

```bash
# Install with all dev dependencies
pip install -e ".[dev]"

# Run the full test suite
pytest -v

# Run with coverage report
pytest --cov=ai_financial_advisor --cov-report=term-missing

# Lint check
ruff check src/ tests/

# Format check
ruff format --check src/ tests/
```

### Test Structure

| Test File | What It Tests | Tests |
|-----------|---------------|:-----:|
| `test_indicators.py` | MACD, OBV, MFI calculations, immutability | 10 |
| `test_trend_score.py` | Score range, uptrend/downtrend, custom weights | 7 |
| `test_config.py` | Settings loading, defaults | 4 |
| `test_llm_providers.py` | Factory pattern, provider instantiation | 4 |
| `test_storage.py` | SQLite CRUD, deduplication | 5 |
| `test_static_generator.py` | HTML generation, index page | 3 |
| **Total** | | **35** |

### Code Quality

- **Linting**: `ruff` with rules for pyflakes, pycodestyle, isort, naming, upgrades
- **Type checking**: `mypy` in strict mode (all new code has type hints)
- **CI**: GitHub Actions runs tests on Python 3.11, 3.12, and 3.13

---

## Technology Stack

| Category | Technology | Why This Choice |
|----------|-----------|-----------------|
| **Language** | Python 3.11+ | Industry standard for finance + AI |
| **Package** | pyproject.toml + hatchling | Modern PEP 621 standard |
| **Configuration** | pydantic-settings | Type-safe, auto-loads `.env`, validates at startup |
| **CLI** | Typer | Minimal code, beautiful output, auto-generated help |
| **LLM SDKs** | openai + anthropic | Official SDKs; Ollama reuses `openai` SDK via base_url |
| **News Data** | NewsAPI + newspaper3k | Headline API + full-text extraction |
| **Stock Data** | yfinance | Free, reliable, covers global markets |
| **Computation** | pandas + numpy | De facto standard for financial data |
| **Visualization** | Plotly | Interactive charts, works in Gradio and HTML |
| **Web Demo** | Gradio | Python-native, one-click HF Spaces deploy |
| **Prompts** | Jinja2 | Separates prompt text from Python logic |
| **Database** | SQLite → PostgreSQL (future) | Zero config for dev, upgrade path for production |
| **Testing** | pytest + pytest-cov | 35 tests with synthetic data fixtures |
| **Code Quality** | ruff + mypy | Fast linting + strict type checking |
| **CI/CD** | GitHub Actions | Free, integrated, multi-Python matrix |

---

## Roadmap

- [x] **Phase 1 — Foundation**: Package scaffolding, pydantic-settings config, LLM abstraction layer (OpenAI/Claude/Ollama), analysis module (MACD/OBV/MFI/trend score), news agent, stock agent, Typer CLI
- [x] **Phase 2 — Demo & Automation**: Gradio web demo, static site generator, GitHub Actions (CI + daily pipeline), sentiment analysis, analyst agent, SQLite storage, documentation
- [ ] **Phase 3 — Intelligence**: Macro data integration (FRED API for GDP/CPI/unemployment), anomaly detection, Telegram bot for daily push notifications
- [ ] **Phase 4 — Production**: FastAPI backend with authentication, user profiles and portfolio tracking, RAG Q&A system (ChromaDB), PostgreSQL migration, Docker containerization

---

## License

MIT — see [LICENSE](LICENSE) for details.
