import sqlite3
import time
from newspaper import Article

# --- 配置 ---
DB_NAME = "news_database.db"

def get_articles_to_scrape():
    """从数据库中获取所有尚未抓取内容的新闻。"""
    print("正在从数据库查找需要抓取内容的文章...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 选取所有 content 字段为空 (NULL) 的条目
    cursor.execute("SELECT id, url FROM articles WHERE content IS NULL")
    
    articles_to_scrape = cursor.fetchall() # fetchall() 获取所有结果
    conn.close()
    
    print(f"找到 {len(articles_to_scrape)} 篇文章需要抓取内容。")
    return articles_to_scrape

def scrape_and_update_article(db_id, url):
    """抓取单个URL的内容并更新到数据库。"""
    print(f"  - 正在处理 ID: {db_id}, URL: {url}")
    
    try:
        # newspaper3k 的核心功能
        article = Article(url, language='en')
        article.download()
        article.parse()
        
        # 提取内容
        full_content = article.text
        # newspaper3k 也能提取作者，可以用来补充我们数据库中的信息
        authors = ', '.join(article.authors)

        # 如果正文内容太短，可能不是有效的新闻，我们也将其视为失败
        if len(full_content) < 100:
            raise ValueError("提取到的内容过短，可能不是有效文章。")

        # --- 如果成功，准备更新数据库 ---
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE articles SET content = ?, author = ? WHERE id = ?",
            (full_content, authors, db_id)
        )
        conn.commit()
        conn.close()
        print(f"    - ID: {db_id} 成功，内容已更新。")
        return True

    except Exception as e:
        # --- 如果失败，也将失败信息更新到数据库，避免重复抓取 ---
        print(f"    - ID: {db_id} 失败: {e}")
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE articles SET content = ? WHERE id = ?",
            ('SCRAPING_FAILED', db_id) # 存入一个失败标记
        )
        conn.commit()
        conn.close()
        return False

# --- 主程序入口 ---
if __name__ == "__main__":
    # 1. 获取任务列表
    articles_list = get_articles_to_scrape()
    
    if not articles_list:
        print("所有文章都已有内容，无需抓取。任务结束。")
    else:
        success_count = 0
        fail_count = 0
        
        # 2. 循环处理每一篇文章
        for i, (article_id, article_url) in enumerate(articles_list):
            print(f"\n--- 处理进度: {i+1}/{len(articles_list)} ---")
            
            result = scrape_and_update_article(article_id, article_url)
            
            if result:
                success_count += 1
            else:
                fail_count += 1
            
            # 礼貌性地停顿1-2秒，避免给对方服务器造成太大压力
            time.sleep(1.5)
            
        print("\n--- 全部任务完成 ---")
        print(f"成功抓取: {success_count} 篇")
        print(f"失败: {fail_count} 篇")