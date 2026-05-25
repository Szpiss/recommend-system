from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay, RocCurveDisplay

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import (  # noqa: E402
    FEATURES_PATH,
    FIGURE_DIR,
    PREDICTIONS_PATH,
    RECOMMENDATION_PATH,
    TRAIN_HISTORY_PATH,
    ensure_dirs,
)
from src.evaluate import evaluate_model  # noqa: E402
from src.feature_extractor import build_feature_table  # noqa: E402
from src.recommend import recommend_for_user  # noqa: E402


plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def plot_training_curves() -> None:
    history = pd.read_csv(TRAIN_HISTORY_PATH)
    plt.figure(figsize=(8, 4.5))
    plt.plot(history["epoch"], history["train_loss"], marker="o", label="train loss")
    plt.plot(history["epoch"], history["val_loss"], marker="o", label="val loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("Training and Validation Loss")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "training_loss_curve.png", dpi=160)
    plt.close()

    plt.figure(figsize=(8, 4.5))
    plt.plot(history["epoch"], history["val_accuracy"], marker="o", color="#2a9d8f")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.title("Validation Accuracy")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "validation_accuracy_curve.png", dpi=160)
    plt.close()


def plot_evaluation_figures() -> None:
    if not PREDICTIONS_PATH.exists():
        evaluate_model()
    predictions = pd.read_csv(PREDICTIONS_PATH)
    y_true = predictions["preference_label"]
    y_pred = predictions["predicted_label"]
    y_prob = predictions["preference_prob"]

    ConfusionMatrixDisplay.from_predictions(y_true, y_pred, cmap="Blues")
    plt.title("Preference Classification Confusion Matrix")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "confusion_matrix.png", dpi=160)
    plt.close()

    RocCurveDisplay.from_predictions(y_true, y_prob)
    plt.title("ROC Curve")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "roc_curve.png", dpi=160)
    plt.close()


def plot_recommendations() -> None:
    if not RECOMMENDATION_PATH.exists():
        recommend_for_user(1, 10)
    recommendations = pd.read_csv(RECOMMENDATION_PATH)
    plt.figure(figsize=(9, 4.8))
    labels = recommendations.get("item_name", recommendations["item_id"]).astype(str)
    plt.bar(labels, recommendations["ranking_score"], color="#457b9d")
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Ranking Score")
    plt.title("Top-N Recommendation Scores")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "topn_recommendations.png", dpi=160)
    plt.close()


def plot_band_features() -> None:
    if not FEATURES_PATH.exists():
        features = build_feature_table()
    else:
        features = pd.read_csv(FEATURES_PATH)
    band_cols = ["delta", "theta", "alpha", "beta", "gamma"]
    summary = features.groupby("preference_label")[band_cols].mean().T
    ax = summary.plot(kind="bar", figsize=(8, 4.8), color=["#b56576", "#2a9d8f"])
    ax.set_xlabel("EEG Band")
    ax.set_ylabel("Mean Power")
    ax.set_title("EEG Band Power by Preference Label")
    ax.legend(["dislike", "like"])
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "eeg_band_features.png", dpi=160)
    plt.close()


def generate_figures() -> None:
    ensure_dirs()
    plot_training_curves()
    plot_evaluation_figures()
    plot_recommendations()
    plot_band_features()
    print(f"[visualize] saved figures to: {FIGURE_DIR}")


if __name__ == "__main__":
    generate_figures()

