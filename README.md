# 推荐系统课程实验仓库

本仓库统一整理推荐系统相关课程实验和扩展项目，避免同一课程内容分散在多个仓库中。当前包含图书推荐、超市商品推荐和 EEG 脑信号偏好推荐三个方向，均保留可运行代码、依赖说明和报告材料。

## 实验总览

| 模块 | 目录 | 主要内容 | 运行入口 |
| --- | --- | --- | --- |
| 实验一：图书推荐系统 | 根目录 | 基于 Book-Crossing 数据集的热门推荐和用户协同过滤推荐 | `python main.py` |
| 实验二：超市智能商品推荐系统 | `lab2_supermarket_recommendation/` | 基于 Amazon 评论数据的商品向量、相似商品检索和网页推荐系统 | `python app.py` |
| 扩展实验：EEG 偏好推荐 | `eeg_preference_recommender/` | 模拟 EEG 数据、频段特征、PyTorch CNN 分类和 Top-N 推荐 | `python main.py` |

## 仓库结构

```text
recommend-system/
├── main.py                              # 图书推荐系统主程序
├── 实验代码.py                           # 图书推荐兼容入口
├── 实验报告.md                           # 图书推荐实验报告
├── 作业说明.md                           # 图书推荐提交说明
├── data/                                # Book-Crossing 图书数据
├── output/                              # 图书推荐运行输出
├── lab2_supermarket_recommendation/     # 实验二：超市商品推荐系统
│   ├── app.py                           # Flask Web 入口
│   ├── recommendation_module.py          # 推荐算法和模型缓存逻辑
│   ├── templates/index.html              # 页面模板
│   ├── requirements.txt                  # 基础依赖
│   ├── requirements-optional.txt         # BERT/Faiss 可选依赖
│   └── 实验二报告.docx
└── eeg_preference_recommender/           # EEG 脑信号偏好推荐扩展实验
    ├── main.py
    ├── src/
    ├── data/
    ├── outputs/
    └── report/
```

## 实验一：图书推荐系统

实验一使用 Book-Crossing 数据集，主要实现两类推荐：

- 热门图书推荐：按有效评分数量和平均评分筛选适合兜底展示的图书。
- 用户协同过滤推荐：根据用户评分相似度寻找相似用户，再从相似用户喜欢但目标用户未评分的图书中生成推荐。

运行方式：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

指定用户和推荐数量：

```bash
python main.py --user-id 11676 --topn 10
```

运行结果会输出到终端，并保存到：

```text
output/demo_result.txt
```

## 实验二：超市智能商品推荐系统

实验二原先独立放在 `recommend-system-lab2` 仓库中，现已合并到本仓库的 `lab2_supermarket_recommendation/` 目录，作为同一门推荐系统课程的第二个实验。

功能流程：

1. 读取 `amazon_reviews.csv` 商品评论数据。
2. 清洗价格、评分、用户、商品名、品牌和类别字段。
3. 按用户划分训练集和测试集，避免同一用户同时出现在训练和测试中。
4. 构建唯一商品池和用户历史行为索引。
5. 使用商品文本信息生成向量表示。
6. 优先使用 Faiss 检索相似商品，依赖缺失时降级到 sklearn 最近邻。
7. 根据用户近期历史商品聚合候选分数，返回 Top-N 推荐。

运行方式：

```bash
cd lab2_supermarket_recommendation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

浏览器访问：

```text
http://127.0.0.1:5000
```

数据文件说明：

- `amazon_reviews.csv` 原始数据集约 1.1GB，超过 GitHub 单文件限制，未纳入仓库。
- 运行前请把数据文件放到 `lab2_supermarket_recommendation/` 根目录。
- 首次启动会训练并生成 `models/` 缓存，再次启动会优先加载缓存。

常用调试参数：

```bash
RS_MAX_ROWS=50000 python app.py
RS_MAX_ROWS=2000 RS_USE_SENTENCE_TRANSFORMER=0 python app.py
```

## 扩展实验：EEG 脑信号偏好推荐

`eeg_preference_recommender/` 是一个独立的深度学习推荐实验，使用模拟脑电数据提取频段特征，通过 PyTorch CNN 推断偏好类别，并生成 Top-N 推荐结果。

运行方式：

```bash
cd eeg_preference_recommender
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

报告位置：

```text
eeg_preference_recommender/report/experiment_report.md
```

## 提交与维护说明

- 同一推荐系统课程的实验统一放在本仓库中，后续不再新建 `recommend-system-lab*` 之类的重复仓库。
- 大体积原始数据不提交到 GitHub，只保留数据字段说明、运行步骤和可复现代码。
- 每个实验目录应保留独立 README 或报告，根 README 负责总览、导航和课程归档说明。
