"""
Data storage: SQLite price log.

Every offer fetched from any source is logged with a timestamp. Over days and
weeks this builds a REAL price history per product and store, which is used by
the advisor and can be exported to CSV for retraining.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta

import pandas as pd

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS price_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ts           TEXT NOT NULL,
    query        TEXT,
    product_key  TEXT,
    title        TEXT NOT NULL,
    store        TEXT NOT NULL,
    price        REAL NOT NULL,
    mrp          REAL,
    rating       REAL,
    reviews      INTEGER,
    url          TEXT,
    source       TEXT
);
CREATE INDEX IF NOT EXISTS idx_price_log_key ON price_log(product_key, store, ts);
CREATE TABLE IF NOT EXISTS api_cache (
    cache_key  TEXT PRIMARY KEY,
    ts         TEXT NOT NULL,
    payload    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tracked_urls (
    url        TEXT PRIMARY KEY,
    label      TEXT,
    added_at   TEXT
);
"""


# --- text repair (mojibake like "à¤ à¤ªà¥à¤ªà¤²" -> "ऐप्पल") ------------------
def _to_bytes(text: str) -> bytes:
    """Turn a mis-decoded string back into the original bytes (cp1252 first, then latin-1)."""
    out = bytearray()
    for ch in text:
        try:
            out += ch.encode("cp1252")
        except UnicodeEncodeError:
            if ord(ch) < 256:
                out.append(ord(ch))
            else:
                raise
    return bytes(out)


def fix_mojibake(text):
    """Repair UTF-8 text that was wrongly decoded as cp1252/latin-1. Safe on normal text."""
    if not isinstance(text, str) or text.isascii():
        return text
    if not any("\u00c2" <= ch <= "\u00f4" for ch in text):   # markers: Ã Â à â ...
        return text
    try:
        fixed = _to_bytes(text).decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
    return fixed if len(fixed) < len(text) else text


def fix_payload(obj):
    """Apply fix_mojibake to every string inside nested dict/list data."""
    if isinstance(obj, str):
        return fix_mojibake(obj)
    if isinstance(obj, list):
        return [fix_payload(x) for x in obj]
    if isinstance(obj, dict):
        return {k: fix_payload(v) for k, v in obj.items()}
    return obj


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.executescript(SCHEMA)
    return conn


def log_offers(offers: list[dict], query: str = "") -> int:
    """Insert offers into the price log. Returns number of rows written."""
    if not offers:
        return 0
    ts = datetime.now().isoformat(timespec="seconds")
    rows = [(ts, query, o.get("product_key"), fix_mojibake(o["title"]), o["store"], float(o["price"]),
             o.get("mrp"), o.get("rating"), o.get("reviews"), o.get("url"), o.get("source"))
            for o in offers if o.get("price")]
    with closing(_connect()) as conn, conn:
        conn.executemany(
            "INSERT INTO price_log (ts, query, product_key, title, store, price, mrp, rating, "
            "reviews, url, source) VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
    return len(rows)


def repair_mojibake_rows() -> int:
    """One-off cleanup: fix garbled titles already saved in the price log."""
    with closing(_connect()) as conn, conn:
        rows = conn.execute("SELECT id, title FROM price_log").fetchall()
        fixes = []
        for row_id, title in rows:
            new = fix_mojibake(title)
            if new != title:
                fixes.append((new, row_id))
        if fixes:
            conn.executemany("UPDATE price_log SET title = ? WHERE id = ?", fixes)
    return len(fixes)


def past_searches() -> list[str]:
    """Search texts and product titles seen before (used for search suggestions)."""
    out: list[str] = []
    try:
        with closing(_connect()) as conn:
            out += [r[0] for r in conn.execute(
                "SELECT DISTINCT query FROM price_log WHERE query IS NOT NULL AND query NOT IN ('', 'url')")]
            out += [r[0] for r in conn.execute("SELECT DISTINCT title FROM price_log LIMIT 1500")]
    except sqlite3.Error:
        pass
    return [fix_mojibake(t) for t in out if t]


def get_log(limit: int | None = None) -> pd.DataFrame:
    sql = "SELECT * FROM price_log ORDER BY ts DESC" + (f" LIMIT {int(limit)}" if limit else "")
    with closing(_connect()) as conn:
        return pd.read_sql_query(sql, conn)


def get_history(product_key: str, store: str | None = None) -> pd.DataFrame:
    """Daily lowest logged price per store for a product (date, store, price)."""
    sql = "SELECT ts, store, price FROM price_log WHERE product_key = ?"
    params: list = [product_key]
    if store:
        sql += " AND store = ?"
        params.append(store)
    with closing(_connect()) as conn:
        df = pd.read_sql_query(sql, conn, params=params)
    if df.empty:
        return pd.DataFrame(columns=["date", "store", "price"])
    df["date"] = pd.to_datetime(df["ts"]).dt.normalize()
    return df.groupby(["date", "store"], as_index=False)["price"].min()


def logged_products() -> pd.DataFrame:
    sql = """SELECT product_key, MAX(title) AS title, COUNT(*) AS records,
                    COUNT(DISTINCT substr(ts,1,10)) AS days, MIN(price) AS lowest, MAX(ts) AS last_seen
             FROM price_log WHERE product_key IS NOT NULL
             GROUP BY product_key ORDER BY last_seen DESC"""
    with closing(_connect()) as conn:
        return pd.read_sql_query(sql, conn)


def export_log_csv() -> bytes:
    return get_log().to_csv(index=False).encode("utf-8")


def clear_log() -> None:
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM price_log")


# --- tracked product URLs (for the scraper) -------------------------------
def add_tracked_url(url: str, label: str = "") -> None:
    with closing(_connect()) as conn, conn:
        conn.execute("INSERT OR REPLACE INTO tracked_urls (url, label, added_at) VALUES (?,?,?)",
                     (url, label, datetime.now().isoformat(timespec="seconds")))


def tracked_urls() -> pd.DataFrame:
    with closing(_connect()) as conn:
        return pd.read_sql_query("SELECT * FROM tracked_urls ORDER BY added_at DESC", conn)


def remove_tracked_url(url: str) -> None:
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM tracked_urls WHERE url = ?", (url,))


# --- API response cache (saves SerpAPI quota) ------------------------------
def cache_get(key: str, max_age_hours: float):
    with closing(_connect()) as conn:
        row = conn.execute("SELECT ts, payload FROM api_cache WHERE cache_key = ?", (key,)).fetchone()
    if not row:
        return None
    if datetime.fromisoformat(row[0]) < datetime.now() - timedelta(hours=max_age_hours):
        return None
    return fix_payload(json.loads(row[1]))


def cache_put(key: str, payload) -> None:
    with closing(_connect()) as conn, conn:
        conn.execute("INSERT OR REPLACE INTO api_cache (cache_key, ts, payload) VALUES (?,?,?)",
                     (key, datetime.now().isoformat(timespec="seconds"),
                      json.dumps(fix_payload(payload), ensure_ascii=False)))


def clear_cache() -> None:
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM api_cache")