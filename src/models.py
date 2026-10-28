"""
ML models.

  * RandomForestRegressor      -> predicts the lowest price over the next 7 days
                                  (as a ratio of today's price, converted back to Rs)
  * GradientBoostingClassifier -> predicts whether the price will drop >= 3%
                                  in the next 7 days  (WAIT vs BUY NOW)

Evaluation is deliberately strict:
  * time-based split: train on the past, test on the most recent 20% of days
  * product hold-out: part of the test set comes from products the model
    never saw during training (checks it generalises to new products)
  * baselines: "price won't change" (regression) and "always predict the
    majority class" (classification)
"""
from __future__ import annotations

import json
import time
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestRegressor
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, mean_absolute_error,
                             precision_score, recall_score, roc_auc_score)

import config
from src.data_generator import build_dataset
from src.features import FEATURES, add_history_dropout, build_training_frame


def time_split(frame: pd.DataFrame):
    dates = np.sort(frame["date"].unique())
    cutoff = pd.Timestamp(dates[int(len(dates) * (1 - config.TEST_FRACTION))])
    seen = frame["split_group"] != "unseen_product"
    # drop training rows whose 7-day target window overlaps the test period (no leakage)
    train = frame[seen & (frame["date"] < cutoff - pd.Timedelta(days=config.HORIZON_DAYS))]
    test = frame[frame["date"] >= cutoff]
    return train, test, cutoff


def _evaluate(reg, clf, test: pd.DataFrame, majority: int) -> dict:
    X, price = test[FEATURES], test["price"].values
    actual_min = test["future_min"].values
    pred_min = np.minimum(reg.predict(X), 1.0) * price
    y_true = test["y_drop"].values
    proba = clf.predict_proba(X)[:, 1]
    y_pred = (proba >= 0.5).astype(int)
    mae, naive_mae = mean_absolute_error(actual_min, pred_min), mean_absolute_error(actual_min, price)
    out = {
        "rows": int(len(test)),
        "mae_inr": round(float(mae), 2), "baseline_mae_inr": round(float(naive_mae), 2),
        "mape_pct": round(float(np.mean(np.abs(pred_min - actual_min) / actual_min) * 100), 2),
        "baseline_mape_pct": round(float(np.mean(np.abs(price - actual_min) / actual_min) * 100), 2),
        "improvement_pct": round(float((1 - mae / naive_mae) * 100), 1),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "baseline_accuracy": round(float(accuracy_score(y_true, np.full_like(y_true, majority))), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, proba)), 4) if len(set(y_true)) > 1 else None,
        "wait_rate": round(float(y_true.mean()), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
    }
    return out, pred_min, proba


