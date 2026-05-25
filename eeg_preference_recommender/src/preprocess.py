from __future__ import annotations

import numpy as np


def standardize_eeg(eeg: np.ndarray) -> np.ndarray:
    """按样本和通道标准化 EEG，减少不同通道幅值差异。"""
    mean = eeg.mean(axis=-1, keepdims=True)
    std = eeg.std(axis=-1, keepdims=True) + 1e-6
    return ((eeg - mean) / std).astype(np.float32)


def moving_average_filter(eeg: np.ndarray, window_size: int = 3) -> np.ndarray:
    """轻量平滑滤波，适合模拟数据和 CPU 快速运行。"""
    if window_size <= 1:
        return eeg.astype(np.float32)
    kernel = np.ones(window_size, dtype=np.float32) / window_size
    filtered = np.apply_along_axis(lambda x: np.convolve(x, kernel, mode="same"), -1, eeg)
    return filtered.astype(np.float32)


def preprocess_batch(eeg: np.ndarray) -> np.ndarray:
    return standardize_eeg(moving_average_filter(eeg))

