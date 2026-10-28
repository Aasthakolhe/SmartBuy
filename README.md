# SmartBuy: Real-Time E-Commerce Price Comparison and ML-Based Buy/Wait Recommendation System

**Short title:** SmartBuy – ML-Powered Live Price Comparison Platform

SmartBuy searches a product across **Amazon, Flipkart, Croma and Reliance Digital** (plus other
sellers), matches the same product across stores despite different titles, ranks the offers with a
**deal score**, and uses machine learning to predict whether the price will drop in the next
7 days, giving a **BUY NOW** or **WAIT** recommendation with reasons.

**Highlights**
- **Live prices** for any product (including new launches like iPhone 17) via Google Shopping India (SerpAPI)
- **1,105-product offline catalog** across 11 categories and 122 brands; works without internet
- Robust matching engine: handles marketing titles, missing brand names, colours, RAM/storage variants,
  Pro/Plus/FE/Edge variants, accessories, refurbished units and brand mismatches
- **RandomForest + GradientBoosting** models evaluated on future days **and on products never seen in training**
- SQLite price log, 6-hour API cache (saves SerpAPI quota), BeautifulSoup URL scraper, backtesting
- 13 automated tests

---

## 1. Run it in VS Code (Windows)

1. Unzip, then in VS Code: **File → Open Folder… → SmartBuy** (the folder containing `app.py`)
2. **Terminal → New Terminal** (Ctrl + `)
3. Run these commands **one at a time**, waiting for each to finish:

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python train.py
python -m streamlit run app.py
```

4. The app opens at **http://localhost:8501**. Press **Ctrl + C** in the terminal to stop it.

`python train.py` takes about 2–4 minutes and prints the model results. Note them for your report.

**Every time after that:**
```powershell
venv\Scripts\activate
python -m streamlit run app.py
```

**One-click option:** type `.\run.bat` in the terminal (or double-click it).
**From VS Code:** press **F5 → "Run SmartBuy (Streamlit)"** after selecting the `venv` interpreter
(Ctrl+Shift+P → *Python: Select Interpreter*).

macOS / Linux: same commands with `source venv/bin/activate` (or `bash run.sh`).
Requires **Python 3.10+** (3.11 or 3.12 recommended).

---

## 2. Data sources (sidebar)

| Source | Needs | What you get |
|---|---|---|
| **🌐 Live prices (SerpAPI)** | free SerpAPI key + internet | **Real current prices** from Google Shopping India: Amazon, Flipkart, Croma, Reliance Digital, Vijay Sales and more. Works for **any** product, including the latest launches. |
| **📦 Product catalog (offline)** | nothing | 1,105 products with prices from SmartBuy's price model (simulated, not live). Full 2-year history for charts, advice and backtests. |
| **🧪 Demo public API** | internet | Products from the free DummyJSON test API. Small and dated (old iPhones, etc.), USD prices, store prices simulated. Only proves the API pipeline. |

> **Why does a search say "no offers"?** In the offline catalog or demo API, the product simply
> isn't in that data. Switch to **🌐 Live prices**, which searches real stores for anything.

### Setting up live prices (5 minutes)

1. Sign up free at **https://serpapi.com** → Dashboard → copy **Your Private API Key**.
2. Either paste it in the sidebar box, **or** save it permanently: copy
   `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and paste the key inside the quotes.
   With a saved key, the app opens in Live mode automatically.
3. Click **🔑 Check key & searches left** to confirm it works.
4. Search e.g. `iPhone 17 256GB`, `Galaxy S25 Ultra`, `LG 55 inch TV`.

The free plan has a monthly search limit. SmartBuy caches each search for 6 hours, so repeating a
search doesn't use another credit. Never share or commit `secrets.toml`.

---

## 3. The dashboard

- **🔎 Compare Prices**: search, cheapest-store card, comparison table with deal scores, price bar
  chart, ML verdict, excluded results with reasons, and (live mode) the raw API results.
- **🤖 Buy / Wait Advisor**: verdict, drop-probability gauge, per-store 7-day forecast, 120-day
  chart with sale events. **Backtest** replays any past date and shows whether the model was right.
- **📈 Price History**: 2-year history of any catalog product, or your own logged live prices.
- **🔗 Track a URL**: BeautifulSoup scraper reading prices from product pages (JSON-LD/meta tags).
- **📊 Model Performance**: MAE/MAPE vs naive baseline, accuracy/precision/recall/F1/ROC-AUC vs
  majority baseline, seen vs never-seen products, results per category, confusion matrix,
  predicted-vs-actual plot, feature importances.
- **🗄️ Data**: browsable 1,105-product catalog (download CSV), training dataset, SQLite price log,
  API cache, sale calendar.

---

## 4. Project structure

```
SmartBuy/
├── app.py                   Streamlit dashboard (6 tabs)
├── train.py                 Train the models from the command line
├── config.py                Settings: stores, sale calendar, model & deal-score parameters
├── requirements.txt
├── run.bat / run.sh         One-click setup and run
├── src/
│   ├── catalog_data.py      Product master data: 1,105 SKUs, 11 categories, 122 brands
│   ├── catalog.py           Catalog access, store-specific title formats
│   ├── collectors.py        Data collection: SerpAPI (live), catalog, DummyJSON, URL scraper
│   ├── storage.py           SQLite: price log, API cache, tracked URLs
│   ├── matching.py          Product matching & comparison engine (RapidFuzz)
│   ├── scoring.py           Deal score (price competitiveness + Bayesian-adjusted rating)
│   ├── data_generator.py    Price-history simulator (per product, on demand)
│   ├── features.py          Feature engineering (19 features)
│   ├── models.py            RandomForest Regressor + GradientBoosting Classifier, evaluation
│   └── advisor.py           BUY NOW / WAIT decision with explanations
├── tests/                   13 automated tests + a realistic SerpAPI sample response
├── data/                    Created at runtime: training CSV + SQLite database
└── models/                  Created at runtime: trained models + metrics.json
```

---

## 5. How it works

**Module 1 – Data collection.** Every source returns offers in one format (title, store, price,
MRP, rating, reviews, link). The SerpAPI parser walks the whole JSON response, so it still works
if Google moves results between blocks (shopping_results, inline, categorised). Errors such as an
invalid key, an exhausted quota or no internet are shown as clear messages.

**Module 2 – Data storage.** SQLite tables: `price_log` (every live price with timestamp, which
builds real price history over time), `api_cache` (6-hour cache of API responses) and
`tracked_urls`. The training dataset is saved as CSV.

**Module 3 – Product matching & comparison.**
1. *Core title*: drops marketing text after `:` `|` `;` (Amazon-style long titles).
2. *Normalisation*: case, punctuation, `256 GB`→`256gb`, `1.5 Ton`, `28 L`, colours and filler
   words removed, synonyms (`PlayStation 5`→`ps5`, `refrigerator`→`fridge`), plurals.
3. *Relevance*: RapidFuzz `token_set_ratio` plus typo-tolerant token recall (`iphon`→`iphone`).
4. *Hard filters*: accessories and refurbished items, different variant (Pro / Plus / Max / FE /
   Edge / Fold…), different model number, different storage, different brand.
5. *Grouping*: catalog offers by product ID; live offers by a canonical key (product line + model
   numbers + variants + sizes), then a merge pass that joins a cluster into its unique superset
   (e.g. a listing that omits RAM joins the one that states it).
6. Cheapest offer per store is kept.

**Deal score (0–100)** = 100 × (w × cheapest/price + (1 − w) × Bayesian rating / 5). The Bayesian
rating shrinks ratings with few reviews toward 4.0. `w` is adjustable in the sidebar (default 0.7).

**Module 4 – Feature engineering** (19 features): price vs 7/30-day average, low and high; 1- and
7-day change; 14-day volatility; price vs MRP; price vs cheapest store; days to next / since last
sale; sale running; expected sale depth; month; weekday; weekend; store; category; price level.

**Module 5 – ML models** (horizon = 7 days):
- `RandomForestRegressor` predicts the **lowest price in the next 7 days**.
- `GradientBoostingClassifier` predicts **will the price drop ≥ 3%** → WAIT, else BUY NOW.
- **Training data**: a stratified sample of catalog products (every category represented), 2 years
  each (from launch for new models).
- **Evaluation**: time-based split (last 20% of days = test, no leakage), **plus 45 products
  held out completely** to check generalisation to new products, plus per-category results.
- History-dropout augmentation: 20% of training rows are duplicated with history features
  neutralised, so advice still works for a product searched for the first time.

**Module 6 – Web dashboard** in Streamlit with interactive Plotly charts.

### Results

Printed by `python train.py` and shown in **Model Performance**. Figures depend on the training
date. A run on 23 Oct 2026:

| Model | Metric | SmartBuy | Baseline |
|---|---|---|---|
| RandomForest Regressor | MAE (7-day low price) | ₹808 | ₹1,322 (naive: price unchanged) |
| | MAPE | 1.75% | 3.07% |
| GradientBoosting Classifier | Accuracy | 90.8% | 77.2% (always BUY NOW) |
| | F1 / ROC-AUC | 0.755 / 0.847 | |
| | Accuracy on **never-seen products** | 91.0% | |

Use the exact figures from **your own** run in the report.

### About the data (state this in your report)

Multi-year, store-level price histories for Indian e-commerce are not publicly available, so the
models are trained on **simulated** histories (`src/data_generator.py`) that reproduce real
behaviour: sticky prices, category-specific depreciation, permanent price cuts, launch pricing,
deep discounts during sale events (Big Billion Days / Great Indian Festival, Diwali, Republic Day,
Independence Day…), pre-sale price hikes, flash deals, AC seasonality, and store, brand and
category differences. Catalog prices are approximate. **Live prices come from real stores via
SerpAPI** and are logged to SQLite as real history. Sale dates in `config.py` are approximate.

---

## 6. Useful commands

| Task | Command |
|---|---|
| Start the app | `python -m streamlit run app.py` |
| Retrain models | `python train.py` |
| Rebuild training data up to today and retrain | `python train.py --new-data` |
| Run tests | `python -m pytest -q` |
| Use a different port | `python -m streamlit run app.py --server.port 8502` |

## 7. Troubleshooting

| Problem | Fix |
|---|---|
| Search shows "No offers matched" | Product isn't in the offline catalog / demo API. Use **🌐 Live prices**. |
| `'python' is not recognized` | Install Python from python.org with **"Add python.exe to PATH"** ticked, then reopen VS Code. |
| `'streamlit' is not recognized` | Activate the venv (`venv\Scripts\activate`, you should see `(venv)`), or use `python -m streamlit run app.py`. |
| `source` not recognized | That's the macOS command. On Windows use `venv\Scripts\activate`. |
| Scripts disabled in PowerShell | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| `OpenBLAS error: Memory allocation still failed` | Run `$env:OPENBLAS_NUM_THREADS="1"` first, or once: `setx OPENBLAS_NUM_THREADS 1` and reopen the terminal. Close heavy apps. |
| Error loading models after upgrading packages | Delete the `models` folder and run `python train.py`. |
| SerpAPI "Invalid API key" | Re-copy the key from serpapi.com → Dashboard; no spaces or quotes in the sidebar box. |
| SerpAPI "run out of searches" | Monthly quota used. Cached searches and the offline catalog still work. |
| URL scraper "HTTP 403/503" | That site blocks scrapers (common for Amazon/Flipkart). Use Live prices. |
| Port 8501 already in use | `python -m streamlit run app.py --server.port 8502` |
