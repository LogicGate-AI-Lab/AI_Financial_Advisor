# V0.4 — 金融仪表板全面重构计划

## Context

V0.3 已完成：回测框架、Telegram 通知、CI/CD、GitHub Pages 部署。但当前站点内容单薄（仅 US + Crypto 少量 symbol，无分析文本，无投资建议）。用户要求全面重构前端：中英文双语、8 大市场 76 个标的、基于金融理论的投资建议、回测结果展示。

**核心约束**：
- 纯静态站点（GitHub Pages），无后端
- 服务器 3.8GB RAM，需顺序处理市场
- 每日 4 次 cron 更新（UTC 01/07/13/19）
- 规则引擎生成投资建议 + LLM 润色（可选）

---

## 工作流概览

```
服务器 cron (4x/day)
  → scripts/build_site_data.py（数据采集 + 分析 + JSON 输出）
  → git push data/site_data/ 到 main
  → GitHub Actions deploy_site.yml 触发
  → site_builder 读取 JSON + 报告 → 构建 /en/ 和 /zh/ 双语站点
  → 部署到 gh-pages
```

---

## Workstream 1: 投资建议规则引擎

### 新建文件
| 文件 | 用途 |
|------|------|
| `src/ai_financial_advisor/analysis/advisor.py` | `InvestmentAdvisor` 规则引擎 |
| `tests/test_advisor.py` | 规则引擎测试 |

### `advisor.py` 设计

```python
@dataclass
class InvestmentAdvice:
    action: str           # "Strong Buy" / "Buy" / "Hold" / "Sell" / "Strong Sell"
    confidence: float     # 0.0-1.0
    reasons: list[str]    # 规则触发的原因列表（英文 key）
    risk_level: str       # "Low" / "Medium" / "High"
    summary: str          # 综合建议文本（英文）

class InvestmentAdvisor:
    def analyze(self, df: pd.DataFrame, trend: TrendResult) -> InvestmentAdvice:
        """基于多维度信号生成投资建议"""
```

**规则维度**（每条规则独立评分，加权汇总）：
1. **趋势评分** — 已有 `TrendResult.score`（权重 30%）
2. **RSI 超买超卖** — RSI>70 卖出信号，RSI<30 买入信号（权重 15%）
3. **布林带位置** — 价格触及上/下轨的信号（权重 15%）
4. **MACD 交叉** — MACD 线与信号线交叉（权重 15%）
5. **成交量确认** — OBV/MFI 与价格趋势一致性（权重 10%）
6. **均值回归** — 价格偏离 SMA 程度（权重 15%）

**风险评估**：基于波动率（ATR/价格比）+ 最大回撤

### 关键复用
- `src/ai_financial_advisor/analysis/indicators.py:compute_all_indicators()` — 已计算 RSI、BB、MACD、OBV、MFI
- `src/ai_financial_advisor/analysis/trend_score.py:calculate_trend_score()` — 趋势维度直接复用

---

## Workstream 2: 数据管线脚本

### 新建文件
| 文件 | 用途 |
|------|------|
| `scripts/build_site_data.py` | 数据采集 + 分析 + JSON 输出 |

### 输出结构
```
data/site_data/
├── markets/
│   ├── us.json          # {symbols: [{symbol, close, score, advice, chart_data, ...}]}
│   ├── crypto.json
│   ├── cn.json
│   ├── hk.json
│   ├── eu.json
│   ├── jp.json
│   ├── forex.json
│   └── commodity.json
├── backtest/
│   └── results.json     # 缓存的回测结果（每周刷新）
└── meta.json            # {updated_at, markets_updated: [...]}
```

### 处理流程
```python
for market in MarketType:  # 顺序处理，省内存
    symbols = get_watchlist(market)
    for symbol in symbols:
        df = download_stock_data(symbol, period="6mo")
        df = compute_all_indicators(df)
        trend = calculate_trend_score(df)
        advice = advisor.analyze(df, trend)
        chart_html = generate_candlestick(df)  # 保存到 charts/
        # 存入 JSON
    # 释放内存后处理下一个市场
```

