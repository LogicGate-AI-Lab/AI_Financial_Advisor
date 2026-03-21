# Deployment Guide

## Local Development

### Prerequisites
- Python 3.11+
- API keys (see `.env.example`)

### Setup
```bash
# Clone the repo
git clone https://github.com/your-username/AI_Financial_Advisor.git
cd AI_Financial_Advisor

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e ".[dev]"

# Copy and fill in your API keys
cp .env.example .env
# Edit .env with your keys

# Verify installation
ai-advisor config show
ai-advisor stock score AAPL
```

### Running Tests
```bash
pytest                          # Run all tests
pytest --cov=ai_financial_advisor  # With coverage
ruff check src/ tests/         # Lint
```

## LLM Configuration

Switch between providers by editing `.env`:

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
LLM_BASE_URL=
LLM_API_KEY=sk-your-openai-key
```

### Claude
```ini
LLM_PROVIDER=claude
LLM_MODEL=claude-sonnet-4-6
LLM_API_KEY=sk-ant-your-claude-key
```

### Ollama (fully offline, no API key)
```ini
LLM_PROVIDER=ollama
LLM_MODEL=llama3
```
Requires Ollama running locally: `ollama serve`

## Deployment Architecture

```
GCP Server (cron jobs, not always-on)
  ├── Daily pipeline: news → report → anomaly detection → Telegram push
  ├── git push to main branch
  └── Logs: data/logs/

GitHub Actions (auto-triggered)
  ├── CI: ruff + pytest on push/PR
  └── deploy_site.yml: build site → deploy to gh-pages

GitHub Pages (gh-pages branch)
  └── Financial dashboard site
```

### Server Setup

Server deployment files live in `server/` (gitignored). See `server/README.md` for setup instructions.

### GitHub Actions

- **`ci.yml`** — Runs on push/PR: lint + multi-version test matrix
- **`deploy_site.yml`** — Runs on push to main (when reports/web change): builds site, deploys to gh-pages
- **`daily_news.yml`** — Manual-trigger backup for the news pipeline (server cron is primary)

**Setup:**
1. Go to your repo → Settings → Secrets and variables → Actions
2. Add secrets: `LLM_PROVIDER`, `LLM_MODEL`, `LLM_BASE_URL`, `LLM_API_KEY`, `NEWS_API_API_KEY`
3. Enable GitHub Pages (Settings → Pages → Source: GitHub Actions)

## CLI Reference

| Command | Description |
|---------|-------------|
| `ai-advisor news run --lang en` | Run news pipeline, generate report |
| `ai-advisor stock score AAPL` | Analyze a single stock |
| `ai-advisor stock scan "AAPL,MSFT"` | Scan and rank multiple stocks |
| `ai-advisor stock scan --market cn` | Scan preset market watchlist |
| `ai-advisor stock alerts "AAPL,MSFT"` | Detect price/volume anomalies |
| `ai-advisor macro show` | Display macroeconomic indicators (FRED) |
| `ai-advisor backtest run AAPL` | Backtest trend strategy on a symbol |
| `ai-advisor backtest scan "AAPL,MSFT"` | Compare backtest results |
| `ai-advisor notify test` | Send a test Telegram notification |
| `ai-advisor notify digest` | Send daily market digest via Telegram |
| `ai-advisor notify alerts "AAPL"` | Send anomaly alerts via Telegram |
| `ai-advisor analyze -r report.md` | Generate investment outlook |
| `ai-advisor web launch` | Start Gradio web interface |
| `ai-advisor config show` | Display current configuration |

## Security Notes

- API keys are **never committed** to git (`.env` is in `.gitignore`)
- Server deployment files are **gitignored** (`server/`)
- GitHub Actions uses encrypted secrets
- Static reports on GitHub Pages contain only AI-generated summaries
- Ollama mode requires zero external API calls
