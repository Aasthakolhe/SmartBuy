"""
Data collection.

Three search sources plus a URL scraper. Every source returns a list of
"offer" dicts with the same shape:

    {"title", "store", "price", "mrp", "rating", "reviews", "url", "image", "source"}

Sources
-------
1. Live (SerpAPI)            - REAL prices from Google Shopping India: Amazon,
   Flipkart, Croma, Reliance Digital and other sellers. Needs a free SerpAPI
   key. Responses are cached for 6 hours to save the monthly quota.
2. Product catalog (offline) - 1,000+ products with simulated current prices
   from the historical model. Always works, no internet needed.
3. Demo public API           - real products fetched live from the free
   DummyJSON test API (no key). Its catalogue is small and dated, prices are in
   USD for one seller, so SmartBuy converts to INR and SIMULATES store prices.
4. URL scraper               - BeautifulSoup scraper that reads the price from a
   product page's structured data (JSON-LD / meta tags).
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

import config
from src.catalog import CATALOG, display_name, store_title


class SourceError(Exception):
    """Raised when a data source fails; the message is shown to the user."""


def _offer(title, store, price, mrp=None, rating=None, reviews=None, url=None, image=None,
           source="", **extra) -> dict:
    return {"title": title, "store": store, "price": float(price),
            "mrp": float(mrp) if mrp else None,
            "rating": float(rating) if rating is not None else None,
            "reviews": int(reviews) if reviews else None,
            "url": url, "image": image, "source": source, **extra}


def normalize_store(name: str) -> str:
    n = (name or "").lower()
    for alias, store in config.STORE_ALIASES.items():
        if alias in n:
            return store
    return name.strip() if name else "Unknown"


# ---------------------------------------------------------------------------
# 1. Product catalogue (offline, 1,000+ products)
# ---------------------------------------------------------------------------
MAX_CATALOG_RESULTS = 30


def search_catalog(query: str, limit: int = MAX_CATALOG_RESULTS) -> tuple[list[dict], int]:
    """Rank catalogue products against the query. Returns (products, total matches)."""
    from src.matching import relevance
    hits, near = [], []
    for p in CATALOG:
        score, reason = relevance(query, display_name(p))
        if reason is None:
            hits.append((score, p))
        elif score >= 60:
            near.append((score, p))
    hits.sort(key=lambda x: (-x[0], x[1]["base_price"]))
    near.sort(key=lambda x: -x[0])
    total = len(hits)
    chosen = [p for _, p in hits[:limit]] or [p for _, p in near[:5]]
    return chosen, total


def fetch_catalog(query: str) -> tuple[list[dict], int]:
    """Today's offers at all four stores for catalogue products matching the query."""
    from src.data_generator import today_offers
    products, total = search_catalog(query)
    offers = []
    for p in products:
        for r in today_offers(p["id"]).itertuples():
            offers.append(_offer(
                store_title(p, r.store), r.store, r.price, r.mrp, r.rating, r.reviews, url=None,
                source="Product catalog", product_id=p["id"], display_name=display_name(p),
                category=p["category"]))
    return offers, total


# ---------------------------------------------------------------------------
# 2. Demo public APIs (DummyJSON)
# ---------------------------------------------------------------------------
DUMMYJSON_URL = "https://dummyjson.com/products/search"


def fetch_demo_api(query: str, limit: int = 12) -> list[dict]:
    try:
        r = requests.get(DUMMYJSON_URL, params={"q": query, "limit": limit},
                         timeout=config.REQUEST_TIMEOUT)
        r.raise_for_status()
        products = r.json().get("products", [])
    except requests.RequestException as e:
        raise SourceError(f"Could not reach the DummyJSON demo API ({e.__class__.__name__}). "
                          "Check your internet connection, or use 'Sample catalog (offline)'.") from e
    return demo_offers_from_products(products)


def _demo_title(title: str, category: str, store: str) -> str:
    """Mimic how each store formats titles, so the matcher has real work to do."""
    cat = category.replace("-", " ").title()
    if store == "Amazon":
        return f"{title} - {cat}"
    if store == "Flipkart":
        first, _, rest = title.partition(" ")
        return f"{first.upper()} {rest}".strip()
    if store == "Croma":
        return f"{title} ({cat})"
    return title


