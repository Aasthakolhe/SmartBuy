"""
Product catalogue (1,000+ SKUs) built from src/catalog_data.py.

Used for (1) the offline "Product catalog" data source and (2) generating the
historical price data the ML models learn from. Prices are approximate Indian
market prices and are NOT live; use the SerpAPI source for live prices.
"""
from __future__ import annotations

from functools import lru_cache

from src.catalog_data import PRODUCTS

CATALOG: list[dict] = []
_seen = set()
for _p in PRODUCTS:
    _k = (_p["brand"].lower(), _p["model"].lower(), _p["spec"].lower())
    if _k in _seen:
        continue
    _seen.add(_k)
    CATALOG.append({**_p, "id": f"P{len(CATALOG) + 1:04d}"})

CATEGORIES = sorted({p["category"] for p in CATALOG})
BRANDS = sorted({p["brand"] for p in CATALOG})
_BY_ID = {p["id"]: p for p in CATALOG}


def display_name(p: dict) -> str:
    """Neutral display name, e.g. 'Apple iPhone 17 (256 GB)'."""
    return f"{p['brand']} {p['model']} ({p['spec']})"


def store_title(p: dict, store: str) -> str:
    """
    Each store writes product titles differently. Reproducing those formats lets
    the matching engine be tested on realistic messy titles.
    """
    b, m, s, c = p["brand"], p["model"], p["spec"], p["color"]
    if store == "Amazon":
        return f"{b} {m} ({s}) - {c}"
    if store == "Flipkart":
        return f"{b.upper()} {m} ({c}, {s})"
    if store == "Croma":
        return f"{b} {m} {s.replace(',', '')} {c}"
    if store == "Reliance Digital":
        return f"{b} {m} {s}, {c}"
    return f"{b} {m} {s} {c}"


def get_product(product_id: str) -> dict | None:
    return _BY_ID.get(product_id)


@lru_cache(maxsize=1)
def catalog_frame():
    import pandas as pd
    df = pd.DataFrame(CATALOG)
    df["name"] = df.apply(display_name, axis=1)
    return df[["id", "name", "brand", "model", "spec", "category", "mrp", "base_price", "launch"]]
