from __future__ import annotations

from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = PROJECT_DIR / "outputs"
FIGURE_DIR = OUTPUT_DIR / "figures"
CHECKPOINT_DIR = OUTPUT_DIR / "checkpoints"
RESULT_DIR = OUTPUT_DIR / "results"
REPORT_DIR = PROJECT_DIR / "report"

INTERACTIONS_PATH = PROCESSED_DIR / "mock_interactions.csv"
ITEMS_PATH = PROCESSED_DIR / "mock_items.csv"
SIGNALS_PATH = PROCESSED_DIR / "mock_eeg_signals.npz"
FEATURES_PATH = PROCESSED_DIR / "band_features.csv"
SPLIT_PATH = PROCESSED_DIR / "train_val_test_split.csv"
MODEL_PATH = CHECKPOINT_DIR / "eeg_preference_net.pt"
TRAIN_HISTORY_PATH = RESULT_DIR / "train_history.csv"
EVAL_METRICS_PATH = RESULT_DIR / "evaluation_metrics.csv"
PREDICTIONS_PATH = RESULT_DIR / "test_predictions.csv"
RECOMMENDATION_PATH = RESULT_DIR / "recommendations.csv"

RANDOM_SEED = 42
N_USERS = 20
N_ITEMS = 100
N_CHANNELS = 8
TIME_STEPS = 128
SAMPLING_RATE = 128
EPOCHS = 8
BATCH_SIZE = 64
LEARNING_RATE = 1e-3
EMBEDDING_DIM = 32
TOP_K = 10


def ensure_dirs() -> None:
    for path in [
        RAW_DIR,
        PROCESSED_DIR,
        FIGURE_DIR,
        CHECKPOINT_DIR,
        RESULT_DIR,
        REPORT_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)

