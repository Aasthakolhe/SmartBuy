"""
Deal score: ranks offers for the same product across stores.

    deal_score (0-100) = 100 * ( w_price  * price_competitiveness
                               + w_rating * bayesian_rating / 5 )

  * price_competitiveness = cheapest price / this offer's price   (1.0 = cheapest)
  * bayesian_rating shrinks ratings with few reviews toward a prior (4.0), so a
    5.0 rating from 3 reviews does not beat a 4.5 rating from 20,000 reviews.
"""
from __future__ import annotations

import pandas as pd

import config


def bayesian_rating(rating, reviews) -> float:
    r = config.RATING_PRIOR if rating is None or pd.isna(rating) else float(rating)
    v = 0 if reviews is None or pd.isna(reviews) else float(reviews)
    m = config.RATING_PRIOR_COUNT
    return (v * r + m * config.RATING_PRIOR) / (v + m)


def score_offers(offers: list[dict], price_weight: float = config.DEFAULT_PRICE_WEIGHT) -> pd.DataFrame:
    if not offers:
        return pd.DataFrame()
    df = pd.DataFrame(offers).copy()
    min_price, max_price = df["price"].min(), df["price"].max()
    df["price_score"] = min_price / df["price"]
    df["adj_rating"] = [bayesian_rating(r, n) for r, n in zip(df["rating"], df["reviews"])]
    df["deal_score"] = 100 * (price_weight * df["price_score"] + (1 - price_weight) * df["adj_rating"] / 5)
    df["save_vs_highest"] = max_price - df["price"]
    df["extra_vs_cheapest"] = df["price"] - min_price
    if "mrp" in df:
        df["discount_pct"] = ((1 - df["price"] / df["mrp"]) * 100).where(df["mrp"].notna())
    df = df.sort_values(["deal_score", "price"], ascending=[False, True]).reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))
    return df
