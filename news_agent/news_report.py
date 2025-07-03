# import os
import sqlite3
import os
from dotenv import load_dotenv
from openai import OpenAI # The library is the same
from datetime import date, timedelta

"""
目前可能存在的问题：
1、LIMIT 100 条，尚不确定是否被完整处理
2、生成的结果稍微有点超出deepseek的处理能力, 但是只超出一点点。
"""

"""
程序总结：
1、获取news_database.db中前一天的新闻内容
2、将内容发送给LLM, 让LLM整理为报告并保存
"""

# --- Configuration ---
DB_NAME = "news_database.db"
REPORTS_DIR = "news_report" # 定义报告存放的文件夹名称
 

def get_news_for_date(target_date_str: str):
    """从数据库中获取指定日期、且内容不为空的新闻。"""
    print(f"正在从数据库读取 {target_date_str} 的新闻...")
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()

    query = """
    SELECT title, description, content, source_name,url
    FROM articles
    WHERE date(published_at) = ? 
      AND content IS NOT NULL 
      AND content != 'SCRAPING_FAILED'
    LIMIT 100;
    """
    
    cursor.execute(query, (target_date_str,))
    articles = cursor.fetchall()
    conn.close()
    
    print(f"找到 {len(articles)} 篇内容完整的相关新闻。")
    return articles

def format_prompt_for_llm(articles):
    """将新闻数据格式化为适合LLM的单个提示字符串。"""
    if not articles:
        return None

    prompt_header = """
        你是一位资深的金融分析师。你的工作是根据收集到的新闻，整理一个要闻列表。

        在整理的时候，你要注意：
        1、如果多条报道在说同一件事情, 那么这件事情作为一件事情展示; 并且报道越多的事情越重要, 你要越重视
        2、特别关注财经相关的内容, 所有财经相关的内容都不能省略掉


        整理完后你要出一份《全球要闻报告》，报告内容包括：
        1、今日新闻概览:
        (1)总结当日最重要的新闻。
        (2)提供一个整体乐观和整体悲观的指标，如果大多数都是有利于市场的新闻，就评价为整体乐观；如果没什么特别的，就评价为整体平稳；如果负面较多，则评价为整体悲观。
        2、重要新闻详情:总结当天新闻中最重要的关于金融、市场、财经、宏观等多方面的内容。不少于10条。
        3、重点板块与公司新闻: 说明哪些公司可能会受到影响，只需要列出公司名字和简要原因即可。
        4、值得关注的信号: 分析当日新闻中最可能影响未来市场的信息。不少于3条。
        5、其他新闻: 和上面主要分析的无关内容但是出现在今天新闻中的，全部收集在这里，不要有任何的遗漏，简单整理即可。

        报告语言应专业、简洁、中立客观。对于专有名词, 保留原英文以防翻译错误。
        在报告的最后将你引用的新闻按照标号记录其对应的链接，方便用户点开查看。

        以下是今天的新闻资料：
        ---
        """
    
    news_body = ""
    for i, article in enumerate(articles):
        # 对content内容进行截取
        content_snippet = article['content'][:1500] if article['content'] else ""
        
        news_body += f"""
                        新闻 {i+1}:
                        新闻来源: {article['source_name']}
                        标题: {article['title']}
                        URL" {article['url']}
                        摘要: {article['description']}
                        内容片段: {content_snippet}...

                        ---
                        """
    
    return prompt_header + news_body

def generate_report_with_deepseek(prompt):
    """
    使用 DeepSeek API (通过OpenAI SDK) 生成报告。
    """
    print("正在连接 DeepSeek API 并生成报告...")
    try:
        # 从.env文件加载环境变量
        load_dotenv()
        api_key = os.getenv("DEEPSEEK_API_KEY") # <-- 使用新的环境变量
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY 未在.env文件中设置。")

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com" # <-- 指定DeepSeek的API地址
        )
            
        response = client.chat.completions.create(
            # * deepseek-chat 模型指向 DeepSeek-V3-0324, 通过指定 model='deepseek-chat' 调用。
            # * deepseek-reasoner 模型指向 DeepSeek-R1-0528, 通过指定 model='deepseek-reasoner' 调用。
            model="deepseek-reasoner",  # <-- 使用DeepSeek的模型
            messages=[
                {"role": "system", "content": "你是一位资深的金融分析师。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=8192, # 注意这个是回复token的数量，8192是一个比较安全的设置
            stream=False # 确保使用非流式输出
        )
        
        report = response.choices[0].message.content
        return report
        
    except Exception as e:
        print(f"调用 DeepSeek API 时发生错误: {e}")
        return None

# --- 主程序入口 ---
if __name__ == "__main__":
    # 默认分析前一天的新闻
    target_date = date.today() - timedelta(days=1)
    target_date_str = target_date.strftime("%Y-%m-%d")
    
    # 1. 从数据库获取数据
    news_articles = get_news_for_date(target_date_str)
    
    if news_articles:
        # 2. 格式化为Prompt
        final_prompt = format_prompt_for_llm(news_articles)
        
        if final_prompt:
            # 3. 调用LLM生成报告
            final_report = generate_report_with_deepseek(final_prompt)
            
            if final_report:
                print("\n\n" + "="*30)
                print(f"  DeepSeek 生成的财经市场报告 ({target_date_str})")
                print("="*30 + "\n")
                print(final_report)

                # --- ✅【文件保存】 ---
                # 1. 确保报告文件夹存在
                os.makedirs(REPORTS_DIR, exist_ok=True)
                
                # 2. 按照您指定的格式创建文件名
                report_filename = f"NR_{target_date_str}.md"
                report_filepath = os.path.join(REPORTS_DIR, report_filename)
                
                # 3. 将报告写入文件
                try:
                    with open(report_filepath, 'w', encoding='utf-8') as f:
                        f.write(f"# 全球重要新闻每日快报 ({target_date_str})\n\n") # 在文件开头加上一级标题
                        f.write(final_report)
                    print(f"\n✅ 报告也已成功保存到文件: {report_filepath}")
                except Exception as e:
                    print(f"\n❌ 保存文件时出错: {e}")
    else:
        print(f"数据库中没有找到 {target_date_str} 的可分析新闻。")