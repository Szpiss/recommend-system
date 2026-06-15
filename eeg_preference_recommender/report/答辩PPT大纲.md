# EEG 脑信号偏好推荐实验答辩 PPT 大纲

## 第 1 页：题目与实验目标

- 用 EEG 脑电信号预测用户是否喜欢内容。
- 模型输出偏好概率和预测评分。
- 将偏好概率转成推荐排序分数。

## 第 2 页：系统功能

- 自动生成模拟 EEG 数据。
- 完成 EEG 标准化、滤波和频段特征提取。
- 训练 EEGPreferenceNet。
- 输出分类评估指标和 Top-N 推荐结果。
- 自动生成图表和实验报告。

## 第 3 页：实现技术

- 使用 PyTorch 搭建 1D CNN 模型。
- 使用 FFT/PSD 思路提取 delta、theta、alpha、beta、gamma 频段功率。
- 模型输出 preference_prob、predicted_rating 和 embedding。
- 推荐公式：score = 0.7 * eeg_preference_score + 0.3 * item_popularity_score。

## 第 4 页：实验结果

- Accuracy = 0.820。
- F1-score = 0.862。
- AUC = 0.919。
- HitRate@10 = 1.000。
- NDCG@10 = 0.935。

## 第 5 页：总结与改进

- 项目跑通了从脑信号到推荐结果的完整流程。
- 创新点是把 EEG 作为隐式反馈，比点击、评分更接近用户即时认知状态。
- 后续可以接入真实 DEAP/SEED 数据集，并尝试 CNN-LSTM 或 Transformer。
