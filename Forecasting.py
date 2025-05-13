# Forecasting_NextMonth.py

import argparse, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb

warnings.filterwarnings("ignore", category=FutureWarning)

def main(csv_path: str, outdir: str = "outputs"):
    outdir = Path(outdir)
    outdir.mkdir(exist_ok=True)

    # 1) Load
    raw = pd.read_csv(csv_path, low_memory=False)

    # 2) Parse date
    raw["Month"] = pd.to_datetime(raw["Month"], errors="coerce")
    raw = raw.dropna(subset=["Month"])

    # 3) Crime count: use the provided 'num_crimes_past_year_1km_full_period'
    raw.rename(columns={"num_crimes_past_year_1km_full_period": "y"}, inplace=True)

    # 4) Ward detection: use WD24NM (ward name)
    if "WD24NM" not in raw.columns:
        raise ValueError("Expected column WD24NM for ward names")
    raw.rename(columns={"WD24NM": "ward"}, inplace=True)

    # 5) Aggregate to monthly counts per ward
    df = (
        raw.groupby(["ward", "Month"], as_index=False)["y"]
           .count()      # count incidents per ward-month
           .rename(columns={"y": "y_count"})
    )

    # 6) Create full grid of (ward × each month in range)
    wards = df["ward"].unique()
    months = pd.date_range(df["Month"].min(), df["Month"].max(), freq="MS")
    grid = pd.MultiIndex.from_product([wards, months], names=["ward", "Month"])
    df = (
        df.set_index(["ward", "Month"])
          .reindex(grid, fill_value=0)
          .reset_index()
    )

    # 7) Build lag + roll + seasonal features
    df = df.sort_values(["ward", "Month"])
    df["lag1"] = df.groupby("ward")["y_count"].shift(1)
    df["lag3"] = df.groupby("ward")["y_count"].shift(3)
    df["lag12"] = df.groupby("ward")["y_count"].shift(12)
    df["roll3"] = (
        df.groupby("ward")["y_count"]
          .rolling(3, min_periods=1)
          .mean()
          .reset_index(0, drop=True)
    )
    df["month_sin"] = np.sin(2 * np.pi * df.Month.dt.month / 12)
    df["month_cos"] = np.cos(2 * np.pi * df.Month.dt.month / 12)

    # 8) Split into train / prediction‐input
    last_month   = df["Month"].max()
    next_month   = last_month + pd.DateOffset(months=1)
    train        = df[df["Month"] <= last_month].dropna()
    predict_df   = df[df["Month"] == last_month].copy()
    predict_df["Month"] = next_month  # label as next month

    feature_cols = ["lag1", "lag3", "lag12", "roll3", "month_sin", "month_cos"]
    X_train = train[feature_cols]
    y_train = train["y_count"]
    X_pred  = predict_df[feature_cols]

    # 9) Train LightGBM on all history
    lgb_train = lgb.Dataset(X_train, y_train)
    params = {
        "objective": "poisson",
        "metric":    "rmse",
        "learning_rate": 0.05,
        "num_leaves":    31,
        "min_data_in_leaf": 30,
        "feature_fraction": 0.9,
        "bagging_fraction": 0.9,
        "bagging_freq":    5,
    }
    model = lgb.train(params, lgb_train, num_boost_round=500)

    # 10) Predict next month for each wardd
    predict_df["prediction"] = model.predict(X_pred)

    # 11) Save results
    out_csv = outdir / "next_month_predictions.csv"
    predict_df[["ward", "Month", "prediction"]].to_csv(out_csv, index=False)
    print(f"✔ Next-month predictions saved to {out_csv}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--csv",
        default="crime_with_wards_num_crimes_past_year_1km_full_period.csv",
        help="path to your incident-level CSV"
    )
    ap.add_argument(
        "--outdir",
        default="outputs",
        help="where to write next_month_predictions.csv"
    )
    args = ap.parse_args()
    main(csv_path=args.csv, outdir=args.outdir)
