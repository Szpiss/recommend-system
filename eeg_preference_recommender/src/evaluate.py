from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from torch.utils.data import DataLoader

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import (  # noqa: E402
    BATCH_SIZE,
    EMBEDDING_DIM,
    EVAL_METRICS_PATH,
    MODEL_PATH,
    N_CHANNELS,
    PREDICTIONS_PATH,
    TOP_K,
    ensure_dirs,
)
from src.data_loader import EEGPreferenceDataset, load_interactions_and_signals, load_split  # noqa: E402
from src.model import EEGPreferenceNet  # noqa: E402


def load_model(device: torch.device | None = None) -> EEGPreferenceNet:
    device = device or torch.device("cpu")
    model = EEGPreferenceNet(n_channels=N_CHANNELS, embedding_dim=EMBEDDING_DIM).to(device)
    if not MODEL_PATH.exists():
        from src.train import train_model

        train_model()
    checkpoint = torch.load(MODEL_PATH, map_location=device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    return model


def predict_split(split_name: str = "test") -> pd.DataFrame:
    ensure_dirs()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    interactions, signals = load_split(split_name)
    loader = DataLoader(EEGPreferenceDataset(interactions, signals), batch_size=BATCH_SIZE)
    model = load_model(device)
    probs, ratings = [], []
    with torch.no_grad():
        for batch in loader:
            output = model(batch["eeg"].to(device))
            probs.extend(output["preference_prob"].detach().cpu().numpy().tolist())
            ratings.extend(output["predicted_rating"].detach().cpu().numpy().tolist())
    predictions = interactions.copy()
    predictions["preference_prob"] = probs
    predictions["predicted_rating"] = ratings
    predictions["predicted_label"] = (predictions["preference_prob"] >= 0.5).astype(int)
    predictions.to_csv(PREDICTIONS_PATH, index=False)
    print(f"[evaluate] saved predictions: {PREDICTIONS_PATH}")
    return predictions


def recommendation_metrics(predictions: pd.DataFrame, k: int = TOP_K) -> dict[str, float]:
    hits, ndcgs, precisions = [], [], []
    for _, group in predictions.groupby("user_id"):
        ranked = group.sort_values("preference_prob", ascending=False).head(k)
        relevant = set(group.loc[group["preference_label"] == 1, "item_id"])
        if not relevant:
            continue
        recommended = ranked["item_id"].tolist()
        hit_vector = [1 if item in relevant else 0 for item in recommended]
        hits.append(float(any(hit_vector)))
        precisions.append(float(np.mean(hit_vector)))
        dcg = sum(hit / np.log2(idx + 2) for idx, hit in enumerate(hit_vector))
        ideal_hits = [1] * min(len(relevant), k)
        idcg = sum(hit / np.log2(idx + 2) for idx, hit in enumerate(ideal_hits))
        ndcgs.append(float(dcg / idcg) if idcg > 0 else 0.0)
    return {
        f"HitRate@{k}": float(np.mean(hits)) if hits else 0.0,
        f"NDCG@{k}": float(np.mean(ndcgs)) if ndcgs else 0.0,
        f"Precision@{k}": float(np.mean(precisions)) if precisions else 0.0,
    }


def evaluate_model() -> pd.DataFrame:
    predictions = predict_split("test")
    y_true = predictions["preference_label"].to_numpy()
    y_pred = predictions["predicted_label"].to_numpy()
    y_prob = predictions["preference_prob"].to_numpy()
    rec_metrics = recommendation_metrics(predictions)
    matrix = confusion_matrix(y_true, y_pred).ravel()
    tn, fp, fn, tp = matrix if len(matrix) == 4 else (0, 0, 0, 0)
    metrics = {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, zero_division=0),
        "Recall": recall_score(y_true, y_pred, zero_division=0),
        "F1-score": f1_score(y_true, y_pred, zero_division=0),
        "AUC": roc_auc_score(y_true, y_prob) if len(np.unique(y_true)) > 1 else 0.0,
        "Confusion_TN": tn,
        "Confusion_FP": fp,
        "Confusion_FN": fn,
        "Confusion_TP": tp,
        **rec_metrics,
    }
    metrics_df = pd.DataFrame([metrics])
    metrics_df.to_csv(EVAL_METRICS_PATH, index=False)
    print(f"[evaluate] saved metrics: {EVAL_METRICS_PATH}")
    print(metrics_df.round(4).to_string(index=False))
    return metrics_df


if __name__ == "__main__":
    evaluate_model()

