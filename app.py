"""
SmartBuy - ML-Powered Live Price Comparison Platform
Streamlit dashboard.   Run:  streamlit run app.py
"""
from __future__ import annotations

import os

# Limit math-library threads BEFORE numpy loads (avoids "OpenBLAS error: Memory
# allocation failed" on Windows machines with many CPU cores).
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
from src import storage
from src.advisor import Advisor
from src.catalog import CATALOG, CATEGORIES, catalog_frame, display_name, get_product
from src.collectors import (SourceError, check_serpapi_key, fetch_catalog, fetch_demo_api,
                            fetch_serpapi, scrape_product_url)
from src.data_generator import build_dataset, product_history
from src.features import FEATURE_LABELS, next_sale_info
from src.matching import match_offers, product_key
from src.models import train_models
from src.scoring import score_offers

st.set_page_config(page_title="SmartBuy", page_icon="🛒", layout="wide")

# Fixed colour per store (colour follows the store everywhere, never its rank)
STORE_COLORS = {"Amazon": "#2a78d6", "Flipkart": "#eb6834", "Croma": "#1baf7a",
                "Reliance Digital": "#eda100"}
OTHER_COLOR = "#8a8984"
LIVE, CATALOG_SRC, DEMO = ("🌐 Live prices (SerpAPI)", f"📦 Product catalog (offline, {len(CATALOG):,} products)",
                           "🧪 Demo public API (DummyJSON)")
SOURCES = [LIVE, CATALOG_SRC, DEMO]
EXAMPLES = ["iPhone 17", "Galaxy S25 Ultra", "OnePlus 13", "MacBook Air M4", "Sony WH-1000XM6",
            "LG 55 inch TV", "1.5 Ton 5 Star AC", "PS5"]

st.markdown("""
<style>
.verdict {border-radius: 14px; padding: 18px 22px; margin-bottom: 8px;}
.verdict h2 {margin: 0; font-size: 2.1rem; letter-spacing: .5px;}
.verdict p {margin: 4px 0 0 0; opacity: .85;}
.buy  {background: rgba(27,175,122,.14); border: 1.5px solid #1baf7a;}
.wait {background: rgba(237,161,0,.14);  border: 1.5px solid #eda100;}
.best {border-radius: 14px; padding: 16px 20px; background: rgba(42,120,214,.10);
       border: 1.5px solid #2a78d6;}
.best h3 {margin: 0 0 4px 0;}
.small-muted {font-size: .85rem; opacity: .7;}
</style>""", unsafe_allow_html=True)


def inr(x) -> str:
    if x is None or pd.isna(x):
        return "—"
    return f"₹{x:,.0f}"


def color_of(store: str) -> str:
    return STORE_COLORS.get(store, OTHER_COLOR)


# ---------------------------------------------------------------------------
# Cached resources
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_training_data() -> pd.DataFrame:
    return build_dataset()


@st.cache_resource(show_spinner=False)
def get_advisor() -> Advisor:
    return Advisor()


def first_run_setup():
    """Generate the dataset and train the models the first time the app runs."""
    if not config.HISTORY_CSV.exists() or not config.REGRESSOR_PATH.exists():
        with st.spinner("First run: generating the historical dataset and training the ML models "
                        "(about 2 minutes)..."):
            train_models(verbose=False)
        st.cache_data.clear()
        st.cache_resource.clear()


first_run_setup()
advisor = get_advisor()
metrics = advisor.metrics
def _valid_key(v) -> bool:
    v = str(v or "").strip()
    return len(v) >= 30 and "your" not in v.lower()   # ignores placeholders from secrets.toml.example


def resolve_serpapi_key() -> str:
    """Find the SerpAPI key without typing: Streamlit secrets -> environment -> config.py."""
    names = ("SERPAPI_KEY", "SERPAPI_API_KEY", "serpapi_key", "SERPAPI")
    try:
        for n in names:
            if _valid_key(st.secrets.get(n)):
                return str(st.secrets[n]).strip()
    except Exception:
        pass
    for n in names:
        if _valid_key(os.getenv(n)):
            return os.getenv(n).strip()
    try:
        if _valid_key(config.get_serpapi_key()):
            return config.get_serpapi_key().strip()
    except Exception:
        pass
    return ""


