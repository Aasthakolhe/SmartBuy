"""
Train SmartBuy's ML models from the command line.

    python train.py              # train (generates the dataset if missing)
    python train.py --new-data   # regenerate the dataset, then train
"""
import os

# Limit math-library threads BEFORE numpy loads (avoids "OpenBLAS error: Memory
# allocation failed" on Windows machines with many CPU cores).
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse

from src.models import train_models

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train SmartBuy models")
    parser.add_argument("--new-data", action="store_true", help="regenerate the historical dataset first")
    args = parser.parse_args()
    train_models(force_new_data=args.new_data, verbose=True)
