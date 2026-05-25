# 数据说明

本目录用于保存 EEG 偏好推荐实验数据。

- `raw/`：可放置真实 DEAP 或其他 EEG 数据集原始文件。
- `processed/mock_interactions.csv`：模拟用户-物品 EEG 偏好样本。
- `processed/mock_eeg_signals.npz`：模拟 EEG 信号数组，形状为 `samples x channels x time_steps`。
- `processed/band_features.csv`：delta、theta、alpha、beta、gamma 频段功率特征。

如果没有真实 EEG 数据，运行 `python src/mock_data.py` 会自动生成可复现实验数据。

