"""
Historical price data generator.

Real multi-year, store-level price histories for Indian e-commerce are not
publicly available, so SmartBuy SIMULATES them with rules that reproduce how
prices behave on Indian stores:

  * sticky prices that change on only ~12% of days, by small amounts
  * category-specific depreciation (phones fall faster than appliances)
  * one permanent price cut per product (e.g. when a successor launches)
  * products launched inside the window start at MRP and only have history
    from their launch date
  * deep discounts during sale events (Big Billion Days / Great Indian
    Festival, Diwali, Republic Day, Independence Day, ...), with depth varying
    by category, brand (Apple discounts less) and store
  * a small price hike in the days just before a big sale
  * random short "flash deals" per store
  * seasonality for air conditioners (dearer in summer)

Histories are generated on demand per product (deterministic: the same product
and end date always give the same series) and cached. The ML training set is a
stratified sample of products saved to data/price_history.csv.

Every live search is also logged to SQLite (storage.py), so real history
accumulates and can be used to retrain the models.
"""
from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache

import numpy as np
import pandas as pd

import config
from src.catalog import CATALOG, CATEGORIES, get_product, store_title

# depreciation per year (min, max), sale-depth multiplier, flash-deal probability per day
CATEGORY_BEHAVIOUR = {
    "Smartphone": {"depr": (0.08, 0.20), "sale": 1.00, "flash": 0.012},
    "Laptop":     {"depr": (0.06, 0.15), "sale": 0.90, "flash": 0.010},
    "Tablet":     {"depr": (0.05, 0.12), "sale": 0.95, "flash": 0.010},
    "TV":         {"depr": (0.08, 0.18), "sale": 1.20, "flash": 0.012},
    "Audio":      {"depr": (0.05, 0.15), "sale": 1.30, "flash": 0.018},
    "Wearable":   {"depr": (0.06, 0.15), "sale": 1.20, "flash": 0.015},
    "Camera":     {"depr": (0.03, 0.10), "sale": 0.70, "flash": 0.006},
    "Appliance":  {"depr": (-0.03, 0.05), "sale": 1.00, "flash": 0.010},
    "Monitor":    {"depr": (0.05, 0.12), "sale": 1.00, "flash": 0.012},
    "Gaming":     {"depr": (0.00, 0.08), "sale": 0.50, "flash": 0.006},
    "Accessory":  {"depr": (0.03, 0.12), "sale": 1.10, "flash": 0.015},
}
DEFAULT_BEHAVIOUR = {"depr": (0.05, 0.12), "sale": 1.0, "flash": 0.012}


def _round_prices(x: np.ndarray) -> np.ndarray:
    """Round to typical Indian retail endings (..99 / ..9)."""
    return np.where(x >= 5000, np.round(x / 100.0) * 100 - 1, np.round(x / 10.0) * 10 - 1)


@lru_cache(maxsize=8)
def _calendar(start_iso: str, end_iso: str):
    """Sale events overlapping the window, as day-index arrays."""
    start, end = date.fromisoformat(start_iso), date.fromisoformat(end_iso)
    evs = []
    for ev in config.sale_events(range(start.year, end.year + 2)):
        s, e = (ev["start"] - start).days, (ev["end"] - start).days
        if e < 0 or s > (end - start).days:
            continue
        evs.append((s, e, ev["depth"]))
    return evs