### 回测缓存逻辑
- 检查 `data/site_data/backtest/results.json` 的 `generated_at`
- 如果 <7 天，跳过回测
- 否则对所有 symbol 运行回测并更新

---

## Workstream 3: 国际化 (i18n)

### 新建文件
| 文件 | 用途 |
|------|------|
| `src/ai_financial_advisor/web/i18n/en.json` | 英文翻译 |
| `src/ai_financial_advisor/web/i18n/zh.json` | 中文翻译 |

### 方案：构建时双语
- `SiteBuilder.build()` 接受 `lang` 参数
- 调用两次：`build(lang="en")` → `/en/`，`build(lang="zh")` → `/zh/`
- 根目录 `index.html` 自动重定向到 `/en/`（或浏览器语言检测）
- 翻译 JSON 包含：UI 标签、市场名称、投资建议文本、导航菜单

### 翻译覆盖范围
- 导航：Dashboard / Reports / Market / Backtest
- 投资建议：action 名称、reasons 列表、risk levels
- 市场名称：US Stocks / 美股、Crypto / 加密货币 等
- 指标标签：Trend Score / 趋势评分、MACD Signal / MACD 信号 等

---

## Workstream 4: 站点生成器重构

### 修改文件
| 文件 | 改动 |
|------|------|
| `src/ai_financial_advisor/web/site_builder.py` | 重构：从 JSON 读数据、i18n 支持、新页面类型 |
| `src/ai_financial_advisor/web/templates/base.html` | 添加语言切换器、更新导航 |
| `src/ai_financial_advisor/web/templates/dashboard.html` | 重构：8 市场概览卡片、最新报告、异常警报 |
| `src/ai_financial_advisor/web/templates/market_index.html` | 重构：市场选择器、评分热力图 |
| `src/ai_financial_advisor/web/templates/stock_detail.html` | 重构：分析文本、投资建议卡片、Plotly 图表 |
| `src/ai_financial_advisor/web/templates/report.html` | 保持，微调 |
| `src/ai_financial_advisor/web/assets/style.css` | 大幅更新：响应式布局、新组件样式 |

### 新建模板
| 文件 | 用途 |
|------|------|
| `src/ai_financial_advisor/web/templates/backtest_index.html` | 回测结果汇总页 |
| `src/ai_financial_advisor/web/templates/backtest_detail.html` | 单股回测详情页 |
| `src/ai_financial_advisor/web/templates/redirect.html` | 根目录语言重定向页 |

### 站点输出结构
```
docs/site/
├── index.html              # 语言重定向
├── en/
│   ├── index.html          # Dashboard
│   ├── reports/
│   │   ├── index.html
│   │   └── NR_*.html
│   ├── market/
│   │   ├── index.html      # 8 市场总览
│   │   └── AAPL.html       # 个股详情（含分析 + 建议）
│   └── backtest/
│       ├── index.html      # 回测汇总
│       └── AAPL.html       # 回测详情
├── zh/                     # 同结构中文版
└── assets/
    ├── style.css
    └── charts/             # Plotly HTML 片段
```

### `SiteBuilder` 改动要点
- `__init__` 新增 `data_dir` 参数（指向 `data/site_data/`）
- `build(lang="en")` 从 JSON 加载数据而非接收 Python 对象
- 新增 `_build_backtest()` 方法
- 模板 render 时注入 `t` (翻译函数) 和 `lang` 变量

---

## Workstream 5: 图表生成

### 新建文件
| 文件 | 用途 |
|------|------|
| `src/ai_financial_advisor/web/charts.py` | Plotly 图表生成工具 |

### 图表类型
1. **K 线图 + 成交量** — 个股详情页（`generate_candlestick(df) → html_str`）
2. **权益曲线** — 回测详情页（`generate_equity_curve(result) → html_str`）
3. **迷你趋势线** — 市场总览页（`generate_sparkline(closes) → html_str`）

### 关键复用
- `src/ai_financial_advisor/strategies/visualization.py` — 已有 Plotly 图表代码（`plot_backtest_result`），提取通用逻辑
- 输出方式：`plotly.io.to_html(fig, include_plotlyjs='cdn', full_html=False)`