def demo_offers_from_products(products: list[dict], on: date | None = None) -> list[dict]:
    """Convert DummyJSON products into simulated per-store offers (deterministic per day)."""
    on = on or date.today()
    offers = []
    for p in products:
        base_inr = float(p.get("price", 0)) * config.USD_TO_INR
        if base_inr <= 0:
            continue
        disc = float(p.get("discountPercentage") or 0)
        mrp = base_inr / max(1 - disc / 100, 0.3) if disc else base_inr * 1.15
        brand = p.get("brand") or ""
        title = p.get("title", "")
        if brand and not title.lower().startswith(brand.lower()):
            title = f"{brand} {title}"
        reviews_n = len(p.get("reviews", []) or []) * 37 + 20
        for store in config.STORES:
            seed = int(hashlib.md5(f"{title}|{store}|{on}".encode()).hexdigest()[:8], 16)
            rng = np.random.default_rng(seed)
            prof = config.STORE_PROFILE[store]
            price = base_inr * (1 + prof["offset"] + rng.normal(0, 0.025))
            price = int(round(price / 10) * 10 - 1) if price > 100 else round(price, 2)
            rating = float(np.clip((p.get("rating") or 4.0) + rng.normal(0, 0.15), 1, 5))
            offers.append(_offer(
                _demo_title(title, p.get("category", ""), store), store, price,
                round(mrp, -1), round(rating, 1), reviews_n, url=None,
                image=p.get("thumbnail"), source="Demo API (simulated store prices)"))
    return offers


# ---------------------------------------------------------------------------
# 3. SerpAPI - Google Shopping India (real live prices)
# ---------------------------------------------------------------------------
SERPAPI_URL = "https://serpapi.com/search.json"
SERPAPI_ACCOUNT_URL = "https://serpapi.com/account.json"
CACHE_HOURS = 6


def fetch_serpapi(query: str, api_key: str, use_cache: bool = True) -> tuple[list[dict], dict]:
    """
    Live Google Shopping India results. Responses are cached for 6 hours in SQLite
    so repeated searches don't use up the free monthly quota.
    Returns (offers, info) where info says whether the cache was used.
    """
    from src import storage
    if not api_key:
        raise SourceError("No SerpAPI key. Paste it in the sidebar or save it in .streamlit/secrets.toml "
                          "(free key at serpapi.com).")
    cache_key = f"serpapi|{query.strip().lower()}"
    if use_cache:
        cached = storage.cache_get(cache_key, CACHE_HOURS)
        if cached is not None:
            return parse_serpapi(cached), {"cached": True}
    params = {"engine": "google_shopping", "q": query, "gl": "in", "hl": "en",
              "location": "India", "google_domain": "google.co.in", "api_key": api_key}
    try:
        r = requests.get(SERPAPI_URL, params=params, timeout=40)
        data = r.json()
    except requests.Timeout as e:
        raise SourceError("SerpAPI took too long to respond. Try again.") from e
    except (requests.RequestException, ValueError) as e:
        raise SourceError(f"Could not reach SerpAPI ({e.__class__.__name__}). Check your internet connection.") from e
    if "error" in data:
        msg = data["error"]
        if "Invalid API key" in msg:
            msg += " Copy the key again from serpapi.com > Dashboard (no spaces or quotes)."
        elif "run out of searches" in msg.lower():
            msg += " Your monthly quota is used up; cached searches and the Product catalog still work."
        raise SourceError(f"SerpAPI error: {msg}")
    storage.cache_put(cache_key, data)
    return parse_serpapi(data), {"cached": False}


def check_serpapi_key(api_key: str) -> dict:
    """Account info: plan and searches left (does not use a search credit)."""
    try:
        r = requests.get(SERPAPI_ACCOUNT_URL, params={"api_key": api_key}, timeout=15)
        data = r.json()
    except (requests.RequestException, ValueError) as e:
        raise SourceError(f"Could not reach SerpAPI ({e.__class__.__name__}).") from e
    if "error" in data:
        raise SourceError(f"SerpAPI error: {data['error']}")
    return data


def _num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.search(r"[\d,]+(?:\.\d+)?", str(v))
    return float(m.group(0).replace(",", "")) if m else None


