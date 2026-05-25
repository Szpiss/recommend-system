from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import (  # noqa: E402
    INTERACTIONS_PATH,
    ITEMS_PATH,
    N_CHANNELS,
    N_ITEMS,
    N_USERS,
    RANDOM_SEED,
    SAMPLING_RATE,
    SIGNALS_PATH,
    TIME_STEPS,
    ensure_dirs,
)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def generate_mock_data() -> None:
    """生成可复现实验数据，模拟 DEAP 风格 EEG 情绪/偏好信号。"""
    ensure_dirs()
    rng = np.random.default_rng(RANDOM_SEED)
    t = np.arange(TIME_STEPS) / SAMPLING_RATE

    user_latent = rng.normal(0, 1, size=(N_USERS, 5))
    item_latent = rng.normal(0, 1, size=(N_ITEMS, 5))
    item_popularity = _sigmoid(rng.normal(0, 1, size=N_ITEMS))
    item_categories = rng.choice(
        ["movie", "music", "game", "short_video", "article"], size=N_ITEMS
    )

    rows: list[dict[str, float | int | str]] = []
    signals: list[np.ndarray] = []

    # 每个用户-物品组合都构造一个可预测样本，后续按用户内未见物品做 Top-N 推荐。
    for user_id in range(1, N_USERS + 1):
        for item_id in range(1, N_ITEMS + 1):
            preference_base = float(
                np.dot(user_latent[user_id - 1], item_latent[item_id - 1]) / 5.0
                + 0.7 * item_popularity[item_id - 1]
                + rng.normal(0, 0.35)
            )
            preference_prob = float(_sigmoid(np.array(preference_base)))
            preference_label = int(preference_prob >= 0.55)
            valence_score = float(np.clip(5.0 + 4.0 * (preference_prob - 0.5) + rng.normal(0, 0.6), 1, 9))
            arousal_score = float(np.clip(4.8 + rng.normal(0, 1.0) + 1.2 * abs(preference_prob - 0.5), 1, 9))
            rating = int(np.clip(np.rint(1 + 4 * preference_prob + rng.normal(0, 0.4)), 1, 5))

            # 偏好越高，alpha/beta/gamma 成分越明显；低偏好样本 theta/delta 稍强。
            band_strengths = {
                "delta": 0.55 + 0.30 * (1 - preference_prob),
                "theta": 0.45 + 0.25 * (1 - preference_prob),
                "alpha": 0.45 + 0.45 * preference_prob,
                "beta": 0.35 + 0.55 * preference_prob,
                "gamma": 0.25 + 0.45 * preference_prob,
            }
            freqs = {"delta": 2.0, "theta": 6.0, "alpha": 10.0, "beta": 20.0, "gamma": 38.0}
            channel_signal = []
            for channel in range(N_CHANNELS):
                phase = rng.uniform(0, 2 * np.pi)
                eeg = np.zeros_like(t, dtype=np.float32)
                for band, freq in freqs.items():
                    eeg += (
                        band_strengths[band]
                        * rng.uniform(0.75, 1.25)
                        * np.sin(2 * np.pi * freq * t + phase + channel * 0.13)
                    )
                eeg += rng.normal(0, 0.45, size=TIME_STEPS)
                channel_signal.append(eeg.astype(np.float32))
            signal = np.stack(channel_signal, axis=0)

            rows.append(
                {
                    "sample_id": len(rows),
                    "user_id": user_id,
                    "item_id": item_id,
                    "valence_score": round(valence_score, 4),
                    "arousal_score": round(arousal_score, 4),
                    "preference_label": preference_label,
                    "rating": rating,
                    "item_popularity_score": round(float(item_popularity[item_id - 1]), 4),
                    "item_category": item_categories[item_id - 1],
                }
            )
            signals.append(signal)

    interactions = pd.DataFrame(rows)
    items = pd.DataFrame(
        {
            "item_id": np.arange(1, N_ITEMS + 1),
            "item_name": [f"Content_{idx:03d}" for idx in range(1, N_ITEMS + 1)],
            "item_category": item_categories,
            "item_popularity_score": item_popularity.round(4),
        }
    )

    interactions.to_csv(INTERACTIONS_PATH, index=False)
    items.to_csv(ITEMS_PATH, index=False)
    np.savez_compressed(SIGNALS_PATH, eeg_signal=np.stack(signals, axis=0).astype(np.float32))
    print(f"[mock_data] saved interactions: {INTERACTIONS_PATH} ({len(interactions)} rows)")
    print(f"[mock_data] saved signals: {SIGNALS_PATH} shape={np.stack(signals).shape}")


if __name__ == "__main__":
    generate_mock_data()

