from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import (  # noqa: E402
    INTERACTIONS_PATH,
    RANDOM_SEED,
    SIGNALS_PATH,
    SPLIT_PATH,
    ensure_dirs,
)
from src.preprocess import preprocess_batch  # noqa: E402


class EEGPreferenceDataset(Dataset):
    def __init__(self, interactions: pd.DataFrame, signals: np.ndarray):
        self.interactions = interactions.reset_index(drop=True)
        sample_ids = self.interactions["sample_id"].to_numpy(dtype=int)
        self.signals = preprocess_batch(signals[sample_ids])
        self.labels = self.interactions["preference_label"].to_numpy(dtype=np.float32)
        self.ratings = self.interactions["rating"].to_numpy(dtype=np.float32)

    def __len__(self) -> int:
        return len(self.interactions)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        return {
            "eeg": torch.tensor(self.signals[idx], dtype=torch.float32),
            "label": torch.tensor(self.labels[idx], dtype=torch.float32),
            "rating": torch.tensor((self.ratings[idx] - 1.0) / 4.0, dtype=torch.float32),
        }


def ensure_data_exists() -> None:
    ensure_dirs()
    if not INTERACTIONS_PATH.exists() or not SIGNALS_PATH.exists():
        from src.mock_data import generate_mock_data

        generate_mock_data()


def load_interactions_and_signals() -> tuple[pd.DataFrame, np.ndarray]:
    ensure_data_exists()
    return pd.read_csv(INTERACTIONS_PATH), np.load(SIGNALS_PATH)["eeg_signal"]


def get_or_create_split() -> pd.DataFrame:
    interactions, _ = load_interactions_and_signals()
    if SPLIT_PATH.exists():
        return pd.read_csv(SPLIT_PATH)

    train_val, test = train_test_split(
        interactions,
        test_size=0.2,
        random_state=RANDOM_SEED,
        stratify=interactions["preference_label"],
    )
    train, val = train_test_split(
        train_val,
        test_size=0.2,
        random_state=RANDOM_SEED,
        stratify=train_val["preference_label"],
    )
    split = interactions[["sample_id"]].copy()
    split["split"] = "unused"
    split.loc[split["sample_id"].isin(train["sample_id"]), "split"] = "train"
    split.loc[split["sample_id"].isin(val["sample_id"]), "split"] = "val"
    split.loc[split["sample_id"].isin(test["sample_id"]), "split"] = "test"
    split.to_csv(SPLIT_PATH, index=False)
    print(f"[data_loader] saved split: {SPLIT_PATH}")
    return split


def load_split(split_name: str) -> tuple[pd.DataFrame, np.ndarray]:
    interactions, signals = load_interactions_and_signals()
    split = get_or_create_split()
    selected_ids = split.loc[split["split"] == split_name, "sample_id"]
    selected = interactions[interactions["sample_id"].isin(selected_ids)].reset_index(drop=True)
    return selected, signals

