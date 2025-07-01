import sqlite3
import pandas as pd
from newsapi import NewsApiClient
from datetime import datetime
import os
from dotenv import load_dotenv

# --- 1. 全局配置 ---
DB_NAME = "news_database.db"
load_dotenv()
API_KEY = os.getenv("NEWS_API_API_KEY")

# 健壮性检查：确保API_KEY已成功加载
if not API_KEY:
    raise ValueError("API密钥未找到。请确保您的.env文件中有'NEWSAPI_KEY=your_key'的配置。")


def setup_database():
    """
    初始化数据库和表。如果表不存在，则创建它。
    """
    print("正在初始化数据库...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 使用 IF NOT EXISTS 确保我们不会重复创建表
    # 这段SQL代码定义了我们在上一节中设计的 articles 表结构
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_name TEXT,
        author TEXT,
        title TEXT NOT NULL,
        description TEXT,
        url TEXT UNIQUE,
        content TEXT,
        published_at DATETIME,
        fetched_at DATETIME,
        category TEXT,
        country_or_source TEXT
    );
    """
    cursor.execute(sql_create_table)
    
    # 为 published_at 创建索引以加快未来查询
    sql_create_index = "CREATE INDEX IF NOT EXISTS idx_published_at ON articles (published_at);"
    cursor.execute(sql_create_index)

    conn.commit()
    conn.close()
    print("数据库初始化完毕。")

def fetch_top_headlines():
    """
    从NewsAPI获取全球重要新闻。
    """
    print("正在从 NewsAPI 获取头条新闻...")
    try:
        newsapi = NewsApiClient(api_key=API_KEY)
        
        target_sources = [
            'reuters', 
            'bloomberg', 
            'the-wall-street-journal',
            'financial-times', 
            'the-economist', 
            'business-insider',
            'the-new-york-times',
            'bbc-news',
            'associated-press',
            'the-washington-post',
            'cnn',
            'abc-news',
            'cbs-news',
            'nbc-news',
            'the-verge',
            'techcrunch',
            'wired',
            'ars-technica',
            'engadget'
        ]
        sources_str = ','.join(target_sources)

        top_headlines = newsapi.get_top_headlines(
            sources=sources_str,
            language='en',
            page_size=100
        )
        
        if top_headlines['status'] == 'ok':
            print(f"成功获取到 {len(top_headlines['articles'])} 条新闻。")
            return top_headlines['articles']
        else:
            print(f"API返回错误: {top_headlines.get('message')}")
            return []
            
    except Exception as e:
        print(f"获取新闻时发生错误: {e}")
        return []

def save_articles_to_db(articles):
    """
    将新闻列表保存到SQLite数据库中，并自动处理重复。
    """
    if not articles:
        print("没有新闻需要保存。")
        return

    print("开始将新闻存入数据库...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 使用 INSERT OR IGNORE，如果url已存在，则忽略这次插入
    # url是新闻的地址，代表着独一无二的标识
    sql_insert = """
    INSERT OR IGNORE INTO articles (
        source_name, author, title, description, url, published_at, 
        fetched_at, category, country_or_source
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    
    articles_to_insert = []
    for article in articles:
        # 将API返回的日期字符串转换为datetime对象，再转为ISO格式字符串
        published_dt = None
        if article.get('publishedAt'):
            published_dt = datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00')).isoformat()

        # 准备一个元组(tuple)，顺序必须和SQL语句中的列名一致
        article_tuple = (
            article['source']['name'],
            article.get('author'),
            article['title'],
            article.get('description'), # <-- 获取并保存'description'（摘要）; 因为版权问题不能保存content
            article['url'],
            published_dt,
            datetime.now().isoformat(), # 当前抓取时间
            'business', # 我们查询的是商业新闻
            article['source']['name'] # 记录来源媒体
        )
        articles_to_insert.append(article_tuple)

    # 使用 executemany 一次性插入所有新闻，效率更高
    cursor.executemany(sql_insert, articles_to_insert)
    
    # cursor.rowcount 会返回受影响的行数，即实际新插入的行数
    new_rows_count = cursor.rowcount

    conn.commit()
    conn.close()
    
    print(f"处理完毕。共尝试插入 {len(articles)} 条新闻，实际新插入 {new_rows_count} 条。")
    print(f"{len(articles) - new_rows_count} 条新闻因已存在而被忽略。")


# --- 主程序入口 ---
if __name__ == "__main__":
    # 1. 确保数据库和表已创建
    setup_database()
    
    # 2. 从API获取新闻
    articles_data = fetch_top_headlines()
    
    # 3. 将获取到的新闻保存到数据库
    save_articles_to_db(articles_data)
    
    print("\n任务完成！")