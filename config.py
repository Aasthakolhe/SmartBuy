"""
SmartBuy - central configuration.

Everything you might want to tweak (paths, stores, sale calendar, model
settings, deal-score weights) lives here so the rest of the code stays clean.
"""
from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "smartbuy.db"                  # SQLite price log
HISTORY_CSV = DATA_DIR / "price_history.csv"        # historical training dataset
REGRESSOR_PATH = MODEL_DIR / "price_regressor.joblib"
CLASSIFIER_PATH = MODEL_DIR / "buy_wait_classifier.joblib"
METRICS_PATH = MODEL_DIR / "metrics.json"

# ---------------------------------------------------------------------------
# Stores
# ---------------------------------------------------------------------------
STORES = ["Amazon", "Flipkart", "Croma", "Reliance Digital"]

# Used to map free-text seller names (e.g. from Google Shopping) to our stores
STORE_ALIASES = {
    "amazon": "Amazon",
    "flipkart": "Flipkart",
    "croma": "Croma",
    "reliance": "Reliance Digital",
    "jiomart": "Reliance Digital",
}

# Synthetic-data behaviour per store: typical price offset vs. base price and
# how deep the store discounts during sale events (1.0 = full event depth).
STORE_PROFILE = {
    "Amazon":           {"offset": 0.000, "sale_depth": 1.00},
    "Flipkart":         {"offset": -0.008, "sale_depth": 1.05},
    "Croma":            {"offset": 0.020, "sale_depth": 0.70},
    "Reliance Digital": {"offset": 0.014, "sale_depth": 0.75},
}

# ---------------------------------------------------------------------------
# Indian e-commerce sale calendar (APPROXIMATE - edit when dates are announced)
# ---------------------------------------------------------------------------
# Diwali dates drive the two biggest festive sales.
DIWALI = {
    2023: date(2023, 11, 12),
    2024: date(2024, 11, 1),
    2025: date(2025, 10, 20),
    2026: date(2026, 11, 8),
    2027: date(2027, 10, 29),
    2028: date(2028, 10, 17),
}

# (name, start month, start day, duration days, (min depth, max depth))
FIXED_SALES = [
    ("Republic Day Sale",     1, 13, 6, (0.06, 0.12)),
    ("Summer Sale",           5, 1, 5, (0.05, 0.10)),
    ("Prime Day / Mid-Year",  7, 12, 3, (0.06, 0.12)),
    ("Independence Day Sale", 8, 5, 6, (0.06, 0.12)),
    ("Black Friday",          11, 27, 4, (0.04, 0.08)),
    ("Year-End Sale",         12, 20, 6, (0.04, 0.08)),
]


def sale_events(years) -> list[dict]:
    """Return every sale event (name, start, end, depth range) for the given years."""
    events = []
    for y in years:
        for name, m, d, dur, depth in FIXED_SALES:
            start = date(y, m, d)
            events.append({"name": name, "start": start,
                           "end": start + timedelta(days=dur - 1), "depth": depth})
        if y in DIWALI:
            dw = DIWALI[y]
            # Big Billion Days / Great Indian Festival: ~1 month before Diwali
            fs = dw - timedelta(days=32)
            events.append({"name": "Festive Mega Sale (BBD / GIF)", "start": fs,
                           "end": fs + timedelta(days=8), "depth": (0.10, 0.22)})
            # Diwali dhamaka sale: ~12 days before Diwali
            ds = dw - timedelta(days=12)
            events.append({"name": "Diwali Sale", "start": ds,
                           "end": ds + timedelta(days=9), "depth": (0.08, 0.15)})
    return sorted(events, key=lambda e: e["start"])


# ---------------------------------------------------------------------------
# Machine learning
# ---------------------------------------------------------------------------
HORIZON_DAYS = 7          # predict over the next 7 days
DROP_THRESHOLD = 0.03     # a "drop" = lowest price in next 7 days is >= 3% lower
HISTORY_DAYS = 730        # length of the synthetic history (2 years)
RANDOM_SEED = 42
TEST_FRACTION = 0.2       # last 20% of the timeline is the test set

# ---------------------------------------------------------------------------
# Deal score (0-100) = weight_price * price competitiveness + weight_rating * rating
# ---------------------------------------------------------------------------
DEFAULT_PRICE_WEIGHT = 0.7
RATING_PRIOR = 4.0        # Bayesian prior rating for stores with few reviews
RATING_PRIOR_COUNT = 50   # how many "virtual" reviews the prior is worth

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------
USD_TO_INR = 88.0         # approximate; only used by the demo public API source
REQUEST_TIMEOUT = 15
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


def get_serpapi_key() -> str:
    """Find the SerpAPI key: environment variable, .env file, or Streamlit secrets."""
    key = os.environ.get("SERPAPI_KEY", "").strip()
    if key:
        return key
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("SERPAPI_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    try:
        import streamlit as st
        return str(st.secrets.get("SERPAPI_KEY", "")).strip()
    except Exception:
        return ""

# Training sample: products used to train, plus never-seen products for testing
TRAIN_PRODUCTS = 140
HOLDOUT_PRODUCTS = 40
MAX_TRAIN_ROWS = 120_000   # cap so training stays fast on a laptop (~1-2 min)
