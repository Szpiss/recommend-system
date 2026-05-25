from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import FEATURES_PATH, INTERACTIONS_PATH, SAMPLING_RATE, SIGNALS_PATH, ensure_dirs  # noqa: E402
from src.preprocess import preprocess_batch  # noqa: E402


BANDS = {
    "delta": (0.5, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta": (13, 30),
    "gamma": (30, 45),
}


def extract_band_power(signal: np.ndarray, sampling_rate: int = SAMPLING_RATE) -> dict[str, float]:
    """用 FFT 近似 PSD，提取五类常见 EEG 频段平均功率。"""
    signal = preprocess_batch(signal)
    freqs = np.fft.rfftfreq(signal.shape[-1], d=1.0 / sampling_rate)
    psd = np.abs(np.fft.rfft(signal, axis=-1)) ** 2
    features: dict[str, float] = {}
    for band, (low, high) in BANDS.items():
        mask = (freqs >= low) & (freqs < high)
        features[band] = float(psd[:, mask].mean()) if mask.any() else 0.0
    return features


def build_feature_table() -> pd.DataFrame:
    ensure_dirs()
    if not INTERACTIONS_PATH.exists() or not SIGNALS_PATH.exists():
        from src.mock_data import generate_mock_data

        generate_mock_data()
    interactions = pd.read_csv(INTERACTIONS_PATH)
    signals = np.load(SIGNALS_PATH)["eeg_signal"]
    rows = []
    for sample_id, signal in enumerate(signals):
        row = {"sample_id": sample_id}
        row.update(extract_band_power(signal))
        rows.append(row)
    features = pd.DataFrame(rows)
    result = interactions.merge(features, on="sample_id", how="left")
    result.to_csv(FEATURES_PATH, index=False)
    print(f"[feature_extractor] saved band features: {FEATURES_PATH}")
    return result


if __name__ == "__main__":
    build_feature_table()

