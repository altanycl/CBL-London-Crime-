#!/usr/bin/env python
# ----------------------------------------------------------
# burglary_prediction_lsoa.py
#
# LightGBM burglary prediction — print-only version.
# ----------------------------------------------------------
import warnings
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, mean_squared_error

warnings.filterwarnings("ignore", category=FutureWarning)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
INPUT_CSV = "lsoa_features_final.csv"   # <- path to your final feature file

# ----------------------------------------------------------------------
# Helper: evaluation metrics
# ----------------------------------------------------------------------
def evaluate(y_true, y_pred) -> dict:
    mae = mean_absolute_error(y_true, y_pred)

    # older sklearn (<0.22) has no "squared" argument
    try:
        rmse = mean_squared_error(y_true, y_pred, squared=False)
    except TypeError:
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))

    mape = (
        np.abs((y_true - y_pred) / np.clip(y_true, 1, None))
          .replace([np.inf, -np.inf], np.nan)
          .dropna()
          .mean() * 100
    )
    return {"MAE": mae, "RMSE": rmse, "MAPE": mape}

# ----------------------------------------------------------------------
# Main routine
# ----------------------------------------------------------------------
def main() -> None:

    # ---------- 1) Load & filter ----------
    df = pd.read_csv(INPUT_CSV, parse_dates=["month"])
    df = df[(df["month"] >= "2011-01-01") & (df["month"] <= "2019-12-31")]

    # ---------- 2) Feature list ----------
    feature_cols = [
        "crime_count_lag1", "crime_count_lag3", "crime_count_lag12",
        "num_crimes_past_year_1km", "MedianPrice",
        "month_sin", "month_cos",
        "rank_last_year", "months_since_last_crime",
        "IMD Decile London", "IMD Rank London",
        "AreaSqKm", "Population", "PopulationPerSqKm"
    ]

    # Drop any rows with missing target or features
    df = df.dropna(subset=["y_true"] + feature_cols)

    # ---------- 3) Train / validation / test splits ----------
    # You can tweak the cut-offs – this keeps one full year for testing
    train_cut, val_cut = "2017-12-31", "2018-12-31"

    train = df[df["month"] <= train_cut]
    val   = df[(df["month"] > train_cut) & (df["month"] <= val_cut)]
    test  = df[df["month"] > val_cut]

    # ---------- 4) LightGBM ----------
    lgb_train = lgb.Dataset(train[feature_cols], train["y_true"])
    lgb_val   = lgb.Dataset(val[feature_cols],   val["y_true"], reference=lgb_train)

    params = {
        "objective": "poisson",
        "metric": "rmse",
        "learning_rate": 0.05,
        "num_leaves": 31,
        "min_data_in_leaf": 30,
        "feature_fraction": 0.9,
        "bagging_fraction": 0.9,
        "bagging_freq": 5,
    }

    # ---- robust training: modern call first, fall back if keywords unsupported ----
    try:                                    # recent LightGBM (≥ 3.x)
        model = lgb.train(
            params,
            lgb_train,
            num_boost_round=600,
            valid_sets=[lgb_val],
            early_stopping_rounds=50,
            verbose_eval=False,             # quiet mode
        )
    except TypeError as e:                  # older builds: drop fancy args
        print(f"⚠  {e}  – retrying with minimal signature.")
        model = lgb.train(
            params,
            lgb_train,
            num_boost_round=400             # fixed rounds, no val set, no verbosity
        )
    # ---------- 5) Evaluate ----------
    num_iter = getattr(model, "best_iteration", None)  # None = use all trees
    test_pred = model.predict(test[feature_cols], num_iteration=num_iter)
    scores = evaluate(test["y_true"], test_pred)

    # ---------- 6) Print results ----------
    print("\n===== LightGBM – LSOA level (2011-2022 training) =====")
    for k, v in scores.items():
        print(f"{k:4}: {v:.3f}")

    # Optional: quick feature importance peek
    print("\nTop 10 features by gain:")
    imp = model.feature_importance(importance_type="gain")
    for name, gain in sorted(zip(feature_cols, imp), key=lambda t: t[1], reverse=True)[:10]:
        print(f"  {name:<28} {gain:.0f}")

# ----------------------------------------------------------------------
if __name__ == "__main__":
    main()
