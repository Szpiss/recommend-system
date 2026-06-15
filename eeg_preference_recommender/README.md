# 基于脑信号推断用户偏好的推荐实验

本项目是《推荐技术分析与应用》课程实验：使用 EEG 脑电信号推断用户对内容的偏好程度，并将预测偏好分数转化为推荐系统中的 Top-N 排序分数。

当前目录包含两个独立但可关联的实验方向：

- 实验一：基于脑信号推断用户偏好的协同过滤推荐
- 实验二：基于脑信号推断用户偏好的深度学习推荐

协同过滤实验把 EEG 偏好标签或深度学习预测分数转化为 user-item preference matrix，再实现 UserCF 和 ItemCF。深度学习实验使用 PyTorch CNN 直接从 EEG 信号中学习偏好概率，并生成推荐结果。

## 实验创新点

1. 将 EEG 脑电信号作为用户隐式反馈；
2. 通过深度学习模型从脑信号中学习用户偏好；
3. 将偏好预测结果转化为推荐系统排序分数；
4. 构建“脑信号感知推荐”的实验型流程；
5. 相比传统点击、评分、浏览记录，EEG 信号能够提供更直接的用户认知和情绪反馈。

## 项目结构

```text
eeg_preference_recommender/
├── data/
│   ├── raw/
│   ├── processed/
│   └── README.md
├── build_preference_matrix.py
├── collaborative_filtering.py
├── run_cf_experiment.py
├── src/
│   ├── config.py
│   ├── data_loader.py
│   ├── preprocess.py
│   ├── feature_extractor.py
│   ├── model.py
│   ├── train.py
│   ├── evaluate.py
│   ├── recommend.py
│   ├── visualize.py
│   ├── mock_data.py
│   └── report_generator.py
├── outputs/
│   ├── figures/
│   ├── checkpoints/
│   └── results/
├── results/
│   ├── cf_recommendations.csv
│   ├── user_similarity.csv
│   └── item_similarity.csv
├── report/
│   ├── experiment_report.md
│   ├── cf_experiment_report.md
│   └── report_content.md
├── requirements.txt
└── main.py
```

## 安装依赖

```bash
cd /Users/cuing/recommend-system/eeg_preference_recommender
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

如果当前环境已经安装 PyTorch、numpy、pandas、scikit-learn 和 matplotlib，也可以直接使用系统 Python 运行。

## 实验一：协同过滤推荐实验

该实验使用 EEG 信号推断出的用户偏好标签或偏好分数作为隐式反馈，构造用户-物品偏好矩阵，并分别实现：

- User-Based Collaborative Filtering：根据相似用户的偏好推荐物品；
- Item-Based Collaborative Filtering：根据相似物品和用户已喜欢物品进行推荐。

运行命令：

```bash
python run_cf_experiment.py
```

输出文件：

- 用户偏好矩阵：`results/preference_matrix.csv`
- 训练矩阵：`results/cf_train_matrix.csv`
- 测试交互：`results/cf_test_interactions.csv`
- 用户相似度矩阵：`results/user_similarity.csv`
- 物品相似度矩阵：`results/item_similarity.csv`
- 推荐结果：`results/cf_recommendations.csv`
- 评价指标：`results/cf_metrics.csv`
- 实验报告：`report/cf_experiment_report.md`

## 实验二：深度学习推荐实验

该实验使用 PyTorch 搭建 EEGPreferenceNet，从 EEG 信号中学习用户偏好概率、预测评分和兴趣 embedding，再融合物品流行度生成推荐结果。

一键运行：

```bash
python main.py
```

该命令会依次完成：

1. 生成模拟 EEG 数据；
2. 提取 EEG 频段特征；
3. 训练 EEGPreferenceNet；
4. 输出分类与推荐评估指标；
5. 生成 Top-N 推荐结果；
6. 生成可视化图表和实验报告。

深度学习实验分步运行：

```bash
python src/mock_data.py
python src/feature_extractor.py
python src/train.py
python src/evaluate.py
python src/recommend.py --user_id 1 --top_k 10
python src/visualize.py
python src/report_generator.py
```

## 输出文件

- 训练模型：`outputs/checkpoints/eeg_preference_net.pt`
- 训练曲线数据：`outputs/results/train_history.csv`
- 测试集预测结果：`outputs/results/test_predictions.csv`
- 评估指标：`outputs/results/evaluation_metrics.csv`
- 推荐结果：`outputs/results/recommendations.csv`
- 可视化图表：`outputs/figures/*.png`
- 实验报告：`report/experiment_report.md`
- Word 复制版报告：`report/report_content.md`

## 方法说明

系统默认生成 20 个用户、100 个物品和 2000 条用户-物品 EEG 样本。模拟信号参考 DEAP 情绪识别思路，将高 valence 视作更强偏好，并让 alpha、beta、gamma 频段能量与喜欢概率呈正相关。模型使用 1D CNN 提取 EEG 时序特征，输出喜欢概率、预测评分和兴趣 embedding。

推荐排序公式为：

```text
score = 0.7 * eeg_preference_score + 0.3 * item_popularity_score
```

其中 `eeg_preference_score` 来自深度学习模型，`item_popularity_score` 是物品流行度兜底分数。
