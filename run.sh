#!/usr/bin/env bash
# SmartBuy - one-click setup and run for macOS / Linux
set -e
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1

if [ ! -d venv ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi
source venv/bin/activate

echo "Installing / checking dependencies..."
python -m pip install --upgrade pip >/dev/null
pip install -r requirements.txt

if [ ! -f models/metrics.json ]; then
  echo "Training the ML models for the first time (2-4 minutes)..."
  python train.py
fi

echo "Starting SmartBuy at http://localhost:8501"
streamlit run app.py
