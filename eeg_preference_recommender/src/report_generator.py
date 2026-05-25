from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import (  # noqa: E402
    EVAL_METRICS_PATH,
    FIGURE_DIR,
    INTERACTIONS_PATH,
    REPORT_DIR,
    TRAIN_HISTORY_PATH,
    ensure_dirs,
)


def _metric_table() -> str:
    if not EVAL_METRICS_PATH.exists():
        return "暂未生成评估指标，请先运行 `python src/evaluate.py`。"
    metrics = pd.read_csv(EVAL_METRICS_PATH).iloc[0].to_dict()
    rows = ["| 指标 | 数值 |", "|---|---:|"]
    for key, value in metrics.items():
        if isinstance(value, float):
            rows.append(f"| {key} | {value:.4f} |")
        else:
            rows.append(f"| {key} | {value} |")
    return "\n".join(rows)


def _data_summary() -> str:
    if not INTERACTIONS_PATH.exists():
        return "当前尚未生成模拟数据。"
    data = pd.read_csv(INTERACTIONS_PATH)
    like_rate = data["preference_label"].mean()
    return (
        f"本实验生成 {data['user_id'].nunique()} 个用户、{data['item_id'].nunique()} 个物品、"
        f"{len(data)} 条用户-物品 EEG 偏好样本；喜欢标签占比为 {like_rate:.2%}。"
    )


def generate_report() -> None:
    ensure_dirs()
    history_note = ""
    if TRAIN_HISTORY_PATH.exists():
        history = pd.read_csv(TRAIN_HISTORY_PATH)
        best_row = history.sort_values("val_accuracy", ascending=False).iloc[0]
        history_note = (
            f"训练共运行 {len(history)} 个 epoch，最佳验证准确率为 "
            f"{best_row['val_accuracy']:.4f}，对应 epoch 为 {int(best_row['epoch'])}。"
        )

    content = f"""# 基于脑信号推断用户偏好的深度学习推荐实验

## 一、实验背景

传统推荐系统主要依赖点击、评分、收藏和浏览时长等行为数据。这些数据容易受到页面位置、曝光策略和用户表达意愿影响，不能完全反映用户即时认知状态。EEG 脑电信号能够记录用户观看内容时的情绪和认知反应，因此可以作为一种更直接的隐式反馈来源。

本实验参考 DEAP 等 EEG 情绪识别数据集的处理思路，将高 valence 近似理解为更强偏好，通过深度学习模型从脑信号中预测用户是否喜欢某个内容，并将预测概率转化为推荐排序分数。

## 二、实验目的

1. 构建可运行的 EEG 偏好识别训练流程；
2. 从 EEG 信号中提取 delta、theta、alpha、beta、gamma 频段功率特征；
3. 使用 PyTorch 搭建 EEGPreferenceNet，输出 preference probability、predicted rating 和兴趣 embedding；
4. 将 EEG 偏好预测分数融合物品流行度，实现 Top-N 推荐；
5. 输出训练指标、推荐指标、可视化图表和报告材料。

## 三、数据集说明

{_data_summary()}

由于本地未包含真实 DEAP 数据集，系统默认使用 `src/mock_data.py` 生成可复现实验数据。模拟数据字段包括 user_id、item_id、eeg_signal、valence_score、arousal_score、preference_label、rating 和 item_popularity_score。信号形状为 channels x time_steps，本实验默认 8 个通道、128 个时间点。

## 四、系统总体流程

数据生成 -> EEG 预处理 -> 频段特征提取 -> CNN 偏好模型训练 -> 测试集分类评估 -> EEG 偏好分数转推荐排序 -> 图表与报告生成。

## 五、EEG 信号预处理方法

预处理阶段先使用移动平均进行轻量平滑，再按样本和通道进行标准化。频段特征提取采用 FFT 近似功率谱密度，统计 delta、theta、alpha、beta、gamma 五类频段的平均功率，用于解释偏好标签与 EEG 频段能量之间的关系。

## 六、深度学习模型结构

模型 `EEGPreferenceNet` 使用 1D CNN 编码 EEG 时间序列。网络由三层卷积、BatchNorm、ReLU、池化和自适应平均池化组成，随后通过 MLP 得到 EEG 兴趣 embedding。输出头包括二分类 preference logits 和归一化 rating 回归分支。训练损失为偏好二分类 BCE 损失加评分 MSE 损失的加权组合。

## 七、基于脑信号的偏好推断方法

模型输入为用户观看某个物品时的 EEG 信号，输出喜欢概率 `preference_prob`。在实验设定中，高 valence、高 alpha/beta/gamma 能量更可能对应喜欢标签。模型学习这种脑信号模式后，可以将实时 EEG 表示转化为用户当前兴趣分数。

## 八、推荐算法设计

推荐阶段对目标用户的候选物品 EEG 样本进行预测，并使用如下排序公式：

```text
score = 0.7 * eeg_preference_score + 0.3 * item_popularity_score
```

其中 EEG 偏好分数体现用户的即时脑信号反馈，物品流行度提供基础兜底。系统输出 Top-N 推荐结果 CSV。

## 九、实验结果与指标分析

{history_note}

{_metric_table()}

从指标看，Accuracy、Precision、Recall、F1-score 和 AUC 用于衡量 EEG 偏好分类能力；HitRate@K、NDCG@K 和 Precision@K 用于衡量推荐列表中命中真实喜欢物品的能力。模拟数据中偏好模式被写入不同频段能量，因此模型通常能够在较少 epoch 内学习到稳定区分信号。

## 十、可视化结果说明

- `outputs/figures/training_loss_curve.png`：训练集和验证集 loss 曲线；
- `outputs/figures/validation_accuracy_curve.png`：验证集 accuracy 曲线；
- `outputs/figures/confusion_matrix.png`：测试集混淆矩阵；
- `outputs/figures/roc_curve.png`：测试集 ROC 曲线；
- `outputs/figures/topn_recommendations.png`：目标用户 Top-N 推荐得分柱状图；
- `outputs/figures/eeg_band_features.png`：不同偏好标签下的 EEG 频段功率对比。

## 十一、实验创新点

1. 将 EEG 脑电信号作为用户隐式反馈；
2. 通过深度学习模型从脑信号中学习用户偏好；
3. 将偏好预测结果转化为推荐系统排序分数；
4. 构建“脑信号感知推荐”的实验型流程；
5. 相比传统点击、评分、浏览记录，EEG 信号能够提供更直接的用户认知和情绪反馈。

## 十二、总结与改进方向

本实验完成了从 EEG 数据生成、信号预处理、深度学习偏好预测到 Top-N 推荐的完整流程。后续可以接入真实 DEAP 或 SEED 数据集，使用更严格的被试独立划分方式，并尝试 CNN-LSTM、Transformer、DeepFM 或 SASRec 等结构，将脑信号特征与用户长期行为序列进一步融合。
"""

    (REPORT_DIR / "experiment_report.md").write_text(content, encoding="utf-8")
    (REPORT_DIR / "report_content.md").write_text(content, encoding="utf-8")
    print(f"[report] saved: {REPORT_DIR / 'experiment_report.md'}")
    print(f"[report] saved: {REPORT_DIR / 'report_content.md'}")


if __name__ == "__main__":
    generate_report()

