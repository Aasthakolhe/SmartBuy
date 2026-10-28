"""
Buy/Wait advisor: turns model predictions into a recommendation with reasons.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pandas as pd

import config
from src import storage
from src.catalog import get_product
from src.data_generator import product_history
from src.features import FEATURES, FEATURE_LABELS, build_live_features, infer_category, next_sale_info
from src.models import load_models, models_ready, train_models

WAIT_THRESHOLD = 0.5


@dataclass
class Advice:
    verdict: str                     # "BUY NOW" or "WAIT"
    wait_probability: float
    current_price: float
    store: str
    predicted_min: float             # predicted lowest price in the next 7 days
    expected_saving: float
    history_days: int
    reasons: list[str] = field(default_factory=list)
    per_store: pd.DataFrame | None = None

    @property
    def confidence(self) -> float:
        return max(self.wait_probability, 1 - self.wait_probability)


class Advisor:
    def __init__(self):
        if not models_ready():
            train_models(verbose=False)
        try:
            self.reg, self.clf, self.metrics = load_models()
        except Exception:
            # models saved by a different scikit-learn version -> retrain locally
            train_models(verbose=False)
            self.reg, self.clf, self.metrics = load_models()

    # ------------------------------------------------------------------
    def _predict_rows(self, rows: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        ratio = np.clip(self.reg.predict(rows[FEATURES]), 0.5, 1.0)
        proba = self.clf.predict_proba(rows[FEATURES])[:, 1]
        return ratio, proba

    def _advise(self, offers: list[dict], histories: dict[str, pd.Series], category: str,
                on: date) -> Advice:
        """offers: one per store (price, store, mrp). histories: store -> price series."""
        cheapest = min(o["price"] for o in offers)
        rows, n_hist = [], {}
        for o in offers:
            row, n = build_live_features(o["price"], o["store"], category, o.get("mrp"),
                                         histories.get(o["store"]), cheapest, on)
            rows.append(row)
            n_hist[o["store"]] = n
        X = pd.concat(rows, ignore_index=True)
        ratio, proba = self._predict_rows(X)

        per_store = pd.DataFrame({
            "store": [o["store"] for o in offers],
            "price": [o["price"] for o in offers],
            "predicted_min_7d": np.round(ratio * [o["price"] for o in offers]),
            "wait_probability": proba,
            "history_days": [n_hist[o["store"]] for o in offers],
        }).sort_values("price").reset_index(drop=True)

        best = per_store.iloc[0]
        # Decision is about the cheapest store: will the best price available drop?
        p_wait = float(best["wait_probability"])
        pred_min = float(min(per_store["predicted_min_7d"].min(), best["price"]))
        verdict = "WAIT" if p_wait >= WAIT_THRESHOLD else "BUY NOW"
        saving = max(best["price"] - pred_min, 0.0)

        reasons = self._reasons(X.iloc[int(np.argmin([o["price"] for o in offers]))], best, on,
                                verdict, saving, int(best["history_days"]))
        return Advice(verdict, p_wait, float(best["price"]), str(best["store"]), pred_min, saving,
                      int(best["history_days"]), reasons, per_store)

    def _reasons(self, f: pd.Series, best: pd.Series, on: date, verdict: str, saving: float,
                 n_hist: int) -> list[str]:
        r = []
        sale = next_sale_info(on)
        if sale:
            if sale["running"]:
                r.append(f"🏷️ **{sale['name']}** is running now (until {sale['end']:%d %b}).")
            elif sale["days_to"] <= 14:
                r.append(f"📅 **{sale['name']}** is expected in about **{sale['days_to']} days** "
                         f"({sale['start']:%d %b}); prices usually drop during sales.")
            else:
                r.append(f"📅 Next big sale ({sale['name']}) is ~{sale['days_to']} days away.")
        if n_hist >= 3:
            vs_min = (f["f_ratio_min30"] - 1) * 100
            if vs_min <= 0.5:
                r.append("📉 Price is at its **lowest level of the last 30 days**.")
            else:
                r.append(f"📈 Price is **{vs_min:.1f}% above** its 30-day low.")
            chg = f["f_chg_7d"] * 100
            if abs(chg) >= 1:
                r.append(f"{'⬆️' if chg > 0 else '⬇️'} Price changed {chg:+.1f}% in the last 7 days.")
        else:
            r.append("ℹ️ Little price history for this product yet, so the advice relies mainly on "
                     "the sale calendar and price vs MRP. Search it again on other days to build history.")
        if f["f_price_vs_mrp"] < 0.999:
            r.append(f"💸 Currently {(1 - f['f_price_vs_mrp']) * 100:.0f}% below MRP.")
        if verdict == "WAIT" and saving > 0:
            r.append(f"🤖 Model expects the price could fall to about **₹{best['price'] - saving:,.0f}** "
                     f"(save ~₹{saving:,.0f}) within {config.HORIZON_DAYS} days.")
        elif verdict == "BUY NOW":
            r.append(f"🤖 Model does not expect a meaningful drop (≥{config.DROP_THRESHOLD:.0%}) "
                     f"in the next {config.HORIZON_DAYS} days.")
        return r

    # ------------------------------------------------------------------
    def advise_catalog(self, product_id: str, as_of: date | None = None) -> Advice:
        """
        Advice for a catalogue product using its price history.
        as_of: a past date to 'replay' (backtest); default = today.
        """
        p = get_product(product_id)
        h = product_history(product_id)
        day = pd.Timestamp(as_of) if as_of else h["date"].max()
        today = h[h["date"] == day]
        if today.empty:
            raise ValueError(f"No data for {product_id} on {day.date()} (before launch?)")
        offers = [{"store": r.store, "price": r.price, "mrp": r.mrp} for r in today.itertuples()]
        past = h[h["date"] < day]
        histories = {s: g.set_index("date")["price"] for s, g in past.groupby("store")}
        return self._advise(offers, histories, p["category"], day.date())

    @staticmethod
    def actual_outcome(product_id: str, as_of: date, store: str) -> dict | None:
        """What really happened in the 7 days after as_of (for backtesting)."""
        h = product_history(product_id)
        h = h[h["store"] == store]
        day = pd.Timestamp(as_of)
        fut = h[(h["date"] > day) & (h["date"] <= day + pd.Timedelta(days=config.HORIZON_DAYS))]
        now = h[h["date"] == day]
        if len(fut) < config.HORIZON_DAYS or now.empty:
            return None
        price, low = float(now["price"].iloc[0]), float(fut["price"].min())
        return {"price": price, "actual_min": low,
                "dropped": low <= price * (1 - config.DROP_THRESHOLD),
                "low_date": fut.loc[fut["price"].idxmin(), "date"].date()}

    def advise_live(self, offers: list[dict], product_key: str, title: str) -> Advice:
        """Advice for a live search result using the SQLite price log as history."""
        on = date.today()
        hist = storage.get_history(product_key)
        hist = hist[hist["date"] < pd.Timestamp(on)]
        histories = {s: g.set_index("date")["price"] for s, g in hist.groupby("store")}
        stores_known = [o for o in offers if o["store"] in config.STORES] or offers
        return self._advise(stores_known, histories, infer_category(title), on)

    def top_features(self, n: int = 8) -> list[tuple[str, float]]:
        imp = self.metrics["feature_importance"]["classifier"]
        return [(FEATURE_LABELS.get(k, k), v) for k, v in sorted(imp.items(), key=lambda x: -x[1])[:n]]