def train_models(force_new_data: bool = False, verbose: bool = True) -> dict:
    t0 = time.time()
    log = print if verbose else (lambda *a, **k: None)

    log("1/4  Loading historical price dataset ...")
    history = build_dataset(force=force_new_data)
    if "split_group" not in history:
        history = build_dataset(force=True)
    n_unseen = history.loc[history["split_group"] == "unseen_product", "product_id"].nunique()
    log(f"     {len(history):,} daily price records | {history['product_id'].nunique()} products "
        f"({n_unseen} held out as never-seen) | {history['category'].nunique()} categories | "
        f"{history['store'].nunique()} stores")

    log("2/4  Engineering features ...")
    frame = build_training_frame(history)
    train, test, cutoff = time_split(frame)
    if len(train) > config.MAX_TRAIN_ROWS:
        train = train.sample(config.MAX_TRAIN_ROWS, random_state=config.RANDOM_SEED)
    train_aug = add_history_dropout(train)
    log(f"     train rows: {len(train):,} (+{len(train_aug) - len(train):,} augmented) | "
        f"test rows: {len(test):,} | test period starts {cutoff.date()}")

    log("3/4  Training RandomForest regressor and GradientBoosting classifier ...")
    reg = RandomForestRegressor(n_estimators=150, max_depth=16, min_samples_leaf=5,
                                n_jobs=2, random_state=config.RANDOM_SEED)
    reg.fit(train_aug[FEATURES], train_aug["y_ratio"])
    clf = GradientBoostingClassifier(n_estimators=200, learning_rate=0.1, max_depth=3,
                                     subsample=0.8, random_state=config.RANDOM_SEED)
    clf.fit(train_aug[FEATURES], train_aug["y_drop"])

    log("4/4  Evaluating on the held-out test period ...")
    majority = int(train["y_drop"].mean() >= 0.5)
    overall, pred_min, proba = _evaluate(reg, clf, test, majority)
    seen_mask = (test["split_group"] != "unseen_product").values
    seen, _, _ = _evaluate(reg, clf, test[seen_mask], majority)
    unseen, _, _ = _evaluate(reg, clf, test[~seen_mask], majority)
    by_cat = {}
    for cat, g in test.groupby("category"):
        r, _, _ = _evaluate(reg, clf, g, majority)
        by_cat[cat] = {k: r[k] for k in ("rows", "mape_pct", "baseline_mape_pct", "accuracy",
                                         "baseline_accuracy", "wait_rate")}

    metrics = {
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "products": int(history["product_id"].nunique()), "unseen_products": int(n_unseen),
        "train_rows": int(len(train)), "augmented_rows": int(len(train_aug) - len(train)),
        "test_rows": int(len(test)), "test_start": str(cutoff.date()),
        "data_start": str(history["date"].min().date()), "data_end": str(history["date"].max().date()),
        "horizon_days": config.HORIZON_DAYS, "drop_threshold": config.DROP_THRESHOLD,
        "regressor": {"model": "RandomForestRegressor", **{k: overall[k] for k in (
            "mae_inr", "baseline_mae_inr", "mape_pct", "baseline_mape_pct", "improvement_pct")}},
        "classifier": {"model": "GradientBoostingClassifier",
                       "baseline_label": "WAIT" if majority else "BUY NOW",
                       **{k: overall[k] for k in ("accuracy", "baseline_accuracy", "precision", "recall",
                                                  "f1", "roc_auc", "confusion_matrix")},
                       "wait_rate_test": overall["wait_rate"]},
        "seen_products": seen, "unseen_products_eval": unseen, "by_category": by_cat,
        "feature_importance": {
            "regressor": dict(zip(FEATURES, map(float, reg.feature_importances_))),
            "classifier": dict(zip(FEATURES, map(float, clf.feature_importances_))),
        },
        "train_seconds": round(time.time() - t0, 1),
    }

    joblib.dump(reg, config.REGRESSOR_PATH, compress=3)
    joblib.dump(clf, config.CLASSIFIER_PATH, compress=3)
    config.METRICS_PATH.write_text(json.dumps(metrics, indent=2))
    sample = test.assign(pred_min=pred_min, wait_proba=proba)[
        ["date", "product_id", "category", "store", "split_group", "price", "future_min", "pred_min",
         "y_drop", "wait_proba"]]
    sample.sample(min(4000, len(sample)), random_state=1).to_csv(
        config.MODEL_DIR / "test_predictions.csv", index=False)

    log(f"     Regressor  MAE: Rs {overall['mae_inr']:,.0f} (naive baseline Rs {overall['baseline_mae_inr']:,.0f})"
        f" | MAPE {overall['mape_pct']:.2f}% (baseline {overall['baseline_mape_pct']:.2f}%)")
    log(f"     Classifier accuracy: {overall['accuracy']:.1%} (majority baseline "
        f"{overall['baseline_accuracy']:.1%}) | F1 {overall['f1']:.3f} | ROC-AUC {overall['roc_auc']:.3f}")
    log(f"     Never-seen products: accuracy {unseen['accuracy']:.1%}, MAPE {unseen['mape_pct']:.2f}%")
    log(f"Done in {metrics['train_seconds']}s. Models saved to {config.MODEL_DIR}")
    return metrics


def models_ready() -> bool:
    return all(p.exists() for p in (config.REGRESSOR_PATH, config.CLASSIFIER_PATH, config.METRICS_PATH))


def load_models():
    """Load models; raises if missing or incompatible (caller retrains)."""
    reg = joblib.load(config.REGRESSOR_PATH)
    clf = joblib.load(config.CLASSIFIER_PATH)
    metrics = json.loads(config.METRICS_PATH.read_text())
    if "unseen_products_eval" not in metrics:
        raise ValueError("old metrics format")
    return reg, clf, metrics
