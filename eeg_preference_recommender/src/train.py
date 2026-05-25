from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import torch
from sklearn.metrics import accuracy_score
from torch import nn
from torch.utils.data import DataLoader

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import (  # noqa: E402
    BATCH_SIZE,
    EMBEDDING_DIM,
    EPOCHS,
    LEARNING_RATE,
    MODEL_PATH,
    N_CHANNELS,
    TRAIN_HISTORY_PATH,
    ensure_dirs,
)
from src.data_loader import EEGPreferenceDataset, get_or_create_split, load_interactions_and_signals  # noqa: E402
from src.model import EEGPreferenceNet  # noqa: E402


def _device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def train_model(epochs: int = EPOCHS) -> pd.DataFrame:
    ensure_dirs()
    interactions, signals = load_interactions_and_signals()
    split = get_or_create_split()
    train_df = interactions.merge(split[split["split"] == "train"], on="sample_id")
    val_df = interactions.merge(split[split["split"] == "val"], on="sample_id")
    train_loader = DataLoader(EEGPreferenceDataset(train_df, signals), batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(EEGPreferenceDataset(val_df, signals), batch_size=BATCH_SIZE)

    device = _device()
    model = EEGPreferenceNet(n_channels=N_CHANNELS, embedding_dim=EMBEDDING_DIM).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    bce_loss = nn.BCEWithLogitsLoss()
    mse_loss = nn.MSELoss()
    history = []

    print(f"[train] device={device}, train={len(train_df)}, val={len(val_df)}, epochs={epochs}")
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for batch in train_loader:
            eeg = batch["eeg"].to(device)
            label = batch["label"].to(device)
            rating = batch["rating"].to(device)
            output = model(eeg)
            loss = bce_loss(output["logits"], label) + 0.35 * mse_loss(output["rating_norm"], rating)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += float(loss.detach().cpu()) * len(label)

        model.eval()
        val_probs, val_labels = [], []
        val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                eeg = batch["eeg"].to(device)
                label = batch["label"].to(device)
                rating = batch["rating"].to(device)
                output = model(eeg)
                loss = bce_loss(output["logits"], label) + 0.35 * mse_loss(output["rating_norm"], rating)
                val_loss += float(loss.detach().cpu()) * len(label)
                val_probs.extend(output["preference_prob"].detach().cpu().numpy().tolist())
                val_labels.extend(label.detach().cpu().numpy().tolist())
        val_pred = [1 if p >= 0.5 else 0 for p in val_probs]
        row = {
            "epoch": epoch,
            "train_loss": total_loss / len(train_df),
            "val_loss": val_loss / len(val_df),
            "val_accuracy": accuracy_score(val_labels, val_pred),
        }
        history.append(row)
        print(
            f"[train] epoch {epoch:02d}/{epochs} "
            f"loss={row['train_loss']:.4f} val_loss={row['val_loss']:.4f} val_acc={row['val_accuracy']:.4f}"
        )

    torch.save({"model_state": model.state_dict()}, MODEL_PATH)
    history_df = pd.DataFrame(history)
    history_df.to_csv(TRAIN_HISTORY_PATH, index=False)
    print(f"[train] saved model: {MODEL_PATH}")
    print(f"[train] saved history: {TRAIN_HISTORY_PATH}")
    return history_df


if __name__ == "__main__":
    train_model()

