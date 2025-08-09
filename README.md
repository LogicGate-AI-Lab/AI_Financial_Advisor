# AI Financial Advisor

**Vision:** To build a data-driven, personalized intelligent investment advisory system. By integrating massive financial data and leveraging advanced data analysis and AI models, this system provides individual investors with a full-chain service from market insight and stock analysis to personalized investment advice and simulated trading, empowering them to make smarter decisions in the complex financial market.

**Project Status:** [In Development]

## Recent Update

The news agent's global news module has finished development and deployed on Google Cloud, you can visit demo website here:

* [https://jeffliulab.github.io/real_time_demo/ai_financial_advisor/index.html](https://jeffliulab.github.io/real_time_demo/ai_financial_advisor/index.html)

Note: The news agent will **automatically update** on UTC 2:00 **EVERY DAY!**

## Core Modules (Plan, might change)

### 1. Data Layer

* **Data Crawler & Integration Module:**
  * **News Agent:** Automatically scrapes key news from major financial websites (e.g., Sina Finance, Reuters, Bloomberg) daily.
  * **Stock Data API:** Fetches daily/minute-level K-line data, financial reports, etc., from reliable sources like Tushare or Yahoo Finance.
  * **Data Preprocessing:** Cleans, deduplicates, and formats both unstructured text and structured data for analysis.
* **User Profile Module:**
  * Manages user's financial status, risk appetite (from questionnaires), current positions, and portfolio details. Initially, a default profile will be used for development.
* **Database:**
  * Stores user profiles, crawled data, analysis results, and transaction history.

### 2. Analysis Layer

* **Data Analysis & Insight Module:**
  * **Market Sentiment Analysis:** Utilizes NLP to analyze news and generate a market sentiment index (Bullish/Bearish/Neutral).
  * **Technical Indicator Calculation:** Computes key technical indicators like MA, RSI, Bollinger Bands, etc.
  * **Anomaly Detection:** Monitors abnormal changes in price, volume, and sentiment to identify potential opportunities or risks.

### 3. Decision & Strategy Layer

* **Investment Recommendation Module:**
  * The "brain" of the system. It synthesizes user profiles, market sentiment, and technical analysis to generate actionable advice on position adjustments.
* **Peer Recommendation System:**
  * Suggests strategies based on the portfolios of similar users or publicly known successful investors.
* **Simulated Trading Module:**
  * **Auto-Trading (Simulation):** Automatically executes trades in a simulated environment based on the recommendation module's signals.
  * **Quant Strategy Backtesting:** Provides an interface for users to write, test, and evaluate their own quantitative trading strategies using historical data.

### 4. User Interaction Layer

* **Frontend Interface:**
  * A web-based dashboard for users to log in, view their portfolio, check P&L, review investment advice, and access market news.
* **RAG (Retrieval-Augmented Generation) Q&A System:**
  * **Goal:** To act as a 24/7 financial encyclopedia.
  * **Functionality:** Allows users to ask questions in natural language (e.g., "What is quantitative easing?", "Summarize recent news about AAPL") and receive accurate, context-aware answers generated from the system's knowledge base.

## Technology Stack (Plan, might change)

* **Backend:** Python (Flask / Django)
* **Data Science:** Pandas, NumPy, Scikit-learn, TensorFlow/PyTorch
* **Web Scraping:** Scrapy, Requests, BeautifulSoup
* **NLP:** Transformers (Hugging Face), NLTK
* **Quantitative Backtesting:** Backtrader, Zipline
* **Databases:** PostgreSQL (for structured data), MongoDB / Elasticsearch (for unstructured data)
* **Frontend:** React / Vue.js
* **Data Visualization:** ECharts, AntV, D3.js
* **Deployment:** Docker, Nginx, Gunicorn

## Development Roadmap (Plan, might change)

* **Phase 1: MVP (Core Functionality)**
  1. Set up backend framework and databases.
  2. Implement the data crawler for news and stock prices.
  3. Develop a basic analysis module for sentiment and technical indicators.
  4. Create a rule-based recommendation engine with a default user profile.
  5. Build a simple frontend to display analysis and recommendations.
* **Phase 2: User System & Interactivity**
  1. Implement full user registration, login, and profile management.
  2. Personalize recommendations based on individual user data.
  3. Enhance the frontend dashboard with visualizations for portfolio and P&L.
* **Phase 3: Advanced Features**
  1. Develop the simulated trading and backtesting module.
  2. Build a prototype of the Peer Recommendation System.
  3. Integrate the RAG Q&A system.
* **Phase 4: Optimization & Iteration**
  1. Refine algorithms based on user feedback and performance metrics.
  2. Improve system stability and scalability.
  3. Explore advanced AI models like Reinforcement Learning for trading strategies.

## Development History

### News Agent

Currently developing news agent, functions achieved including:

* Automatically search main newspaper, and use LLM to analyze most important macro news and produce a **Daily Global News Report**.