def _walk_items(node):
    """Yield every dict that looks like a product listing, anywhere in the response."""
    if isinstance(node, dict):
        if node.get("title") and (node.get("extracted_price") or node.get("price")) and \
                (node.get("source") or node.get("seller") or node.get("store")):
            yield node
        for k, v in node.items():
            if k not in ("search_metadata", "search_parameters", "filters", "pagination", "serpapi_pagination"):
                yield from _walk_items(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk_items(v)


def parse_serpapi(data: dict) -> list[dict]:
    """Robust to layout changes: collects listings from shopping_results, inline and categorised blocks."""
    offers, seen = [], set()
    for it in _walk_items(data):
        price = it.get("extracted_price") or _num(it.get("price"))
        seller = it.get("source") or it.get("seller") or it.get("store") or ""
        if not price or price < 50:
            continue
        key = (it["title"].strip().lower(), seller.lower(), float(price))
        if key in seen:
            continue
        seen.add(key)
        offers.append(_offer(
            it["title"], normalize_store(seller), price,
            mrp=it.get("extracted_old_price") or _num(it.get("old_price")),
            rating=it.get("rating"), reviews=it.get("reviews"),
            url=it.get("product_link") or it.get("link"), image=it.get("thumbnail"),
            source="SerpAPI Google Shopping", seller=seller))
    return offers


# ---------------------------------------------------------------------------
# 4. BeautifulSoup scraper for a single product URL
# ---------------------------------------------------------------------------
def scrape_product_url(url: str) -> dict:
    """
    Read title and price from a product page using structured data that most
    stores embed for search engines (JSON-LD Product schema, meta tags, itemprop).
    Some sites block automated requests; in that case use SerpAPI instead.
    """
    headers = {"User-Agent": config.USER_AGENT, "Accept-Language": "en-IN,en;q=0.9"}
    try:
        r = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
    except requests.RequestException as e:
        raise SourceError(f"Could not open the page ({e.__class__.__name__}).") from e
    if r.status_code != 200:
        raise SourceError(f"The site returned HTTP {r.status_code} (it may block automated requests).")
    result = parse_product_html(r.text)
    if not result.get("price"):
        raise SourceError("No price found in the page's structured data. "
                          "This site may load prices with JavaScript or block scrapers.")
    result.update(url=url, store=normalize_store(re.sub(r"^https?://(www\.)?", "", url).split("/")[0]),
                  source="URL scraper")
    return result


def parse_product_html(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    out: dict = {"title": None, "price": None, "mrp": None, "rating": None, "reviews": None}

    def walk(node):
        if isinstance(node, list):
            for n in node:
                yield from walk(n)
        elif isinstance(node, dict):
            yield node
            for k in ("@graph", "itemListElement"):
                if k in node:
                    yield from walk(node[k])

    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or tag.get_text() or "")
        except (ValueError, TypeError):
            continue
        for node in walk(data):
            types = node.get("@type")
            types = types if isinstance(types, list) else [types]
            if "Product" not in types:
                continue
            out["title"] = out["title"] or node.get("name")
            offers = node.get("offers") or {}
            offers = offers[0] if isinstance(offers, list) and offers else offers
            if isinstance(offers, dict):
                out["price"] = out["price"] or _num(offers.get("price") or offers.get("lowPrice"))
            agg = node.get("aggregateRating") or {}
            if isinstance(agg, dict):
                out["rating"] = out["rating"] or _num(agg.get("ratingValue"))
                out["reviews"] = out["reviews"] or _num(agg.get("reviewCount") or agg.get("ratingCount"))

    if not out["price"]:
        for attrs in ({"property": "product:price:amount"}, {"property": "og:price:amount"},
                      {"itemprop": "price"}):
            tag = soup.find(attrs=attrs)
            if tag:
                out["price"] = _num(tag.get("content") or tag.get_text())
                if out["price"]:
                    break
    if not out["title"]:
        t = soup.find("meta", property="og:title") or soup.find("title")
        if t:
            out["title"] = (t.get("content") or t.get_text() or "").strip()
    if out["reviews"]:
        out["reviews"] = int(out["reviews"])
    return out
