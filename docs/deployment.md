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

## Deployment Options

### 1. GitHub Actions + GitHub Pages (Recommended, Free)

The daily news pipeline runs automatically via GitHub Actions:

**Setup:**
1. Go to your repo → Settings → Secrets and variables → Actions
2. Add these secrets:
   - `LLM_PROVIDER`, `LLM_MODEL`, `LLM_BASE_URL`, `LLM_API_KEY`
   - `NEWS_API_API_KEY`
3. Enable GitHub Pages (Settings → Pages → Source: GitHub Actions)
4. The `daily_news.yml` workflow runs at UTC 02:00 daily

**Manual trigger:**
Go to Actions → "Daily News Pipeline" → "Run workflow"

### 2. Hugging Face Spaces (Interactive Demo, Free)

Deploy the Gradio app to HF Spaces for a live, interactive demo.

**Setup:**
1. Create a new Space on huggingface.co (SDK: Gradio)
2. Upload these files:
   ```
   src/ai_financial_advisor/   → ai_financial_advisor/
   app.py                      → (see below)
   requirements.txt            → (see below)
   ```
3. Add API keys in Space Settings → Variables and Secrets

**app.py for HF Spaces:**
```python
from ai_financial_advisor.web.gradio_app import create_app
app = create_app()
app.launch()
```

**requirements.txt:**
```
pydantic-settings>=2.0
openai>=1.0
anthropic>=0.30
yfinance>=0.2
pandas>=2.0
numpy>=1.24
plotly>=5.0
jinja2>=3.1
gradio>=4.0
```

### 3. Google Cloud Run (Production API, ~$5/month)

For the FastAPI backend (Phase 4):

```bash
# Build container
docker build -t ai-financial-advisor .

# Deploy to Cloud Run
gcloud run deploy ai-advisor \
  --image gcr.io/YOUR_PROJECT/ai-financial-advisor \
  --platform managed \
  --allow-unauthenticated
```

### 4. Local Only (Zero Cost, Maximum Privacy)

```bash
# Use Ollama for LLM (no API calls)
# Set in .env: LLM_PROVIDER=ollama, LLM_MODEL=llama3

# Run stock analysis
ai-advisor stock scan "AAPL,MSFT,NVDA,TSLA"

# Launch local web interface
ai-advisor web launch
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `ai-advisor news run --lang en` | Run news pipeline, generate report |
| `ai-advisor stock score AAPL` | Analyze a single stock |
| `ai-advisor stock scan "AAPL,MSFT"` | Scan and rank multiple stocks |
| `ai-advisor analyze -r report.md` | Generate investment outlook |
| `ai-advisor web launch` | Start Gradio web interface |
| `ai-advisor config show` | Display current configuration |

## Security Notes

- API keys are **never committed** to git (`.env` is in `.gitignore`)
- GitHub Actions uses encrypted secrets
- HF Spaces uses its own secrets management
- Static reports on GitHub Pages contain only AI-generated summaries
- Ollama mode requires zero external API calls