saved_key = resolve_serpapi_key()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🛒 SmartBuy")
    st.caption("ML-Powered Live Price Comparison")
    source = st.radio("Data source", SOURCES, index=0 if saved_key else 1,
                      help="Live prices = real Amazon/Flipkart/Croma/Reliance Digital prices via Google "
                           "Shopping India (SerpAPI key needed). Product catalog = 1,000+ products, "
                           "works offline. Demo API = small public test catalogue.")
    api_key, only_major, use_cache = "", False, True
    if source == LIVE:
        api_key = st.text_input("SerpAPI key", value=saved_key, type="password",
                                help="Free key at serpapi.com. Save it permanently in .streamlit/secrets.toml")
        if not api_key:
            st.info("Get a free key at **serpapi.com** → Dashboard → copy *Your Private API Key*.")
        only_major = st.checkbox("Only Amazon, Flipkart, Croma, Reliance", value=False,
                                 help="Off = also show other sellers (Vijay Sales, JioMart, ...)")
        use_cache = st.checkbox("Reuse results for 6 hours (saves quota)", value=True)
        if api_key and st.button("🔑 Check key & searches left"):
            try:
                acc = check_serpapi_key(api_key)
                st.success(f"Key OK · plan: {acc.get('plan_name', '?')} · searches left this month: "
                           f"{acc.get('total_searches_left', acc.get('plan_searches_left', '?'))}")
            except SourceError as e:
                st.error(str(e))
    st.divider()
    price_weight = st.slider("Deal score: weight on price", 0.0, 1.0, config.DEFAULT_PRICE_WEIGHT, 0.05,
                             help="Remaining weight goes to the (review-adjusted) rating.")
    log_enabled = st.checkbox("Log live prices to database", value=True)
    st.divider()
    st.caption(f"Models trained: {metrics['trained_at'].replace('T', ' ')} on "
               f"{metrics['products']} products ({metrics['data_start']} → {metrics['data_end']})")
    if st.button("🔄 Regenerate data & retrain", help="Rebuilds the training data up to today and retrains (~2 min)"):
        with st.spinner("Retraining (about 2 minutes)..."):
            train_models(force_new_data=True, verbose=False)
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("SmartBuy: ML-Powered Live Price Comparison")
st.caption("Compare prices across Amazon, Flipkart, Croma and Reliance Digital, "
           "and let machine learning tell you whether to **buy now or wait**.")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Products in catalog", f"{len(CATALOG):,}", f"{len(CATEGORIES)} categories", delta_color="off")
c2.metric("Price-prediction MAE", inr(metrics["regressor"]["mae_inr"]),
          f"-{metrics['regressor']['improvement_pct']}% vs naive", delta_color="normal")
c3.metric("Buy/Wait accuracy", f"{metrics['classifier']['accuracy']:.1%}",
          f"+{(metrics['classifier']['accuracy'] - metrics['classifier']['baseline_accuracy']) * 100:.1f} pts vs baseline")
sale = next_sale_info()
c4.metric("Next sale event", sale["name"] if sale else "—",
          ("running now" if sale and sale["running"] else f"in {sale['days_to']} days") if sale else None,
          delta_color="off")

tab_cmp, tab_adv, tab_hist, tab_url, tab_model, tab_data = st.tabs(
    ["🔎 Compare Prices", "🤖 Buy / Wait Advisor", "📈 Price History", "🔗 Track a URL",
     "📊 Model Performance", "🗄️ Data"])


# ---------------------------------------------------------------------------
# Shared UI pieces
# ---------------------------------------------------------------------------
def product_picker(prefix: str, default_id: str = "P0001") -> str:
    """Category filter + searchable product dropdown over the whole catalogue."""
    a, b = st.columns([1, 3])
    cats = ["All categories"] + CATEGORIES
    default = get_product(default_id)
    cat = a.selectbox("Category", cats, key=f"{prefix}_cat",
                      index=cats.index(default["category"]) if default else 0)
    items = [p for p in CATALOG if cat == "All categories" or p["category"] == cat]
    ids = [p["id"] for p in items]
    idx = ids.index(default_id) if default_id in ids else 0
    return b.selectbox(f"Product ({len(items):,} — type to search)", ids, index=idx, key=f"{prefix}_pid",
                       format_func=lambda i: display_name(get_product(i)))


