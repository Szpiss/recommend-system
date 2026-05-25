from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from src.evaluate import evaluate_model
from src.feature_extractor import build_feature_table
from src.mock_data import generate_mock_data
from src.recommend import recommend_for_user
from src.train import train_model
from src.visualize import generate_figures
from src.report_generator import generate_report


def main() -> None:
    print("[main] Step 1/6 generate mock EEG data")
    generate_mock_data()
    print("[main] Step 2/6 extract EEG band features")
    build_feature_table()
    print("[main] Step 3/6 train EEG preference model")
    train_model()
    print("[main] Step 4/6 evaluate model and recommendation metrics")
    evaluate_model()
    print("[main] Step 5/6 generate Top-N recommendations")
    recommend_for_user(user_id=1, top_k=10)
    print("[main] Step 6/6 generate figures and report")
    generate_figures()
    generate_report()
    print("[main] done")


if __name__ == "__main__":
    main()

