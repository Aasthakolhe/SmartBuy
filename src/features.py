"""
Feature engineering.

The SAME functions build features for training (from the historical dataset)
and for live predictions (from a product's logged price history), so the model
sees identical inputs in both cases.

Targets (horizon = 7 days):
  * y_ratio : lowest price over the next 7 days / today's price   (regression)
  * y_drop  : 1 if that lowest price is >= 3% below today's price (classification)
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

import config
from src.catalog import CATEGORIES

STORE_CODES = {s: i for i, s in enumerate(config.STORES)}
CATEGORY_CODES = {c: i for i, c in enumerate(CATEGORIES + ["Other"])}

HISTORY_FEATURES = ["f_ratio_ma7", "f_ratio_ma30", "f_ratio_min30", "f_ratio_max30",
                    "f_chg_1d", "f_chg_7d", "f_vol14"]
FEATURES = HISTORY_FEATURES + [
    "f_price_vs_mrp", "f_cross_store_ratio",
    "f_days_to_sale", "f_days_since_sale", "f_in_sale", "f_next_sale_depth",
    "f_month", "f_dow", "f_is_weekend", "f_store", "f_category", "f_log_price",
]
NEUTRAL_HISTORY = {"f_ratio_ma7": 1.0, "f_ratio_ma30": 1.0, "f_ratio_min30": 1.0,
                   "f_ratio_max30": 1.0, "f_chg_1d": 0.0, "f_chg_7d": 0.0, "f_vol14": 0.01}

FEATURE_LABELS = {
    "f_ratio_ma7": "Price vs 7-day average", "f_ratio_ma30": "Price vs 30-day average",
    "f_ratio_min30": "Price vs 30-day low", "f_ratio_max30": "Price vs 30-day high",
    "f_chg_1d": "1-day price change", "f_chg_7d": "7-day price change",
    "f_vol14": "14-day volatility", "f_price_vs_mrp": "Price vs MRP",
    "f_cross_store_ratio": "Price vs cheapest store", "f_days_to_sale": "Days to next sale",
    "f_days_since_sale": "Days since last sale", "f_in_sale": "Sale running now",
    "f_next_sale_depth": "Expected depth of next sale", "f_month": "Month",
    "f_dow": "Day of week", "f_is_weekend": "Weekend", "f_store": "Store",
    "f_category": "Category", "f_log_price": "Price level (log)",
}


# ---------------------------------------------------------------------------
# Sale-calendar features
# ---------------------------------------------------------------------------
def calendar_features(dates: pd.Series) -> pd.DataFrame:
    """Days to next / since last sale, whether a sale is on, and its typical depth."""
    dates = pd.to_datetime(dates)
    years = range(dates.min().year - 1, dates.max().year + 2)
    events = config.sale_events(years)
    starts = np.array([np.datetime64(e["start"]) for e in events])
    ends = np.array([np.datetime64(e["end"]) for e in events])
    depths = np.array([np.mean(e["depth"]) for e in events])

    d = dates.values.astype("datetime64[D]")
    in_sale = ((d[:, None] >= starts[None, :]) & (d[:, None] <= ends[None, :])).any(axis=1)

    nxt = np.searchsorted(starts, d, side="right")          # first event starting after d
    nxt = np.clip(nxt, 0, len(starts) - 1)
    days_to = (starts[nxt] - d).astype(int)
    next_depth = depths[nxt]

    prev = np.searchsorted(ends, d, side="left") - 1         # last event ending before d
    prev = np.clip(prev, 0, len(ends) - 1)
    days_since = (d - ends[prev]).astype(int)

    return pd.DataFrame({
        "f_days_to_sale": np.clip(days_to, 0, 90),
        "f_days_since_sale": np.clip(np.where(in_sale, 0, days_since), 0, 90),
        "f_in_sale": in_sale.astype(int),
        "f_next_sale_depth": next_depth,
    }, index=dates.index)


def next_sale_info(on: date | None = None) -> dict | None:
    on = on or date.today()
    for ev in config.sale_events(range(on.year, on.year + 2)):
        if ev["end"] >= on:
            return {**ev, "days_to": max((ev["start"] - on).days, 0), "running": ev["start"] <= on}
    return None


# ---------------------------------------------------------------------------
# History features for one price series
# ---------------------------------------------------------------------------
def _history_features(price: pd.Series) -> pd.DataFrame:
    ma7 = price.rolling(7, min_periods=1).mean()
    ma30 = price.rolling(30, min_periods=1).mean()
    mn30 = price.rolling(30, min_periods=1).min()
    mx30 = price.rolling(30, min_periods=1).max()
    std14 = price.rolling(14, min_periods=2).std().fillna(0)
    return pd.DataFrame({
        "f_ratio_ma7": price / ma7,
        "f_ratio_ma30": price / ma30,
        "f_ratio_min30": price / mn30,
        "f_ratio_max30": price / mx30,
        "f_chg_1d": price.pct_change(1).fillna(0),
        "f_chg_7d": price.pct_change(7).fillna(0),
        "f_vol14": (std14 / price.rolling(14, min_periods=1).mean()).fillna(0.01),
    }, index=price.index)


def _static_features(df: pd.DataFrame) -> pd.DataFrame:
    dates = pd.to_datetime(df["date"])
    out = calendar_features(dates)
    out["f_price_vs_mrp"] = (df["price"] / df["mrp"]).clip(0, 1.5).fillna(0.85)
    out["f_month"] = dates.dt.month
    out["f_dow"] = dates.dt.day_of_week
    out["f_is_weekend"] = (dates.dt.day_of_week >= 5).astype(int)
    out["f_store"] = df["store"].map(STORE_CODES).fillna(0).astype(int)
    out["f_category"] = df["category"].map(CATEGORY_CODES).fillna(CATEGORY_CODES["Other"]).astype(int)
    out["f_log_price"] = np.log(df["price"].astype(float))
    return out


# ---------------------------------------------------------------------------
# Training dataset
# ---------------------------------------------------------------------------
def build_training_frame(history: pd.DataFrame) -> pd.DataFrame:
    """Turn the raw daily price history into a feature + target table."""
    df = history.sort_values(["product_id", "store", "date"]).reset_index(drop=True)

    # Cross-store comparison: today's price vs the cheapest store today
    day_min = df.groupby(["product_id", "date"])["price"].transform("min")
    df["f_cross_store_ratio"] = df["price"] / day_min

    parts = []
    for _, g in df.groupby(["product_id", "store"], sort=False):
        price = g["price"].astype(float)
        hist = _history_features(price)
        # lowest price over the next HORIZON days (excluding today)
        fut = price[::-1].rolling(config.HORIZON_DAYS, min_periods=config.HORIZON_DAYS).min()[::-1].shift(-1)
        hist["future_min"] = fut
        parts.append(hist)
    df = df.join(pd.concat(parts))
    df = df.join(_static_features(df))

    df = df.dropna(subset=["future_min"]).copy()
    df["y_ratio"] = df["future_min"] / df["price"]
    df["y_drop"] = (df["y_ratio"] <= 1 - config.DROP_THRESHOLD).astype(int)
    return df


def add_history_dropout(train: pd.DataFrame, fraction: float = 0.2, seed: int = config.RANDOM_SEED) -> pd.DataFrame:
    """
    Augmentation: copy a fraction of training rows with the history features
    set to neutral values. This teaches the model to still give sensible advice
    for products we have little or no price history for (e.g. a brand-new search).
    """
    extra = train.sample(frac=fraction, random_state=seed).copy()
    for col, val in NEUTRAL_HISTORY.items():
        extra[col] = val
    return pd.concat([train, extra], ignore_index=True)


# ---------------------------------------------------------------------------
# Live / single-product features
# ---------------------------------------------------------------------------
def build_live_features(price: float, store: str, category: str, mrp: float | None = None,
                        history: pd.Series | None = None, cheapest_price: float | None = None,
                        on: date | None = None) -> tuple[pd.DataFrame, int]:
    """
    Build one feature row for a product at a store right now.

    history: daily prices before today (index = dates). May be empty.
    Returns (feature row, number of history days used).
    """
    on = on or date.today()
    hist = pd.Series(dtype=float) if history is None else history.dropna().astype(float)
    hist = hist[pd.to_datetime(hist.index) < pd.Timestamp(on)] if len(hist) else hist
    n_hist = len(hist)

    series = pd.concat([hist, pd.Series([float(price)], index=[pd.Timestamp(on)])])
    if n_hist >= 3:
        hrow = _history_features(series).iloc[[-1]].reset_index(drop=True)
    else:
        hrow = pd.DataFrame([NEUTRAL_HISTORY])

    base = pd.DataFrame([{
        "date": pd.Timestamp(on), "price": float(price),
        "mrp": float(mrp) if mrp else np.nan,
        "store": store if store in STORE_CODES else config.STORES[0],
        "category": category,
    }])
    srow = _static_features(base).reset_index(drop=True)
    row = pd.concat([hrow, srow], axis=1)
    row["f_cross_store_ratio"] = float(price) / float(cheapest_price or price)
    return row[FEATURES], n_hist


def infer_category(title: str) -> str:
    t = title.lower()
    rules = [
        ("Laptop", ["laptop", "macbook", "notebook", "chromebook", "vivobook", "ideapad", "thinkpad"]),
        ("Tablet", ["ipad", "tablet", " tab "]),
        ("Wearable", ["watch", "band", "fitness tracker"]),
        ("Audio", ["headphone", "earbud", "airpods", "earphone", "speaker", "airdopes", "tws", "soundbar", "buds"]),
        ("TV", [" tv", "television", "smart led", "oled", "qled"]),
        ("Smartphone", ["phone", "iphone", "galaxy", "pixel", "redmi", "oneplus", "5g", "mobile", "smartphone"]),
    ]
    padded = f" {t} "
    for cat, words in rules:
        if any(w in padded for w in words):
            return cat
    return "Other"