def verdict_card(adv, title: str = ""):
    cls = "buy" if adv.verdict == "BUY NOW" else "wait"
    icon = "✅" if adv.verdict == "BUY NOW" else "⏳"
    sub = (f"Best price now {inr(adv.current_price)} at {adv.store} · "
           f"predicted 7-day low {inr(adv.predicted_min)}")
    st.markdown(f"""<div class="verdict {cls}">
        <div class="small-muted">ML recommendation{(' · ' + title) if title else ''}</div>
        <h2>{icon} {adv.verdict}</h2><p>{sub}</p></div>""", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Chance of a ≥3% drop", f"{adv.wait_probability:.0%}")
    m2.metric("Expected saving if you wait", inr(adv.expected_saving))
    m3.metric("Model confidence", f"{adv.confidence:.0%}")
    with st.container(border=True):
        st.markdown("**Why?**")
        for r in adv.reasons:
            st.markdown(f"- {r}")


def price_bar_chart(df: pd.DataFrame):
    df = df.sort_values("price")
    cheapest = df["price"].min()
    fig = go.Figure(go.Bar(
        x=df["store"], y=df["price"], marker_color=[color_of(s) for s in df["store"]],
        marker_line_width=0, text=[inr(p) + ("  ★" if p == cheapest else "") for p in df["price"]],
        textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Price: ₹%{y:,.0f}<extra></extra>"))
    fig.update_layout(title="Price by store (★ = cheapest)", height=380, bargap=0.45,
                      yaxis=dict(title="Price (₹)", tickprefix="₹", tickformat=",",
                                 range=[0, df["price"].max() * 1.15], gridcolor="rgba(128,128,128,.15)"),
                      xaxis_title=None, margin=dict(t=50, b=10, l=10, r=10), showlegend=False)
    st.plotly_chart(fig, key=f"bar_{hash(tuple(df['price']))}_{hash(tuple(df['store']))}")


def add_sale_shading(fig, start, end):
    for ev in config.sale_events(range(start.year, end.year + 1)):
        s, e = pd.Timestamp(ev["start"]), pd.Timestamp(ev["end"]) + pd.Timedelta(days=1)
        if e < start or s > end:
            continue
        fig.add_vrect(x0=s, x1=e, fillcolor="rgba(128,128,128,.13)", line_width=0, layer="below",
                      annotation_text=ev["name"].split(" (")[0], annotation_position="top left",
                      annotation_font_size=9, annotation_font_color="gray")


def history_chart(h: pd.DataFrame, title: str, predicted: tuple | None = None, shade: bool = True,
                  height: int = 420, key: str = ""):
    fig = go.Figure()
    for store in [s for s in config.STORES if s in set(h["store"])] + \
                 sorted(set(h["store"]) - set(config.STORES)):
        g = h[h["store"] == store].sort_values("date")
        fig.add_trace(go.Scatter(
            x=g["date"], y=g["price"], name=store, mode="lines+markers" if len(g) < 40 else "lines",
            line=dict(color=color_of(store), width=2, shape="hv"), marker=dict(size=8),
            hovertemplate=f"<b>{store}</b><br>%{{x|%d %b %Y}}<br>₹%{{y:,.0f}}<extra></extra>"))
    if predicted:
        d0, d1, value = predicted
        fig.add_trace(go.Scatter(x=[d0, d1], y=[value, value], name="Predicted 7-day low",
                                 mode="lines", line=dict(color="#6250d6", width=2, dash="dash"),
                                 hovertemplate="Predicted low ₹%{y:,.0f}<extra></extra>"))
    if shade and not h.empty:
        add_sale_shading(fig, h["date"].min(), h["date"].max() + pd.Timedelta(days=8))
    fig.update_layout(title=title, height=height, hovermode="x unified",
                      yaxis=dict(title="Price (₹)", tickprefix="₹", tickformat=",",
                                 gridcolor="rgba(128,128,128,.15)"),
                      xaxis=dict(gridcolor="rgba(128,128,128,.08)"),
                      legend=dict(orientation="h", y=-0.15), margin=dict(t=50, b=10, l=10, r=10))
    st.plotly_chart(fig, key=key or f"hist_{title}")


# ---------------------------------------------------------------------------
# TAB 1 - Compare prices
# ---------------------------------------------------------------------------
def run_search(query: str) -> dict:
    info: dict = {}
    if source == CATALOG_SRC:
        offers, total = fetch_catalog(query)
        info["total"] = total
    elif source == DEMO:
        offers = fetch_demo_api(query)
    else:
        offers, info = fetch_serpapi(query, api_key, use_cache=use_cache)
        info["raw"] = offers
        if only_major:
            offers = [o for o in offers if o["store"] in config.STORES]
    matched = match_offers(query, offers)
    if log_enabled and source != CATALOG_SRC and not info.get("cached"):
        storage.log_offers([o for g in matched["groups"] for o in g["offers"]], query)
    return {"query": query, "source": source, "offers": offers, "matched": matched, "info": info}


with tab_cmp:
    with st.form("search_form"):
        q1, q2 = st.columns([4, 1])
        query = q1.text_input("Search a product", value="iPhone 17", key="query_input",
                              placeholder="e.g. iPhone 17 256GB, Galaxy S25 Ultra, LG 55 inch TV, 1.5 ton AC")
        q2.write("")
        q2.write("")
        submitted = q2.form_submit_button("Compare prices", type="primary")
    if source == LIVE:
        st.caption("🌐 Live mode: real prices from Google Shopping India (Amazon, Flipkart, Croma, Reliance "
                   "Digital and other sellers). Any product works, including brand-new launches.")
    elif source == CATALOG_SRC:
        st.caption("📦 Offline catalog: " + " · ".join(EXAMPLES) + ". Prices are simulated by SmartBuy's "
                   "price model, not live; switch to 🌐 Live prices for real-time store prices.")
    else:
        st.caption("🧪 Demo API: DummyJSON is a small public test catalogue (older products, USD prices), "
                   "store prices are simulated. Try: iPhone, Samsung, laptop, watch, perfume.")

    if submitted and query.strip():
        with st.spinner(f"Fetching prices for '{query}'..."):
            try:
                st.session_state["search_result"] = run_search(query.strip())
            except SourceError as e:
                st.session_state.pop("search_result", None)
                st.error(str(e))

    res = st.session_state.get("search_result")
    if res:
        groups = res["matched"]["groups"]
        info = res.get("info", {})
        msg = f"{len(res['offers'])} offers fetched from **{res['source']}**"
        if info.get("cached"):
            msg += " (cached result, no API credit used)"
        msg += f" · {len(groups)} matching product(s) · {len(res['matched']['rejected'])} excluded"
        st.caption(msg)
        if info.get("total", 0) > len(groups):
            st.caption(f"Showing the top {len(groups)} of {info['total']} matching catalog products; "
                       "add details (model, storage, size) to narrow it down.")
        if not groups:
            st.warning(f"No offers matched '{res['query']}'.")
            near = sorted(res["matched"]["rejected"], key=lambda o: -o["match_score"])[:5]
            near = [o for o in near if o["match_score"] >= 60]
            if near:
                st.info("Closest results: " + " · ".join(f"*{o['title'][:70]}* ({o['reason']})" for o in near))
            if res["source"] != LIVE:
                st.info("💡 This product isn't in the offline data. Select **🌐 Live prices (SerpAPI)** in the "
                        "sidebar to search real Amazon / Flipkart / Croma / Reliance Digital prices for any product.")
        else:
            labels = [f"{g['name'][:90]}  —  {g['stores']} store(s), from {inr(g['min_price'])}" for g in groups]
            idx = st.selectbox(f"Matched product / variant ({len(groups)})", range(len(groups)),
                               format_func=lambda i: labels[i]) if len(groups) > 1 else 0
            group = groups[idx]
            scored = score_offers(group["offers"], price_weight)
            st.session_state["selected_group"] = group

            left, right = st.columns([1.15, 1])
            with left:
                cheapest = scored.loc[scored["price"].idxmin()]
                top = scored.iloc[0]
                spread = scored["price"].max() - scored["price"].min()
                st.markdown(f"""<div class="best"><div class="small-muted">Cheapest store</div>
                    <h3>🏆 {cheapest['store']} — {inr(cheapest['price'])}</h3>
                    <div>Save <b>{inr(spread)}</b> vs the most expensive store ·
                    Best overall deal score: <b>{top['store']}</b> ({top['deal_score']:.1f}/100)</div>
                    </div>""", unsafe_allow_html=True)
                st.write("")
                table = pd.DataFrame({
                    "Rank": scored["rank"], "Store": scored["store"], "Product title": scored["title"],
                    "Price": scored["price"].map(inr), "MRP": scored["mrp"].map(inr),
                    "Discount": scored.get("discount_pct", pd.Series(dtype=float)).map(
                        lambda d: "—" if pd.isna(d) else f"{d:.0f}%"),
                    "Rating": scored["rating"].map(lambda r: "—" if pd.isna(r) else f"{r:.1f} ★"),
                    "Reviews": scored["reviews"].map(lambda r: "—" if pd.isna(r) else f"{int(r):,}"),
                    "Deal score": scored["deal_score"].round(1),
                    "Link": scored["url"],
                })
                st.dataframe(table, hide_index=True, column_config={
                    "Deal score": st.column_config.ProgressColumn("Deal score", min_value=0, max_value=100,
                                                                  format="%.1f"),
                    "Link": st.column_config.LinkColumn("Link", display_text="Open"),
                    "Product title": st.column_config.TextColumn(width="large"),
                })
            with right:
                price_bar_chart(scored)

            st.subheader("🤖 Should you buy now or wait?")
            if get_product(group["key"]):
                adv = advisor.advise_catalog(group["key"])
            else:
                adv = advisor.advise_live(group["offers"], group["key"], group["name"])
            verdict_card(adv, group["name"][:80])

            with st.expander(f"Why were {len(res['matched']['rejected'])} results excluded?"):
                rej = pd.DataFrame(res["matched"]["rejected"])
                if rej.empty:
                    st.write("Nothing was excluded.")
                else:
                    rej = rej.sort_values("match_score", ascending=False)
                    st.dataframe(pd.DataFrame({"Store": rej["store"], "Title": rej["title"],
                                               "Price": rej["price"].map(inr),
                                               "Match score": rej["match_score"],
                                               "Reason": rej["reason"]}).head(300), hide_index=True)
        if info.get("raw") is not None:
            with st.expander(f"Raw live results from SerpAPI ({len(info['raw'])})"):
                raw = pd.DataFrame(info["raw"])
                if not raw.empty:
                    st.dataframe(raw[["store", "title", "price", "rating", "reviews", "url"]], hide_index=True,
                                 column_config={"url": st.column_config.LinkColumn("Link", display_text="Open")})
    else:
        st.info("Search for a product above to compare prices across stores.")


# ---------------------------------------------------------------------------
# TAB 2 - Buy/Wait advisor
# ---------------------------------------------------------------------------
with tab_adv:
    st.markdown("Pick any of the catalog products to see the model's recommendation, the 7-day price "
                "forecast and the reasons. Use **Backtest** to replay a past date and check the model "
                "against what actually happened.")
    pid = product_picker("adv")
    hist_p = product_history(pid)
    mode = st.radio("Mode", ["Today", "Backtest a past date"], horizontal=True)
    as_of = None
    if mode == "Backtest a past date":
        hmin = hist_p["date"].min().date() + timedelta(days=35)
        hmax = hist_p["date"].max().date() - timedelta(days=config.HORIZON_DAYS)
        if hmin >= hmax:
            st.info("This product launched recently; not enough history to backtest yet.")
        else:
            as_of = st.slider("Replay date", min_value=hmin, max_value=hmax,
                              value=max(hmin, hmax - timedelta(days=60)), format="DD MMM YYYY")

    adv = advisor.advise_catalog(pid, as_of)
    day = pd.Timestamp(as_of) if as_of else hist_p["date"].max()
    name = display_name(get_product(pid))
    v1, v2 = st.columns([1, 1.3])
    with v1:
        verdict_card(adv, f"as of {day:%d %b %Y}")
        if as_of:
            out = Advisor.actual_outcome(pid, as_of, adv.store)
            if out:
                correct = (adv.verdict == "WAIT") == out["dropped"]
                st.markdown(f"**What actually happened at {adv.store}:** lowest price in the next "
                            f"{config.HORIZON_DAYS} days was **{inr(out['actual_min'])}** "
                            f"(on {out['low_date']:%d %b}), "
                            f"{'a drop' if out['dropped'] else 'no meaningful drop'}. "
                            f"Prediction was {'✅ correct' if correct else '❌ wrong'}.")
    with v2:
        g = go.Figure(go.Indicator(
            mode="gauge+number", value=adv.wait_probability * 100,
            number={"suffix": "%"}, title={"text": "Probability the price drops ≥3% in 7 days"},
            gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#6250d6", "thickness": 0.3},
                   "steps": [{"range": [0, 50], "color": "rgba(27,175,122,.25)"},
                             {"range": [50, 100], "color": "rgba(237,161,0,.25)"}],
                   "threshold": {"line": {"color": "gray", "width": 2}, "value": 50}}))
        g.update_layout(height=260, margin=dict(t=60, b=10, l=30, r=30))
        st.plotly_chart(g, key="gauge")
        ps = adv.per_store.copy()
        st.dataframe(pd.DataFrame({
            "Store": ps["store"], "Price": ps["price"].map(inr),
            "Predicted 7-day low": ps["predicted_min_7d"].map(inr),
            "Drop probability": ps["wait_probability"].map(lambda p: f"{p:.0%}"),
        }), hide_index=True)

    window = hist_p[(hist_p["date"] <= day + pd.Timedelta(days=config.HORIZON_DAYS if as_of else 0))
                    & (hist_p["date"] >= day - pd.Timedelta(days=120))]
    history_chart(window, f"{name}: last 120 days" + (" + the following week" if as_of else ""),
                  predicted=(day, day + pd.Timedelta(days=config.HORIZON_DAYS), adv.predicted_min),
                  key="adv_hist")
    st.caption("Grey bands = sale events. Dashed line = the model's predicted lowest price over the next 7 days.")

    sel = st.session_state.get("selected_group")
    if sel and not get_product(sel["key"]):
        st.divider()
        st.markdown(f"**Last live search:** {sel['name']}")
        verdict_card(advisor.advise_live(sel["offers"], sel["key"], sel["name"]), "live search")


# ---------------------------------------------------------------------------
# TAB 3 - Price history
# ---------------------------------------------------------------------------
with tab_hist:
    which = st.radio("History source", ["Product catalog (2-year history)", "My live price log (SQLite)"],
                     horizontal=True)
    if which.startswith("Product"):
        hp = product_picker("hist")
        hh_all = product_history(hp)
        stores = st.multiselect("Stores", config.STORES, default=config.STORES)
        dmin, dmax = hh_all["date"].min().date(), hh_all["date"].max().date()
        rng = st.slider("Date range", dmin, dmax, (max(dmin, dmax - timedelta(days=365)), dmax),
                        format="DD MMM YYYY")
        hh = hh_all[hh_all["store"].isin(stores) &
                    hh_all["date"].between(pd.Timestamp(rng[0]), pd.Timestamp(rng[1]))]
        p = get_product(hp)
        if p.get("launch") and pd.Timestamp(p["launch"]) > pd.Timestamp(date.today() - timedelta(days=730)):
            st.caption(f"Launched {pd.Timestamp(p['launch']):%d %b %Y}; history starts at launch.")
        if hh.empty:
            st.info("No data for this selection.")
        else:
            history_chart(hh, display_name(p), key="hist_main")
            stats = hh.groupby("store")["price"].agg(["min", "mean", "max", "last"]).reindex(
                [s for s in config.STORES if s in stores])
            stats["drop from high"] = (1 - stats["min"] / stats["max"]) * 100
            st.dataframe(pd.DataFrame({
                "Store": stats.index, "Lowest": stats["min"].map(inr), "Average": stats["mean"].map(inr),
                "Highest": stats["max"].map(inr), "Latest": stats["last"].map(inr),
                "Low vs high": stats["drop from high"].map(lambda d: f"-{d:.0f}%")}), hide_index=True)
    else:
        lp = storage.logged_products()
        if lp.empty:
            st.info("Your live price log is empty. Search with **🌐 Live prices** (or the demo API, or track a "
                    "URL) and every fetched price is saved here. Search the same product on different days "
                    "to build a real price history.")
        else:
            labels = {r.product_key: f"{r.title[:80]}  ({r.records} records, {r.days} day(s))"
                      for r in lp.itertuples()}
            key = st.selectbox("Logged product", list(labels), format_func=lambda k: labels[k])
            lh = storage.get_history(key)
            history_chart(lh, labels[key].split("  (")[0], shade=False, key="log_hist")
            raw = storage.get_log()
            st.dataframe(raw[raw["product_key"] == key][["ts", "store", "title", "price", "rating", "source"]],
                         hide_index=True)


# ---------------------------------------------------------------------------
# TAB 4 - Track a URL (BeautifulSoup scraper)
# ---------------------------------------------------------------------------
with tab_url:
    st.markdown("Paste a product page URL. SmartBuy's BeautifulSoup scraper reads the price from the "
                "page's structured data (JSON-LD / meta tags) and saves it to your price log. "
                "Works best with Croma and Reliance Digital; Amazon and Flipkart often block scrapers, "
                "so use 🌐 Live prices for those.")
    with st.form("url_form"):
        url = st.text_input("Product URL", placeholder="https://www.croma.com/...")
        go_btn = st.form_submit_button("Fetch price", type="primary")
    if go_btn and url.strip():
        with st.spinner("Scraping..."):
            try:
                item = scrape_product_url(url.strip())
                item["product_key"] = product_key(item["title"] or url)
                if log_enabled:
                    storage.log_offers([item], query="url")
                storage.add_tracked_url(url.strip(), item["title"] or "")
                st.success(f"**{item['title']}** — {inr(item['price'])} at {item['store']}"
                           + (f" · {item['rating']} ★ ({item['reviews']:,} reviews)"
                              if item.get("rating") and item.get("reviews") else ""))
            except SourceError as e:
                st.error(str(e))
    tracked = storage.tracked_urls()
    if not tracked.empty:
        st.subheader("Tracked URLs")
        st.dataframe(tracked, hide_index=True, column_config={"url": st.column_config.LinkColumn("URL")})
        if st.button("🔄 Refresh all tracked prices"):
            ok, fails = 0, []
            for u in tracked["url"]:
                try:
                    it = scrape_product_url(u)
                    it["product_key"] = product_key(it["title"] or u)
                    storage.log_offers([it], query="url")
                    ok += 1
                except SourceError as e:
                    fails.append(f"{u}: {e}")
            st.success(f"Updated {ok} of {len(tracked)} URLs.")
            for f in fails:
                st.warning(f)


# ---------------------------------------------------------------------------
# TAB 5 - Model performance
# ---------------------------------------------------------------------------
with tab_model:
    r, c = metrics["regressor"], metrics["classifier"]
    st.markdown(
        f"Trained on **{metrics['products'] - metrics['unseen_products']} products** "
        f"({metrics['train_rows']:,} rows + {metrics['augmented_rows']:,} augmented). Evaluated on a "
        f"**time-based split**: everything from **{metrics['test_start']}** onwards "
        f"({metrics['test_rows']:,} store-days) is unseen, and **{metrics['unseen_products']} products were never "
        f"seen at all** during training. Horizon: next {metrics['horizon_days']} days; a 'drop' means the price "
        f"falls by at least {metrics['drop_threshold']:.0%}.")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("RandomForest MAE", inr(r["mae_inr"]), f"naive baseline {inr(r['baseline_mae_inr'])}",
              delta_color="off")
    k2.metric("MAPE", f"{r['mape_pct']:.2f}%", f"baseline {r['baseline_mape_pct']:.2f}%", delta_color="off")
    k3.metric("GradientBoosting accuracy", f"{c['accuracy']:.1%}",
              f"majority baseline {c['baseline_accuracy']:.1%}", delta_color="off")
    k4.metric("ROC-AUC", f"{c['roc_auc']:.3f}")
    k5, k6, k7, k8 = st.columns(4)
    k5.metric("Precision (WAIT)", f"{c['precision']:.1%}")
    k6.metric("Recall (WAIT)", f"{c['recall']:.1%}")
    k7.metric("F1 score", f"{c['f1']:.3f}")
    k8.metric("Accuracy on never-seen products", f"{metrics['unseen_products_eval']['accuracy']:.1%}")

    m1, m2 = st.columns(2)
    with m1:
        fig = go.Figure(go.Bar(x=["Naive baseline<br>(price stays the same)", "RandomForest"],
                               y=[r["baseline_mae_inr"], r["mae_inr"]], marker_color=["#8a8984", "#2a78d6"],
                               text=[inr(r["baseline_mae_inr"]), inr(r["mae_inr"])], textposition="outside",
                               cliponaxis=False))
        fig.update_layout(title="Price prediction error (MAE, lower is better)", height=340, bargap=0.5,
                          yaxis=dict(tickprefix="₹", tickformat=",", gridcolor="rgba(128,128,128,.15)",
                                     range=[0, r["baseline_mae_inr"] * 1.2]),
                          margin=dict(t=50, b=10, l=10, r=10))
        st.plotly_chart(fig, key="mae_bar")
    with m2:
        fig = go.Figure(go.Bar(x=[f"Majority baseline<br>(always {c['baseline_label']})", "GradientBoosting"],
                               y=[c["baseline_accuracy"] * 100, c["accuracy"] * 100],
                               marker_color=["#8a8984", "#2a78d6"],
                               text=[f"{c['baseline_accuracy']:.1%}", f"{c['accuracy']:.1%}"],
                               textposition="outside", cliponaxis=False))
        fig.update_layout(title="Buy/Wait accuracy (higher is better)", height=340, bargap=0.5,
                          yaxis=dict(ticksuffix="%", range=[0, 105], gridcolor="rgba(128,128,128,.15)"),
                          margin=dict(t=50, b=10, l=10, r=10))
        st.plotly_chart(fig, key="acc_bar")

    st.markdown("**Generalisation check — products seen in training vs never-seen products (same test period)**")
    sp, up = metrics["seen_products"], metrics["unseen_products_eval"]
    st.dataframe(pd.DataFrame({
        "Test group": ["Products seen in training", "Never-seen products"],
        "Rows": [f"{sp['rows']:,}", f"{up['rows']:,}"],
        "MAE": [inr(sp["mae_inr"]), inr(up["mae_inr"])],
        "MAPE": [f"{sp['mape_pct']:.2f}% (base {sp['baseline_mape_pct']:.2f}%)",
                 f"{up['mape_pct']:.2f}% (base {up['baseline_mape_pct']:.2f}%)"],
        "Accuracy": [f"{sp['accuracy']:.1%} (base {sp['baseline_accuracy']:.1%})",
                     f"{up['accuracy']:.1%} (base {up['baseline_accuracy']:.1%})"],
        "F1": [f"{sp['f1']:.3f}", f"{up['f1']:.3f}"],
    }), hide_index=True)

    st.markdown("**Results by category**")
    bc = pd.DataFrame(metrics["by_category"]).T.reset_index().rename(columns={"index": "Category"})
    st.dataframe(pd.DataFrame({
        "Category": bc["Category"], "Test rows": bc["rows"].map(lambda v: f"{int(v):,}"),
        "MAPE": bc["mape_pct"].map(lambda v: f"{v:.2f}%"),
        "Naive MAPE": bc["baseline_mape_pct"].map(lambda v: f"{v:.2f}%"),
        "Accuracy": bc["accuracy"].map(lambda v: f"{v:.1%}"),
        "Majority baseline": bc["baseline_accuracy"].map(lambda v: f"{v:.1%}"),
        "WAIT share": bc["wait_rate"].map(lambda v: f"{v:.0%}"),
    }), hide_index=True)

    m3, m4 = st.columns(2)
    with m3:
        cm = c["confusion_matrix"]
        fig = go.Figure(go.Heatmap(z=cm, x=["Predicted BUY NOW", "Predicted WAIT"],
                                   y=["Actual BUY NOW", "Actual WAIT"], colorscale=[[0, "#eaf2fc"], [1, "#1c5aa6"]],
                                   showscale=False, text=[[f"{v:,}" for v in row] for row in cm],
                                   texttemplate="%{text}", textfont={"size": 16},
                                   hovertemplate="%{y} / %{x}: %{z:,}<extra></extra>"))
        fig.update_layout(title="Confusion matrix (test set)", height=340, yaxis=dict(autorange="reversed"),
                          margin=dict(t=50, b=10, l=10, r=10))
        st.plotly_chart(fig, key="cm")
    with m4:
        tp_path = config.MODEL_DIR / "test_predictions.csv"
        if tp_path.exists():
            tp = pd.read_csv(tp_path)
            tp = tp.sample(min(1500, len(tp)), random_state=0)
            lim = [tp[["future_min", "pred_min"]].min().min(), tp[["future_min", "pred_min"]].max().max()]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=lim, y=lim, mode="lines", name="Perfect prediction",
                                     line=dict(color="gray", dash="dash", width=1.5)))
            fig.add_trace(go.Scatter(x=tp["future_min"], y=tp["pred_min"], mode="markers", name="Test sample",
                                     marker=dict(size=8, color="#2a78d6", opacity=0.45,
                                                 line=dict(width=1, color="white")),
                                     hovertemplate="Actual ₹%{x:,.0f}<br>Predicted ₹%{y:,.0f}<extra></extra>"))
            fig.update_layout(title="Predicted vs actual 7-day low price", height=340,
                              xaxis=dict(title="Actual (₹)", type="log", tickprefix="₹"),
                              yaxis=dict(title="Predicted (₹)", type="log", tickprefix="₹"),
                              legend=dict(orientation="h", y=-0.25), margin=dict(t=50, b=10, l=10, r=10))
            st.plotly_chart(fig, key="scatter")

    fi = metrics["feature_importance"]
    imp = pd.DataFrame({"feature": [FEATURE_LABELS.get(k, k) for k in fi["classifier"]],
                        "Classifier": list(fi["classifier"].values()),
                        "Regressor": [fi["regressor"][k] for k in fi["classifier"]]})
    f1c, f2c = st.columns(2)
    for col, mname in ((f1c, "Classifier"), (f2c, "Regressor")):
        d = imp.sort_values(mname).tail(10)
        fig = go.Figure(go.Bar(x=d[mname], y=d["feature"], orientation="h", marker_color="#2a78d6",
                               hovertemplate="%{y}: %{x:.3f}<extra></extra>"))
        fig.update_layout(title=f"Top features — {mname}", height=380,
                          xaxis=dict(title="Importance", gridcolor="rgba(128,128,128,.15)"),
                          margin=dict(t=50, b=10, l=10, r=10))
        col.plotly_chart(fig, key=f"fi_{mname}")

    st.info("**About the training data:** multi-year store-level price histories for India are not publicly "
            "available, so the models are trained on simulated histories that reproduce real patterns (sale "
            "events, pre-sale price hikes, flash deals, depreciation, launch pricing, store and category "
            "differences). Live prices fetched through SerpAPI are logged to SQLite, so real history "
            "accumulates and can be used to retrain.")


