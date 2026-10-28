"""
SmartBuy test suite.   Run with:   python -m pytest -q
(The models are trained automatically if missing, ~2 minutes.)
"""
import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import config  # noqa: E402
from src.catalog import CATALOG, CATEGORIES, display_name  # noqa: E402
from src.collectors import (demo_offers_from_products, fetch_catalog, parse_product_html,  # noqa: E402
                            parse_serpapi, search_catalog)
from src.data_generator import product_history  # noqa: E402
from src.matching import match_offers, product_key  # noqa: E402
from src.scoring import score_offers  # noqa: E402

SERPAPI_IPHONE17 = json.loads((HERE / "serpapi_iphone17_sample.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------- catalogue
def test_catalog_has_1000_plus_unique_products():
    assert len(CATALOG) >= 1000
    keys = {(p["brand"], p["model"], p["spec"]) for p in CATALOG}
    assert len(keys) == len(CATALOG)
    assert len(CATEGORIES) >= 10
    assert all(0 < p["base_price"] <= p["mrp"] for p in CATALOG)


def test_iphone_17_in_catalog_search():
    offers, total = fetch_catalog("iphone 17")
    res = match_offers("iphone 17", offers)
    names = [g["name"] for g in res["groups"]]
    assert total == 2 and all("iPhone 17 (" in n for n in names)        # 256 GB and 512 GB, no Pro/Pro Max
    assert all(g["stores"] == 4 for g in res["groups"])


def test_catalog_search_variants_and_brands():
    assert all("Pro Max" in display_name(p) for p in search_catalog("iphone 17 pro max")[0])
    tvs, _ = search_catalog("lg television 55")
    assert tvs and all(p["brand"] == "LG" for p in tvs)
    consoles, _ = search_catalog("playstation 5")
    assert any("Console" in p["model"] for p in consoles)


def test_launched_products_start_at_launch():
    p = next(p for p in CATALOG if p["model"] == "iPhone 17")
    h = product_history(p["id"])
    assert h["date"].min().date() == date.fromisoformat(p["launch"])
    assert (h["price"] <= p["mrp"]).all()


# --------------------------------------------------------------------- live data
def test_serpapi_parser_handles_nested_blocks():
    offers = parse_serpapi(SERPAPI_IPHONE17)
    assert len(offers) == 11
    assert {"Amazon", "Flipkart", "Croma", "Reliance Digital", "Vijay Sales"} <= {o["store"] for o in offers}


def test_live_iphone17_matching():
    res = match_offers("iphone 17", parse_serpapi(SERPAPI_IPHONE17))
    g256 = res["groups"][0]
    assert "256" in g256["key"] and g256["stores"] == 5      # brand-less + marketing titles grouped
    assert g256["offers"][0]["store"] == "Flipkart" and g256["offers"][0]["price"] == 79900
    reasons = {r["reason"] for r in res["rejected"]}
    assert {"different variant", "accessory / refurbished"} <= reasons
    assert any("512" in g["key"] for g in res["groups"])


def test_store_title_formats_give_same_key():
    from src.catalog import store_title
    for p in CATALOG[:300]:
        keys = {product_key(store_title(p, s)) for s in config.STORES}
        assert len(keys) == 1, (p["id"], keys)


def test_deal_score_prefers_cheap_and_well_rated():
    df = score_offers(parse_serpapi(SERPAPI_IPHONE17)[:4])
    assert df.iloc[0]["store"] == "Flipkart"
    assert df["deal_score"].between(0, 100).all()


def test_demo_api_offers():
    products = [{"title": "iPhone 9", "brand": "Apple", "price": 549, "rating": 4.69,
                 "discountPercentage": 12.96, "category": "smartphones", "thumbnail": ""}]
    offers = demo_offers_from_products(products, on=date(2026, 1, 1))
    res = match_offers("iphone 9", offers)
    assert res["groups"] and res["groups"][0]["stores"] == 4


def test_api_cache_roundtrip():
    from src import storage
    storage.cache_put("test|key", {"a": 1})
    assert storage.cache_get("test|key", 1) == {"a": 1}


# --------------------------------------------------------------------- scraper
def test_scraper_reads_json_ld():
    html = """<html><head><script type="application/ld+json">
    {"@context":"https://schema.org","@type":"Product","name":"Sony WH-1000XM5",
     "offers":{"@type":"Offer","price":"26990","priceCurrency":"INR"},
     "aggregateRating":{"ratingValue":"4.4","reviewCount":"1520"}}</script></head></html>"""
    out = parse_product_html(html)
    assert out["title"] == "Sony WH-1000XM5" and out["price"] == 26990 and out["reviews"] == 1520


def test_scraper_meta_fallback():
    html = '<html><head><meta property="og:title" content="LG TV"><meta property="product:price:amount" content="29,990"></head></html>'
    out = parse_product_html(html)
    assert out["price"] == 29990 and out["title"] == "LG TV"


# --------------------------------------------------------------------- ML
def test_advisor_end_to_end():
    from src.advisor import Advisor
    adv = Advisor()
    pid = next(p["id"] for p in CATALOG if p["model"] == "iPhone 17")
    a = adv.advise_catalog(pid)
    assert a.verdict in {"BUY NOW", "WAIT"} and 0 <= a.wait_probability <= 1
    assert a.predicted_min <= a.current_price
    live = adv.advise_live(match_offers("iphone 17", parse_serpapi(SERPAPI_IPHONE17))["groups"][0]["offers"],
                           "test-key", "Apple iPhone 17 256GB")
    assert live.verdict in {"BUY NOW", "WAIT"}
    m = adv.metrics
    assert m["classifier"]["accuracy"] > m["classifier"]["baseline_accuracy"]
    assert m["regressor"]["mae_inr"] < m["regressor"]["baseline_mae_inr"]
