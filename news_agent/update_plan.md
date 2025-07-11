因为NG面试，所以暂时停止项目更新。

用google云存储存储json文件，设计ETL数据工程。


```
your-news-bucket/
│
├── raw/
│   │   # 存放从API直接获取、未经任何处理的原始数据
│   └── daily/
│       ├── 2025-07-11/
│       │   └── raw_articles_2025-07-11.json
│       └── 2025-07-12/
│           └── raw_articles_2025-07-12.json
│
├── processed/
│   │   # 存放经过清洗、抓取、丰富后的中间数据
│   └── daily/
│       ├── 2025-07-11/
│       │   └── cleaned_articles_2025-07-11.json
│       └── 2025-07-12/
│           └── cleaned_articles_2025-07-12.json
│
└── reports/
    │   # 存放最终生成的、可供前端访问的报告
    └── daily/
        ├── 2025-07-11/
        │   └── report_2025-07-11.md
        └── 2025-07-12/
            └── report_2025-07-12.md
```


接下来的步骤：

1、进入google cloud storage

2、创建存储bucket

3、创建目录结构

4、设置生命周期，实现自动删除等