### 集成方式
- 小图表（sparkline）内联到 JSON 的 `chart_html` 字段
- 大图表（K线、权益曲线）存为独立 HTML 文件在 `data/site_data/charts/`，站点构建时内联或 iframe 引用

---

## Workstream 6: Cron + Deploy 改动

### 修改文件
| 文件 | 改动 |
|------|------|
| `server/crontab.example` | 更新为 4x/day 调度 |
| `.github/workflows/deploy_site.yml` | 简化为 deploy-only（从 JSON 构建站点） |

### Cron 调度（UTC）
```cron
# 4x/day 数据更新 + 站点部署
0 1 * * *  cron_wrapper.sh python scripts/build_site_data.py && git add data/site_data/ && git commit -m "data: update $(date +%Y-%m-%d_%H)" && git push
0 7 * * *  cron_wrapper.sh python scripts/build_site_data.py && git add data/site_data/ && git commit -m "data: update $(date +%Y-%m-%d_%H)" && git push
0 13 * * * cron_wrapper.sh python scripts/build_site_data.py && git add data/site_data/ && git commit -m "data: update $(date +%Y-%m-%d_%H)" && git push
0 19 * * * cron_wrapper.sh python scripts/build_site_data.py && git add data/site_data/ && git commit -m "data: update $(date +%Y-%m-%d_%H)" && git push

# 每日 UTC 07:00 — 新闻报告
0 7 * * * cron_wrapper.sh ai-advisor news run --lang en && git add data/reports/ && git commit -m "daily: news $(date +%Y-%m-%d)" && git push
```

### `deploy_site.yml` 简化
```yaml
name: Deploy Site to GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - "data/site_data/**"
      - "data/reports/**"
      - "src/ai_financial_advisor/web/**"
      - ".github/workflows/deploy_site.yml"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .

      - name: Build site (bilingual)
        run: |
          python -c "
          from pathlib import Path
          from ai_financial_advisor.web.site_builder import SiteBuilder
          builder = SiteBuilder(
              reports_dir=Path('data/reports'),
              output_dir=Path('docs/site'),
              data_dir=Path('data/site_data'),
          )
          builder.build(lang='en')
          builder.build(lang='zh')
          print('Site built: en + zh')
          "

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: docs/site
          destination_dir: .
```

---

## Workstream 7: 测试

### 新建文件
| 文件 | 用途 |
|------|------|
| `tests/test_advisor.py` | 规则引擎测试（各规则独立 + 综合评分） |
| `tests/test_charts.py` | 图表生成测试（输出为有效 HTML） |

### 测试重点
- `InvestmentAdvisor.analyze()` 对不同市场状态返回正确 action
- RSI 超买/超卖边界条件
- 无成交量资产（外汇）的规则降级
- 图表生成不崩溃 + 输出包含 plotly div
- i18n JSON 完整性：en 和 zh 的 key 集合一致

---

## 实施顺序（详细步骤）

### Step 1: 投资建议规则引擎
1. 创建 `src/ai_financial_advisor/analysis/advisor.py`
   - 定义 `InvestmentAdvice` dataclass
   - 实现 `InvestmentAdvisor.analyze()` 方法
   - 6 个规则维度各自独立评分函数
   - 加权汇总 → action 映射（score > 0.6 → Strong Buy, > 0.2 → Buy, etc.）
   - 风险评估函数（波动率 + 回撤）
2. 创建 `tests/test_advisor.py`
   - 测试各规则边界条件
   - 测试综合评分逻辑
   - 测试无成交量数据的降级处理
3. 运行 `pytest tests/test_advisor.py -v` 确认通过

### Step 2: 图表生成工具
1. 创建 `src/ai_financial_advisor/web/charts.py`
   - `generate_candlestick(df, symbol) → str`：K线 + 成交量子图
   - `generate_equity_curve(equity_series, trades) → str`：权益曲线 + 交易标注
   - `generate_sparkline(closes, width=200, height=50) → str`：迷你趋势线
   - 所有函数返回 HTML 字符串（`to_html(include_plotlyjs='cdn', full_html=False)`）
