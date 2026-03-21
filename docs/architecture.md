# System Architecture

## Overview

AI Financial Advisor is a modular, data-driven investment advisory system built as an installable Python package (`pip install -e .`). It follows a strict layered architecture where each layer has clear responsibilities and interfaces, with no circular dependencies.

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

## Key Design Decisions

### 1. LLM Abstraction Layer (`llm/`)

All LLM calls go through a `LLMProvider` abstract base class:

```python
class LLMProvider(ABC):
    def complete(self, messages, *, temperature, max_tokens) -> LLMResponse: ...
    def name(self) -> str: ...
```

Three implementations:
- **`OpenAIProvider`** — Covers OpenAI, DeepSeek, and any OpenAI-compatible API via `base_url` override
- **`ClaudeProvider`** — Anthropic Claude (handles the different message format: system prompts passed separately)
- **`OllamaProvider`** — Inherits from `OpenAIProvider` with `base_url=localhost:11434/v1`

The `factory.py` reads `LLMSettings` from config and returns the appropriate provider. Switching from DeepSeek to Claude is a one-line `.env` change.

### 2. Analysis as Pure Functions (`analysis/`)

The `analysis/` package contains **only pure computation** — no I/O, no LLM calls, no side effects:
- `indicators.py`: MACD, OBV, MFI calculations (single source of truth; eliminated 3 prior duplicates)
- `trend_score.py`: Composite score formula returning a typed `TrendScoreResult` dataclass
- `sentiment.py`: LLM-based sentiment extraction (the only module here that calls an LLM, but via injected provider)

This design makes the analysis layer:
- Easy to unit test with synthetic DataFrames
- Reusable in Jupyter notebooks, QuantConnect strategies, or other contexts
- Independent of any specific data source or LLM

### 3. Lazy Agent Imports (`agents/__init__.py`)

The `agents/__init__.py` uses Python's `__getattr__` for lazy module loading. This prevents importing `newspaper3k` (which has heavy dependencies like `lxml`, `nltk`) when only `StockAgent` is needed:

```python
def __getattr__(name):
    if name == "StockAgent":
        from .stock_agent import StockAgent
        return StockAgent
    ...
```

### 4. Jinja2 Prompt Templates (`agents/prompts/`)

All LLM prompts are stored as `.j2` (Jinja2) template files, not hardcoded in Python:
- `news_report_en.j2` / `news_report_cn.j2` — News report generation (merged from two separate V0 scripts)
- `analyst_report.j2` — Investment outlook synthesis

This separates prompt engineering from application logic and makes prompts easy to version, review, and modify.

### 5. Configuration via pydantic-settings (`config.py`)

All settings are loaded from `.env` with type validation at startup:
- `LLMSettings` — provider, model, API key, base_url, temperature, max_tokens
- `NewsAPISettings` — API key, sources list, language, page size
- `StorageSettings` — backend type, SQLite path, GCS bucket, reports directory

Invalid configuration fails fast with clear error messages.

### 6. Storage Abstraction (`data/storage/`)

A `DataStore` abstract base class with `SQLiteStore` implementation (and future `GCSStore`):
- `save_articles()` — Insert with URL-based deduplication
- `get_articles_by_date()` — Query by publish date
- `update_article_content()` — Update after scraping

## Data Flow

### Daily News Pipeline
```
NewsAPI
  → NewsFetcher.fetch_headlines()
  → list[Article] (title, url, description)
  → DataStore.save_articles()
  → news_scraper.scrape_full_text()
  → list[Article] (with full content)
  → DataStore.update_article_content()
  → NewsAgent.generate_report(language="en"|"cn")
  → Jinja2 template → LLMProvider.complete()
  → markdown report
  → NewsAgent.save_report()
  → data/reports/NR_YYYY-MM-DD.md
  → static_generator.generate_static_site()
  → docs/site/index.html (GitHub Pages)
```

### Stock Analysis Pipeline
```
yfinance
  → download_stock_data(symbol, period)
  → DataFrame (OHLCV, 60-250 rows)
  → compute_all_indicators()
  → DataFrame + MACD, Signal, Histogram, OBV, MFI columns
  → calculate_trend_score()
  → TrendScoreResult(score, macd_signal, mfi_signal, obv_signal, interpretation)
```

### Full Analyst Pipeline
```
News Report (markdown text)
  → analyze_sentiment(report, llm)
  → SentimentResult(overall, confidence, sectors, tickers)

Stock Symbols
  → StockAgent.analyze_multiple(symbols)
  → list[StockAnalysis(symbol, trend, data)]

SentimentResult + list[StockAnalysis]
  → analyst_report.j2 template
  → LLMProvider.complete()
  → Investment Outlook Report
```

## Module Dependency Graph

```
config.py ──→ llm/base.py
                 ↑
         ┌───────┼───────────┐
         │       │           │
     llm/openai  llm/claude  llm/ollama
         │       │           │
         └───────┼───────────┘
                 ↑
             llm/factory.py
                 ↑
    ┌────────────┼────────────────┐
    │            │                │
 agents/     analysis/         data/
 news_agent  indicators.py    news_fetcher.py
 stock_agent trend_score.py   news_scraper.py
 analyst_agent sentiment.py   stock_data.py
    │                          storage/
    ↑
 ┌──┼──────────┐
 │  │          │
cli.py  web/   scripts/
      gradio   daily_pipeline
      static
```

**Rule: Lower layers never import from upper layers. No circular dependencies.**

## File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `config.py` | ~80 | Pydantic settings with env loading |
| `cli.py` | ~150 | 6 CLI commands across 4 groups |
| `llm/base.py` | ~40 | ABC + LLMResponse dataclass |
| `llm/openai_provider.py` | ~60 | OpenAI/DeepSeek provider |
| `llm/claude_provider.py` | ~55 | Anthropic provider |
| `llm/ollama_provider.py` | ~20 | Inherits OpenAI, local defaults |
| `llm/factory.py` | ~35 | Provider factory function |
| `data/news_fetcher.py` | ~70 | NewsAPI client |
| `data/news_scraper.py` | ~55 | newspaper3k scraper |
| `data/stock_data.py` | ~35 | yfinance wrapper |
| `data/storage/base.py` | ~30 | DataStore ABC |
| `data/storage/sqlite_store.py` | ~100 | SQLite implementation |
| `analysis/indicators.py` | ~80 | MACD, OBV, MFI (single source) |
| `analysis/trend_score.py` | ~70 | Composite trend scoring |
| `analysis/sentiment.py` | ~100 | LLM-based sentiment extraction |
| `agents/news_agent.py` | ~120 | News pipeline orchestration |
| `agents/stock_agent.py` | ~65 | Stock analysis orchestration |
| `agents/analyst_agent.py` | ~80 | Full analyst pipeline |
| `web/gradio_app.py` | ~150 | Interactive Gradio demo |
| `web/static_generator.py` | ~160 | HTML report generation |
