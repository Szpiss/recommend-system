# 推荐系统课程实验仓库

本仓库统一整理推荐系统相关课程实验和扩展项目，避免同一课程内容分散在多个仓库中。当前包含图书推荐、超市商品推荐、EEG 脑信号偏好推荐和奥运奖牌数据可视化实验，均保留可运行代码、依赖说明、结果产物和报告材料。

## 实验总览

| 模块 | 目录 | 主要内容 | 运行入口 |
| --- | --- | --- | --- |
| 实验一：图书推荐系统 | 根目录 | 基于 Book-Crossing 数据集的热门推荐和用户协同过滤推荐 | `python main.py` |
| 实验二：超市智能商品推荐系统 | `lab2_supermarket_recommendation/` | 基于 Amazon 评论数据的商品向量、相似商品检索和网页推荐系统 | `python app.py` |
| 扩展实验：EEG 偏好推荐 | `eeg_preference_recommender/` | EEG 偏好矩阵、UserCF/ItemCF、PyTorch CNN 偏好预测和 Top-N 推荐 | `python main.py` / `python run_cf_experiment.py` |
| 数据可视化实验：奥运奖牌故事 | `olympic_medal_story/` | 东京奥运会奖牌数据清洗、交互图表和可视化总览页面 | `python olympic_medal_story.py` |

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
├── eeg_preference_recommender/          # EEG 脑信号偏好推荐扩展实验
└── olympic_medal_story/                 # 奥运奖牌数据可视化实验
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

`eeg_preference_recommender/` 是一个独立的推荐系统扩展实验，包含两个方向：

- 协同过滤推荐：基于 EEG 偏好标签构造 user-item preference matrix，并实现 UserCF 和 ItemCF。
- 深度学习推荐：使用模拟脑电数据提取频段特征，通过 PyTorch CNN 推断偏好类别，并生成 Top-N 推荐结果。

运行方式：

```bash
cd eeg_preference_recommender
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_cf_experiment.py
python main.py
```

报告位置：

```text
eeg_preference_recommender/report/experiment_report.md
eeg_preference_recommender/report/cf_experiment_report.md
```

## 数据可视化实验：奥运奖牌故事

`olympic_medal_story/` 用东京奥运会奖牌数据生成一组可展示图表，包括：

- 各国家奖牌总数 Top10 柱状图
- 各项目金牌分布饼图
- 获奖时间与奖牌数量关系折线图
- 子项目获奖名次分布热力图
- 运动员获奖金牌时间轴
- 金牌国家与项目关联桑基图

运行方式：

```bash
python olympic_medal_story/olympic_medal_story.py
```

汇总页面：

```text
olympic_medal_story/output/charts/东京奥运会奖牌数据可视化总览.html
```

## 提交与维护说明

- 同一推荐系统课程的实验统一放在本仓库中，后续不再新建 `recommend-system-lab*` 之类的重复仓库。
- 大体积原始数据谨慎提交；超过 GitHub 限制的数据应保留字段说明、运行步骤和获取方式。
- 每个实验目录应保留独立 README 或报告，根 README 负责总览、导航和课程归档说明。
