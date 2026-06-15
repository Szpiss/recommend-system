from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


PROJECT_DIR = Path(__file__).resolve().parent
CF_RESULT_DIR = PROJECT_DIR / "results"
USER_SIMILARITY_PATH = CF_RESULT_DIR / "user_similarity.csv"
ITEM_SIMILARITY_PATH = CF_RESULT_DIR / "item_similarity.csv"
CF_RECOMMENDATIONS_PATH = CF_RESULT_DIR / "cf_recommendations.csv"


def compute_user_similarity(train_matrix: pd.DataFrame) -> pd.DataFrame:
    values = train_matrix.fillna(0.0).to_numpy(dtype=float)
    sim = cosine_similarity(values)
    result = pd.DataFrame(sim, index=train_matrix.index, columns=train_matrix.index)
    result.to_csv(USER_SIMILARITY_PATH)
    print(f"[cf] saved user similarity matrix: {USER_SIMILARITY_PATH} shape={result.shape}")
    return result


def compute_item_similarity(train_matrix: pd.DataFrame) -> pd.DataFrame:
    values = train_matrix.fillna(0.0).to_numpy(dtype=float).T
    sim = cosine_similarity(values)
    result = pd.DataFrame(sim, index=train_matrix.columns, columns=train_matrix.columns)
    result.to_csv(ITEM_SIMILARITY_PATH)
    print(f"[cf] saved item similarity matrix: {ITEM_SIMILARITY_PATH} shape={result.shape}")
    return result


def _candidate_items(train_matrix: pd.DataFrame, user_id: int) -> list[str]:
    user_row = train_matrix.loc[user_id]
    return user_row[user_row.isna()].index.tolist()


def user_cf_scores(
    train_matrix: pd.DataFrame,
    user_similarity: pd.DataFrame,
    user_id: int,
    top_neighbors: int = 10,
) -> pd.Series:
    matrix = train_matrix.fillna(0.0)
    sims = user_similarity.loc[user_id].drop(index=user_id).clip(lower=0)
    neighbors = sims.sort_values(ascending=False).head(top_neighbors)
    if neighbors.sum() <= 0:
        return pd.Series(0.0, index=train_matrix.columns)
    scores = matrix.loc[neighbors.index].T.dot(neighbors) / (neighbors.sum() + 1e-8)
    return scores


def item_cf_scores(train_matrix: pd.DataFrame, item_similarity: pd.DataFrame, user_id: int) -> pd.Series:
    user_row = train_matrix.loc[user_id]
    known = user_row.dropna()
    liked = known[known > 0]
    if liked.empty:
        return pd.Series(0.0, index=train_matrix.columns)
    sims = item_similarity.loc[:, liked.index].clip(lower=0)
    scores = sims.dot(liked) / (sims.sum(axis=1) + 1e-8)
    return scores


def recommend_user_cf(
    train_matrix: pd.DataFrame,
    user_similarity: pd.DataFrame,
    top_k: int = 10,
    top_neighbors: int = 10,
) -> pd.DataFrame:
    rows: list[dict[str, int | float | str]] = []
    for user_id in train_matrix.index:
        scores = user_cf_scores(train_matrix, user_similarity, int(user_id), top_neighbors)
        candidates = _candidate_items(train_matrix, int(user_id))
        ranked = scores.loc[candidates].sort_values(ascending=False).head(top_k)
        for rank, (item_id, score) in enumerate(ranked.items(), start=1):
            rows.append(
                {
                    "algorithm": "UserCF",
                    "user_id": int(user_id),
                    "rank": rank,
                    "item_id": int(item_id),
                    "score": float(score),
                }
            )
    return pd.DataFrame(rows)


def recommend_item_cf(
    train_matrix: pd.DataFrame,
    item_similarity: pd.DataFrame,
    top_k: int = 10,
) -> pd.DataFrame:
    rows: list[dict[str, int | float | str]] = []
    for user_id in train_matrix.index:
        scores = item_cf_scores(train_matrix, item_similarity, int(user_id))
        candidates = _candidate_items(train_matrix, int(user_id))
        ranked = scores.loc[candidates].sort_values(ascending=False).head(top_k)
        for rank, (item_id, score) in enumerate(ranked.items(), start=1):
            rows.append(
                {
                    "algorithm": "ItemCF",
                    "user_id": int(user_id),
                    "rank": rank,
                    "item_id": int(item_id),
                    "score": float(score),
                }
            )
    return pd.DataFrame(rows)


def precision_recall_at_k(
    recommendations: pd.DataFrame,
    test_interactions: pd.DataFrame,
    k: int = 10,
) -> pd.DataFrame:
    relevant = (
        test_interactions[test_interactions["preference_label"] == 1]
        .groupby("user_id")["item_id"]
        .apply(lambda x: set(x.astype(int)))
        .to_dict()
    )
    metric_rows: list[dict[str, float | str]] = []
    for algorithm, algo_recs in recommendations.groupby("algorithm"):
        precisions, recalls, hit_rates = [], [], []
        for user_id, user_recs in algo_recs.groupby("user_id"):
            rel_items = relevant.get(int(user_id), set())
            if not rel_items:
                continue
            top_items = user_recs.sort_values("rank").head(k)["item_id"].astype(int).tolist()
            hits = len(set(top_items) & rel_items)
            precisions.append(hits / k)
            recalls.append(hits / len(rel_items))
            hit_rates.append(1.0 if hits > 0 else 0.0)
        metric_rows.append(
            {
                "algorithm": algorithm,
                f"Precision@{k}": float(np.mean(precisions)) if precisions else 0.0,
                f"Recall@{k}": float(np.mean(recalls)) if recalls else 0.0,
                f"HitRate@{k}": float(np.mean(hit_rates)) if hit_rates else 0.0,
            }
        )
    return pd.DataFrame(metric_rows)


def run_collaborative_filtering(
    train_matrix: pd.DataFrame,
    test_interactions: pd.DataFrame,
    top_k: int = 10,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    CF_RESULT_DIR.mkdir(parents=True, exist_ok=True)
    user_similarity = compute_user_similarity(train_matrix)
    item_similarity = compute_item_similarity(train_matrix)

    user_recs = recommend_user_cf(train_matrix, user_similarity, top_k=top_k)
    item_recs = recommend_item_cf(train_matrix, item_similarity, top_k=top_k)
    recommendations = pd.concat([user_recs, item_recs], ignore_index=True)
    recommendations.to_csv(CF_RECOMMENDATIONS_PATH, index=False)
    print(f"[cf] saved recommendations: {CF_RECOMMENDATIONS_PATH} rows={len(recommendations)}")

    metrics = precision_recall_at_k(recommendations, test_interactions, k=top_k)
    return recommendations, user_similarity, item_similarity, metrics