2. 创建 `tests/test_charts.py`
3. 运行测试确认通过

### Step 3: 国际化数据
1. 创建 `src/ai_financial_advisor/web/i18n/en.json`
2. 创建 `src/ai_financial_advisor/web/i18n/zh.json`
3. 确保两个文件的 key 集合完全一致

### Step 4: 数据管线脚本
1. 创建 `scripts/build_site_data.py`
   - 导入 StockAgent、InvestmentAdvisor、charts 模块
   - 顺序遍历 8 个市场的 watchlist
   - 为每个 symbol：下载数据 → 计算指标 → 趋势评分 → 投资建议 → 生成图表
   - 输出 JSON 到 `data/site_data/markets/`
   - 回测缓存逻辑（检查 7 天有效期）
   - 输出 `meta.json`
2. 本地测试运行：`python scripts/build_site_data.py`

### Step 5: 站点生成器重构
1. 重构 `src/ai_financial_advisor/web/site_builder.py`
   - `__init__` 添加 `data_dir` 参数
   - `build(lang="en")` 从 JSON 读取市场数据
   - 添加 i18n 翻译加载逻辑
   - 新增 `_build_backtest()` 方法
   - 新增 `_build_redirect()` 方法（根目录重定向页）
   - 调整所有路径为 `/{lang}/` 前缀

### Step 6: 模板重构
1. 更新 `base.html`：语言切换器、8 市场导航
2. 重构 `dashboard.html`：市场概览卡片（每市场一个卡片，含平均评分 + 迷你图）
3. 重构 `market_index.html`：市场筛选、股票表格（含评分颜色、趋势箭头）
4. 重构 `stock_detail.html`：
   - 投资建议卡片（action + confidence + reasons）
   - 分析文本区域
   - K 线图嵌入
   - 指标数值展示
5. 新建 `backtest_index.html`：回测结果汇总表格
6. 新建 `backtest_detail.html`：权益曲线 + 交易记录 + 绩效指标
7. 新建 `redirect.html`：语言检测 + 重定向

### Step 7: 样式更新
1. 大幅更新 `style.css`
   - 响应式 CSS Grid 布局
   - 投资建议卡片样式（Strong Buy 绿色 → Strong Sell 红色渐变）
   - 图表容器样式
   - 语言切换器样式
   - 移动端适配

### Step 8: Deploy 更新
1. 更新 `.github/workflows/deploy_site.yml`（双语构建，从 JSON 读数据）
2. 更新 `server/crontab.example`（4x/day 调度）
3. 更新服务器 crontab

### Step 9: 端到端验证
1. 本地运行 `python scripts/build_site_data.py`
2. 本地构建站点
3. `python -m http.server -d docs/site 8000` 浏览器验证
4. `pytest -v` 全部通过
5. `ruff check && ruff format --check`
6. git commit + push
7. 确认 GitHub Actions 绿色
8. 确认 GitHub Pages 站点更新

---

## 涉及的所有文件汇总

### 新建文件（~12 个）
```
src/ai_financial_advisor/analysis/advisor.py
src/ai_financial_advisor/web/charts.py
src/ai_financial_advisor/web/i18n/en.json
src/ai_financial_advisor/web/i18n/zh.json
src/ai_financial_advisor/web/templates/backtest_index.html
src/ai_financial_advisor/web/templates/backtest_detail.html
src/ai_financial_advisor/web/templates/redirect.html
scripts/build_site_data.py
tests/test_advisor.py
tests/test_charts.py
```

### 修改文件（~9 个）
```
src/ai_financial_advisor/web/site_builder.py
src/ai_financial_advisor/web/templates/base.html
src/ai_financial_advisor/web/templates/dashboard.html
src/ai_financial_advisor/web/templates/market_index.html
src/ai_financial_advisor/web/templates/stock_detail.html
src/ai_financial_advisor/web/templates/report.html
src/ai_financial_advisor/web/assets/style.css
.github/workflows/deploy_site.yml
server/crontab.example
```