# ---------------------------------------------------------------------------
# TAB 6 - Data
# ---------------------------------------------------------------------------
with tab_data:
    st.subheader(f"Product catalog ({len(CATALOG):,} products)")
    cf = catalog_frame()
    cat_sel = st.multiselect("Filter categories", CATEGORIES, default=[])
    view = cf[cf["category"].isin(cat_sel)] if cat_sel else cf
    st.dataframe(view.rename(columns={"base_price": "typical price"}), hide_index=True, height=300)
    st.download_button("⬇️ Download catalog.csv", cf.to_csv(index=False).encode(), "catalog.csv", "text/csv")
    st.bar_chart(cf["category"].value_counts(), horizontal=True, height=300)

    d1, d2 = st.columns(2)
    with d1:
        st.subheader("Training dataset (CSV)")
        training = load_training_data()
        st.caption(f"{len(training):,} rows · {training['product_id'].nunique()} products × "
                   f"{training['store'].nunique()} stores × up to {training['date'].nunique()} days")
        st.dataframe(training.sort_values("date", ascending=False).head(300), hide_index=True, height=300)
        st.caption(f"Full file: {config.HISTORY_CSV.name} in the data folder "
                   f"({config.HISTORY_CSV.stat().st_size / 1e6:.0f} MB)")
    with d2:
        st.subheader("Live price log (SQLite)")
        log = storage.get_log(500)
        st.caption(f"{len(storage.get_log()):,} records in data/smartbuy.db")
        st.dataframe(log, hide_index=True, height=300)
        b1, b2, b3 = st.columns(3)
        b1.download_button("⬇️ Price log CSV", storage.export_log_csv(), "price_log.csv", "text/csv")
        if b2.button("🗑️ Clear log"):
            storage.clear_log()
            st.rerun()
        if b3.button("♻️ Clear API cache"):
            storage.clear_cache()
            st.success("Cache cleared.")

    st.subheader("Sale calendar used by the model")
    today = date.today()
    evs = [e for e in config.sale_events(range(today.year, today.year + 2)) if e["end"] >= today][:10]
    st.dataframe(pd.DataFrame({
        "Event": [e["name"] for e in evs], "Starts": [e["start"].strftime("%d %b %Y") for e in evs],
        "Ends": [e["end"].strftime("%d %b %Y") for e in evs],
        "Typical discount": [f"{e['depth'][0]:.0%}–{e['depth'][1]:.0%}" for e in evs]}), hide_index=True)
    st.caption("Dates are approximate. Edit DIWALI and FIXED_SALES in config.py when stores announce sales.")
