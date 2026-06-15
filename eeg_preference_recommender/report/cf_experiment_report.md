# 基于脑信号推断用户偏好的协同过滤推荐实验

## 一、实验目的

本实验在现有 EEG 深度学习推荐实验之外，新增一条传统推荐算法路线：将脑信号推断出的用户偏好标签或偏好分数转化为用户-物品偏好矩阵，并基于该矩阵实现 User-Based Collaborative Filtering 和 Item-Based Collaborative Filtering。

## 二、数据说明

本实验采用模拟脑信号特征与偏好标签，用于验证算法流程。数据来自 `data/processed/mock_interactions.csv`，每条记录包含 user_id、item_id、valence_score、arousal_score、preference_label 和 rating 等字段。若本地已存在深度学习预测文件 `outputs/results/test_predictions.csv`，程序会优先把其中的 `preference_prob` 作为部分样本的偏好分数；其他样本继续使用模拟 EEG 偏好标签。

## 三、偏好矩阵构造

- 用户数量：20
- 物品数量：100
- 训练矩阵已知反馈数：1600
- 测试隐藏反馈数：400
- 训练矩阵密度：80.00%

喜欢记为 1，不喜欢记为 0。为了模拟推荐场景，程序按用户隐藏约 20% 的物品作为测试集，在训练矩阵中将这些位置保留为空值 NaN，随后由协同过滤算法预测并推荐。

## 四、算法设计

### 1. UserCF

UserCF 使用用户-物品偏好矩阵计算用户之间的余弦相似度。对于目标用户，选择相似用户的历史偏好作为参考，对目标用户未见物品进行加权打分。

### 2. ItemCF

ItemCF 使用物品在不同用户上的偏好向量计算物品之间的余弦相似度。对于目标用户，根据其已喜欢物品寻找相似物品，并生成 Top-N 推荐结果。

## 五、实验输出

- 用户偏好矩阵：`results/preference_matrix.csv`
- 训练矩阵：`results/cf_train_matrix.csv`
- 测试集：`results/cf_test_interactions.csv`
- 用户相似度矩阵：`results/user_similarity.csv`
- 物品相似度矩阵：`results/item_similarity.csv`
- 推荐结果：`results/cf_recommendations.csv`
- 评价指标：`results/cf_metrics.csv`

## 六、评价指标

| algorithm | Precision@10 | Recall@10 | HitRate@10 |
| --- | --- | --- | --- |
| ItemCF | 0.6450 | 0.5422 | 1.0000 |
| UserCF | 0.6650 | 0.5589 | 1.0000 |

Precision@K 表示推荐列表中真正喜欢物品的占比，Recall@K 表示用户真实喜欢物品被推荐命中的比例，HitRate@K 表示推荐列表是否至少命中一个喜欢物品。

## 七、推荐结果样例

| algorithm | user_id | rank | item_id | score |
| --- | --- | --- | --- | --- |
| UserCF | 1 | 1 | 75 | 0.8813 |
| UserCF | 1 | 2 | 90 | 0.7839 |
| UserCF | 1 | 3 | 88 | 0.7675 |
| UserCF | 1 | 4 | 44 | 0.6951 |
| UserCF | 1 | 5 | 23 | 0.5984 |
| UserCF | 1 | 6 | 51 | 0.5819 |
| UserCF | 1 | 7 | 20 | 0.5427 |
| UserCF | 1 | 8 | 43 | 0.4968 |
| UserCF | 1 | 9 | 49 | 0.4670 |
| UserCF | 1 | 10 | 34 | 0.4493 |
| UserCF | 2 | 1 | 58 | 0.7898 |
| UserCF | 2 | 2 | 91 | 0.7889 |

## 八、实验总结

本实验说明 EEG 偏好标签不仅可以用于深度学习分类模型，也可以转化为传统协同过滤算法的隐式反馈矩阵。与深度学习推荐相比，协同过滤实现更简单、解释性更强；不足是当用户或物品历史反馈较少时，容易受到数据稀疏问题影响。后续可以将 EEG 深度学习预测分数、协同过滤分数和物品内容特征进行融合，形成更完整的混合推荐系统。
