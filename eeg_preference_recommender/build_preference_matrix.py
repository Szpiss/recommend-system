from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
DL_RESULT_DIR = PROJECT_DIR / "outputs" / "results"
CF_RESULT_DIR = PROJECT_DIR / "results"
MOCK_INTERACTIONS_PATH = DATA_DIR / "mock_interactions.csv"
DL_PREDICTIONS_PATH = DL_RESULT_DIR / "test_predictions.csv"
PREFERENCE_MATRIX_PATH = CF_RESULT_DIR / "preference_matrix.csv"
TRAIN_MATRIX_PATH = CF_RESULT_DIR / "cf_train_matrix.csv"
TEST_INTERACTIONS_PATH = CF_RESULT_DIR / "cf_test_interactions.csv"

RANDOM_SEED = 42


def ensure_mock_data() -> None:
    if MOCK_INTERACTIONS_PATH.exists():
        return
    print("[matrix] mock_interactions.csv not found, generating mock EEG data first...")
    from src.mock_data import generate_mock_data

    generate_mock_data()


def load_preference_source() -> pd.DataFrame:
    """加载 EEG 偏好数据，优先补充深度学习预测分数，基础标签来自模拟 EEG 偏好标签。"""
    ensure_mock_data()
    interactions = pd.read_csv(MOCK_INTERACTIONS_PATH)
    interactions["preference_score"] = interactions["preference_label"].astype(float)
    interactions["feedback_source"] = "mock_eeg_preference_label"

    if DL_PREDICTIONS_PATH.exists():
        predictions = pd.read_csv(DL_PREDICTIONS_PATH)
        pred_cols = ["sample_id", "preference_prob", "predicted_label"]
        interactions = interactions.merge(predictions[pred_cols], on="sample_id", how="left")
        has_pred = interactions["preference_prob"].notna()
        interactions.loc[has_pred, "preference_score"] = interactions.loc[has_pred, "preference_prob"]
        interactions.loc[has_pred, "feedback_source"] = "eeg_deep_learning_prediction"
    else:
        print("[matrix] deep learning predictions not found; using mock EEG labels as implicit feedback.")

    return interactions


def build_full_preference_matrix(interactions: pd.DataFrame) -> pd.DataFrame:
    matrix = interactions.pivot_table(
        index="user_id",
        columns="item_id",
        values="preference_score",
        aggfunc="mean",
    )
    matrix = matrix.sort_index().sort_index(axis=1)
    matrix.index.name = "user_id"
    matrix.columns = [str(col) for col in matrix.columns]
    return matrix


def split_train_test(interactions: pd.DataFrame, test_size: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    """按用户划分测试物品，模拟推荐系统中未交互物品的预测场景。"""
    train_parts: list[pd.DataFrame] = []
    test_parts: list[pd.DataFrame] = []
    for _, group in interactions.groupby("user_id"):
        stratify = group["preference_label"] if group["preference_label"].nunique() > 1 else None
        train, test = train_test_split(
            group,
            test_size=test_size,
            random_state=RANDOM_SEED,
            stratify=stratify,
        )
        train_parts.append(train)
        test_parts.append(test)
    return pd.concat(train_parts, ignore_index=True), pd.concat(test_parts, ignore_index=True)


def build_train_matrix(train_interactions: pd.DataFrame, full_matrix: pd.DataFrame) -> pd.DataFrame:
    train_matrix = full_matrix.copy()
    train_matrix.loc[:, :] = np.nan
    for row in train_interactions.itertuples(index=False):
        train_matrix.loc[row.user_id, str(row.item_id)] = row.preference_score
    return train_matrix


def build_preference_matrices() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    CF_RESULT_DIR.mkdir(parents=True, exist_ok=True)
    interactions = load_preference_source()
    full_matrix = build_full_preference_matrix(interactions)
    train_interactions, test_interactions = split_train_test(interactions)
    train_matrix = build_train_matrix(train_interactions, full_matrix)

    full_matrix.to_csv(PREFERENCE_MATRIX_PATH)
    train_matrix.to_csv(TRAIN_MATRIX_PATH)
    test_interactions.to_csv(TEST_INTERACTIONS_PATH, index=False)

    print(f"[matrix] saved full preference matrix: {PREFERENCE_MATRIX_PATH} shape={full_matrix.shape}")
    print(f"[matrix] saved train matrix with hidden test items: {TRAIN_MATRIX_PATH}")
    print(f"[matrix] saved test interactions: {TEST_INTERACTIONS_PATH} rows={len(test_interactions)}")
    return full_matrix, train_matrix, test_interactions


if __name__ == "__main__":
    build_preference_matrices()

