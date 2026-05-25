from __future__ import annotations

import torch
from torch import nn


class EEGPreferenceNet(nn.Module):
    """CNN + MLP 融合网络，输出偏好概率、评分和 EEG 兴趣 embedding。"""

    def __init__(self, n_channels: int = 8, embedding_dim: int = 32):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv1d(n_channels, 32, kernel_size=7, padding=3),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(32, 64, kernel_size=5, padding=2),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(64, 96, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
        )
        self.embedding_head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(96, embedding_dim),
            nn.ReLU(),
            nn.Dropout(0.15),
        )
        self.preference_head = nn.Linear(embedding_dim, 1)
        self.rating_head = nn.Sequential(nn.Linear(embedding_dim, 1), nn.Sigmoid())

    def forward(self, eeg: torch.Tensor) -> dict[str, torch.Tensor]:
        embedding = self.embedding_head(self.encoder(eeg))
        logits = self.preference_head(embedding).squeeze(-1)
        preference_prob = torch.sigmoid(logits)
        rating_score = self.rating_head(embedding).squeeze(-1)
        return {
            "logits": logits,
            "preference_prob": preference_prob,
            "predicted_rating": 1.0 + rating_score * 4.0,
            "rating_norm": rating_score,
            "embedding": embedding,
        }

