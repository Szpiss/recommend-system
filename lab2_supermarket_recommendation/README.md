# 超市智能商品推荐系统

本项目为“机器学习与推荐系统综合设计”实验二，实现了基于 Amazon 商品评论数据的网页端商品推荐系统。系统包含数据清洗、训练集与测试集划分、唯一商品池构建、用户历史索引、商品向量表示、相似商品检索、基于商品的协同过滤推荐以及模型保存与加载。

## 项目结构

```text
.
├── app.py
├── recommendation_module.py
├── templates/
│   └── index.html
├── requirements.txt
└── README.md
```

`amazon_reviews.csv` 原始数据集体积约 1.1GB，超过 GitHub 单文件限制，未纳入仓库。运行前请将数据文件放在项目根目录。

## 运行方法

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

浏览器访问：

```text
http://127.0.0.1:5000
```

首次启动会自动读取数据并训练推荐模型，生成的缓存保存在 `models/` 目录。再次启动时会优先加载缓存。

如需启用 BERT 语义向量和 Faiss 检索，可额外安装：

```bash
pip install -r requirements-optional.txt
```

## 常用配置

为了便于本地调试，程序支持通过环境变量控制训练规模和向量模型：

```bash
RS_MAX_ROWS=50000 python app.py
RS_MAX_ROWS=2000 RS_USE_SENTENCE_TRANSFORMER=0 python app.py
```

说明：

- `RS_MAX_ROWS`：限制读取的 CSV 行数，默认 50000；设为 0 表示读取全量数据。
- `RS_USE_SENTENCE_TRANSFORMER`：设为 1 时优先使用 SentenceTransformer；设为 0 时使用 sklearn 的文本向量降级实现。
- `RS_EMBEDDING_MODEL`：指定 SentenceTransformer 模型名，默认 `paraphrase-multilingual-MiniLM-L12-v2`。

## 推荐流程

1. 读取 `amazon_reviews.csv`，清洗价格、评分、用户、商品名、品牌、类别等字段。
2. 按用户划分训练集和测试集，避免同一用户同时出现在训练和测试中。
3. 根据商品名和品牌去重，构建唯一商品池和原始商品到唯一商品的映射。
4. 按用户聚合历史评论记录，形成用户历史行为索引。
5. 拼接商品名、品牌、类别和特征文本，生成商品向量。
6. 优先使用 Faiss 建立向量索引；依赖缺失时使用 sklearn 最近邻检索。
7. 根据相似商品矩阵和用户近期历史行为累加候选商品得分。
8. 返回得分最高的商品，并在候选不足时用随机商品补足页面展示数量。