@lru_cache(maxsize=4096)
def _history(product_id: str, end_iso: str, n_days: int) -> pd.DataFrame:
    p = get_product(product_id)
    idx = int(product_id[1:])
    rng = np.random.default_rng(config.RANDOM_SEED * 100_003 + idx)
    beh = CATEGORY_BEHAVIOUR.get(p["category"], DEFAULT_BEHAVIOUR)

    end = date.fromisoformat(end_iso)
    window_start = end - timedelta(days=n_days - 1)
    start = window_start
    if p.get("launch"):
        launch = date.fromisoformat(p["launch"])
        if launch > window_start:
            start = min(launch, end - timedelta(days=30))
    n = (end - start).days + 1
    days = pd.date_range(start, end, freq="D")
    i = np.arange(n)

    # ---- reference price path (depreciation, permanent cut, seasonality) ----
    annual = rng.uniform(*beh["depr"])
    daily = (1 - annual) ** (1 / 365)
    ref = p["base_price"] / daily ** (n - 1 - i)
    if n > 90 and rng.random() < 0.7:
        cut_day = int(rng.integers(45, n - 30))
        ref = np.where(i < cut_day, ref / (1 - rng.uniform(0.04, 0.10)), ref)
    if p.get("sub") == "AC":
        ref = ref * (1 + 0.04 * np.cos(2 * np.pi * (days.dayofyear.values - 135) / 365))
    ref = np.minimum(ref, p["mrp"])

    # ---- sale events and pre-sale hikes (day indexes relative to `start`) ----
    sale_mult = beh["sale"] * rng.uniform(0.8, 1.2) * (0.6 if p["brand"] == "Apple" else 1.0)
    depth = np.zeros(n)
    pre_sale = np.zeros(n, dtype=bool)
    for s, e, (lo, hi) in _calendar(start.isoformat(), end_iso):
        d = rng.uniform(lo, hi) * sale_mult
        a, b = max(s, 0), min(e, n - 1)
        if a <= b:
            depth[a:b + 1] = np.maximum(depth[a:b + 1], d)
        if hi >= 0.12:
            pa, pb = max(s - 5, 0), min(s - 1, n - 1)
            if pa <= pb:
                pre_sale[pa:pb + 1] = True

    frames = []
    for store in config.STORES:
        prof = config.STORE_PROFILE[store]
        s_ref = ref * (1 + prof["offset"] + rng.normal(0, 0.006))
        change = rng.random(n) < 0.12
        noise = rng.normal(0, 0.012, n)
        sticky = np.empty(n)
        x = s_ref[0] * (1 + rng.normal(0, 0.01))
        for t in range(n):
            if change[t]:
                x = x + 0.5 * (s_ref[t] - x) + s_ref[t] * noise[t]
            x = min(max(x, s_ref[t] * 0.95), s_ref[t] * 1.05)
            sticky[t] = x

        price = sticky.copy()
        bump = pre_sale & (rng.random(n) < 0.6)
        price[bump] *= 1 + rng.uniform(0.01, 0.03, bump.sum())
        in_sale = depth > 0
        sale_cut = np.minimum(depth * prof["sale_depth"] + rng.normal(0, 0.01, n), 0.40)
        price[in_sale] *= 1 - sale_cut[in_sale]

        # flash deals outside sale events
        flash = np.zeros(n)
        starts = np.where((rng.random(n) < beh["flash"]) & ~in_sale)[0]
        for s0 in starts:
            flash[s0:s0 + int(rng.integers(1, 4))] = rng.uniform(0.04, 0.10)
        flash[in_sale] = 0
        price *= 1 - flash

        price = _round_prices(np.minimum(price, p["mrp"]))
        frames.append(pd.DataFrame({
            "date": days, "product_id": product_id, "brand": p["brand"],
            "title": store_title(p, store), "category": p["category"], "store": store,
            "price": price.astype(int), "mrp": p["mrp"],
            "rating": round(float(np.clip(rng.normal(4.3, 0.15), 3.8, 4.8)), 1),
            "reviews": int(rng.integers(150, 25000)),
        }))
    return pd.concat(frames, ignore_index=True)


def product_history(product_id: str, end_date: date | None = None,
                    n_days: int = config.HISTORY_DAYS) -> pd.DataFrame:
    """Daily price history of one catalog product at all four stores."""
    end = (end_date or date.today()).isoformat()
    return _history(product_id, end, n_days).copy()


def today_offers(product_id: str) -> pd.DataFrame:
    h = product_history(product_id)
    return h[h["date"] == h["date"].max()]


# ---------------------------------------------------------------------------
# Training dataset: a stratified sample of products
# ---------------------------------------------------------------------------
def training_products(seed: int = config.RANDOM_SEED) -> tuple[list[str], list[str]]:
    """Pick products for training and a separate set of never-seen products for testing."""
    rng = np.random.default_rng(seed)
    total = len(CATALOG)
    train, holdout = [], []
    for cat in CATEGORIES:
        ids = [p["id"] for p in CATALOG if p["category"] == cat]
        rng.shuffle(ids)
        k_train = max(4, round(config.TRAIN_PRODUCTS * len(ids) / total))
        k_hold = max(2, round(config.HOLDOUT_PRODUCTS * len(ids) / total))
        train += ids[:k_train]
        holdout += ids[k_train:k_train + k_hold]
    return sorted(train), sorted(holdout)


def build_dataset(force: bool = False) -> pd.DataFrame:
    """Load the training CSV, generating it first if needed."""
    if config.HISTORY_CSV.exists() and not force:
        return pd.read_csv(config.HISTORY_CSV, parse_dates=["date"])
    train, holdout = training_products()
    df = pd.concat([product_history(pid) for pid in train + holdout], ignore_index=True)
    df["split_group"] = np.where(df["product_id"].isin(holdout), "unseen_product", "train_product")
    out = df.copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out.to_csv(config.HISTORY_CSV, index=False)
    return df


if __name__ == "__main__":
    data = build_dataset(force=True)
    print(f"Saved {len(data):,} rows ({data['product_id'].nunique()} products) to {config.HISTORY_CSV}")
