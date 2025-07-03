# news_agent

news agent aims to get all financial news and extract key words into database.

RUN SCRIPTS IN FOLLOWING SEQUENCE:

1. api_NewsApi.py: get newest news, store in database
2. api_newsapi_newspaper3k.py: get the contents of the news, store in database
3. news_report.py: use LLM to analyze news and get the news report (of last day)

## core api scripts

## database

newsapi_articles.db, store NewsApi's top news.
