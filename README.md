# 图书推荐系统课程实验

这是一个基于 `Book-Crossing` 数据集完成的图书推荐小项目，适合作为推荐系统课程实验提交。

## 新增：EEG 脑信号偏好推荐实验

本仓库另补充了一个独立的深度学习推荐实验目录：

- `eeg_preference_recommender/`：基于脑信号推断用户偏好的推荐系统实验
- 支持模拟 EEG 数据、频段特征提取、PyTorch CNN 训练、分类评估、Top-N 推荐和报告生成
- 一键运行入口：`cd eeg_preference_recommender && python main.py`
- 实验报告：`eeg_preference_recommender/report/experiment_report.md`

下面是原图书推荐系统实验说明。


项目尽量保持简单，主要做了两件事：

1. 热门图书推荐
2. 基于用户评分的简单协同过滤推荐

默认直接运行就会自动选择一个评分记录较多的用户，输出一组可展示的推荐结果，方便答辩时演示。

## 项目结构

- `main.py`：主程序
- `实验代码.py`：兼容入口，内部直接调用 `main.py`
- `data/`：原始图书数据
- `output/`：程序运行后保存的推荐结果
- `README.md`：项目说明
- `实验报告.md`：课程实验报告
- `作业说明.md`：提交文件说明
- `requirements.txt`：依赖列表

## 数据集说明

本项目使用 `Book-Crossing` 数据集，主要文件有：

- `data/BX-Users.csv`
- `data/BX-Books.csv`
- `data/BX-Book-Ratings.csv`

程序会读取用户、图书、评分三张表，其中推荐主要使用评分数据。

## 推荐思路

为了保证代码容易理解，这里没有做复杂模型，而是用了一个比较基础的方案。

1. 先清洗数据，只保留有效评分记录。
2. 去掉评分次数过少的用户和图书，减少噪声。
3. 对目标用户找到和他评分习惯接近的相似用户。
4. 从相似用户喜欢但目标用户还没看过的图书里挑出推荐结果。
5. 如果指定用户数据太少，就退回到热门图书推荐。

## 运行方法

先创建虚拟环境并安装依赖：

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

直接运行默认演示：

```bash
.venv/bin/python main.py
```

也可以指定用户：

```bash
.venv/bin/python main.py --user-id 11676 --topn 10
```

如果想继续使用原来的命令名，也可以：

```bash
.venv/bin/python 实验代码.py
```

## 运行结果

程序会在终端打印：

- 数据集清洗后的规模
- 默认演示用户
- 个性化推荐结果
- 热门图书推荐结果

同时会把结果保存到：

- `output/demo_result.txt`

## 适合答辩时怎么讲

可以按这个顺序讲：

1. 我先用了 Book-Crossing 图书评分数据。
2. 因为原始数据比较杂，所以先做了简单清洗。
3. 推荐部分我用了最基础的用户协同过滤，优点是容易理解。
4. 如果用户历史评分太少，系统就用热门图书推荐兜底。
5. 这样做虽然不复杂，但结构完整，能够正常跑通并输出结果。
