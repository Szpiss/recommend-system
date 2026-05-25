from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import torch

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import BATCH_SIZE, ITEMS_PATH, RECOMMENDATION_PATH, TOP_K, ensure_dirs  # noqa: E402
from src.data_loader import EEGPreferenceDataset, get_or_create_split, load_interactions_and_signals  # noqa: E402
from src.evaluate import load_model  # noqa: E402


def recommend_for_user(user_id: int, top_k: int = TOP_K) -> pd.DataFrame:
    ensure_dirs()
    interactions, signals = load_interactions_and_signals()
    split = get_or_create_split()
    train_ids = set(split.loc[split["split"] == "train", "sample_id"])
    seen_items = set(
        interactions.loc[
            (interactions["user_id"] == user_id) & (interactions["sample_id"].isin(train_ids)),
            "item_id",
        ]
    )
    candidates = interactions[
        (interactions["user_id"] == user_id) & (~interactions["item_id"].isin(seen_items))
    ].reset_index(drop=True)
    if candidates.empty:
        raise ValueError(f"user_id={user_id} has no candidate items")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_model(device)
    loader = torch.utils.data.DataLoader(EEGPreferenceDataset(candidates, signals), batch_size=BATCH_SIZE)
    probs, ratings = [], []
    with torch.no_grad():
        for batch in loader:
            output = model(batch["eeg"].to(device))
            probs.extend(output["preference_prob"].detach().cpu().numpy().tolist())
            ratings.extend(output["predicted_rating"].detach().cpu().numpy().tolist())

    result = candidates.copy()
    result["eeg_preference_score"] = probs
    result["predicted_rating"] = ratings
    result["ranking_score"] = (
        0.7 * result["eeg_preference_score"] + 0.3 * result["item_popularity_score"]
    )
    if ITEMS_PATH.exists():
        items = pd.read_csv(ITEMS_PATH)
        result = result.merge(items[["item_id", "item_name"]], on="item_id", how="left")
    result = result.sort_values("ranking_score", ascending=False).head(top_k).reset_index(drop=True)
    result.insert(0, "rank", range(1, len(result) + 1))
    result.to_csv(RECOMMENDATION_PATH, index=False)
    print(f"[recommend] saved Top-{top_k} recommendations: {RECOMMENDATION_PATH}")
    print(result[["rank", "user_id", "item_id", "item_name", "ranking_score", "eeg_preference_score"]].to_string(index=False))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user_id", type=int, default=1)
    parser.add_argument("--top_k", type=int, default=TOP_K)
    args = parser.parse_args()
    recommend_for_user(args.user_id, args.top_k)


if __name__ == "__main__":
    main()

