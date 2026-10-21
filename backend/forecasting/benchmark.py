"""Compare XGBoost, LightGBM and CatBoost on the PO-line delay dataset.

Same features, same time-based split, near-default hyperparameters, CPU only.
Each library uses its own native categorical handling on the raw
vendor_id / vendor_category / sku columns.

The boosting libraries are imported lazily so the rest of the backend does not
depend on them:
    uv pip install xgboost lightgbm catboost
    python -m scripts.build_forecast_dataset --benchmark
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from forecasting.features import CATEGORICAL_COLUMNS, FEATURE_COLUMNS

SEED = 42


def _xgb(task: str):
    import xgboost as xgb

    common = {
        "n_estimators": 400, "learning_rate": 0.05, "max_depth": 6, "subsample": 0.9,
        "colsample_bytree": 0.9, "tree_method": "hist", "enable_categorical": True,
        "random_state": SEED, "n_jobs": -1,
    }
    if task == "reg":
        return xgb.XGBRegressor(objective="reg:absoluteerror", **common)
    return xgb.XGBClassifier(objective="binary:logistic", eval_metric="logloss", **common)


def _lgbm(task: str):
    import lightgbm as lgb

    common = {
        "n_estimators": 400, "learning_rate": 0.05, "num_leaves": 31, "subsample": 0.9,
        "subsample_freq": 1, "colsample_bytree": 0.9, "random_state": SEED, "verbose": -1,
    }
    if task == "reg":
        return lgb.LGBMRegressor(objective="l1", **common)
    return lgb.LGBMClassifier(objective="binary", **common)


def _cat(task: str):
    import catboost as cb

    common = {
        "iterations": 800, "learning_rate": 0.05, "depth": 6, "random_seed": SEED,
        "verbose": False, "cat_features": CATEGORICAL_COLUMNS, "thread_count": -1,
        "allow_writing_files": False,
    }
    if task == "reg":
        return cb.CatBoostRegressor(loss_function="MAE", **common)
    return cb.CatBoostClassifier(loss_function="Logloss", **common)


MODELS = {"xgboost": _xgb, "lightgbm": _lgbm, "catboost": _cat}


def _prep(df: pd.DataFrame, model: str) -> pd.DataFrame:
    X = df[FEATURE_COLUMNS].copy()
    if model == "catboost":
        # CatBoost wants plain strings for categorical columns.
        for col in CATEGORICAL_COLUMNS:
            X[col] = X[col].astype(str)
    return X


def _auc(y: np.ndarray, p: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score

    return float(roc_auc_score(y, p)) if len(np.unique(y)) > 1 else float("nan")


def run_benchmark(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    """Fit each model for regression (delay_days) and classification (is_late)."""
    from sklearn.metrics import f1_score, mean_absolute_error, root_mean_squared_error

    y_tr, y_te = train["delay_days"], test["delay_days"]
    l_tr, l_te = train["is_late"].astype(int), test["is_late"].astype(int)

    # Baseline: the vendor's historical mean delay as of the PO date.
    base = test["vendor_prior_mean_delay"].fillna(y_tr.mean())
    rows = [{
        "model": "baseline (vendor prior mean)",
        "MAE_days": mean_absolute_error(y_te, base),
        "RMSE_days": root_mean_squared_error(y_te, base),
        "AUC_late": _auc(l_te, test["vendor_prior_late_rate"].fillna(l_tr.mean())),
        "F1_late": f1_score(l_te, (base > 0).astype(int)),
    }]
    for name, make in MODELS.items():
        try:
            reg, clf = make("reg"), make("clf")
        except ImportError:
            print(f"skipping {name}: not installed")
            continue
        X_tr, X_te = _prep(train, name), _prep(test, name)
        reg.fit(X_tr, y_tr)
        clf.fit(X_tr, l_tr)
        pred = reg.predict(X_te)
        prob = clf.predict_proba(X_te)[:, 1]
        rows.append({
            "model": name,
            "MAE_days": mean_absolute_error(y_te, pred),
            "RMSE_days": root_mean_squared_error(y_te, pred),
            "AUC_late": _auc(l_te, prob),
            "F1_late": f1_score(l_te, (prob >= 0.5).astype(int)),
        })
    return pd.DataFrame(rows).round(3)
