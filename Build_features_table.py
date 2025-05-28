#!/usr/bin/env python3
"""
build_lsoa_features.py

Reads raw crime CSV, aggregates to LSOA × month (filling zeros),
builds lagged & extra features, drops the first month (2010-12),
normalizes inputs per-month, computes a clean month feature,
and writes out a feature table for downstream GCN modeling.
"""

import pandas as pd
import numpy as np


def main():
    INPUT_CSV  = "London_burglaries_with_wards_correct_with_price.csv"
    OUTPUT_CSV = "lsoa_features.csv"

    # 1) Load and parse
    df = pd.read_csv(INPUT_CSV, parse_dates=["Month_dt", "Month"])
    df["month"] = df["Month_dt"].dt.to_period("M")

    # 2) Raw crime counts per LSOA×month
    crime_counts = (
        df.groupby(["LSOA code", "month"])
          .size()
          .rename("crime_count")
          .reset_index()
    )

    # 3) Fill zero-crime months for every LSOA × every month in span
    all_ls  = crime_counts["LSOA code"].unique()
    all_mon = pd.period_range(df["month"].min(),
                              df["month"].max(),
                              freq="M")
    full_idx = pd.MultiIndex.from_product(
        [all_ls, all_mon],
        names=["LSOA code", "month"]
    )
    crime_counts = (
        crime_counts
        .set_index(["LSOA code", "month"])
        .reindex(full_idx, fill_value=0)
        .reset_index()
    )

    # 4) Rename target and compute 1-month lag
    crime_counts = crime_counts.rename(columns={"crime_count": "y_true"})
    crime_counts["crime_count_lag1"] = (
        crime_counts
        .groupby("LSOA code")["y_true"]
        .shift(1)
        .fillna(0)
    )

    # 5) Pull in extras (no month_num here)
    extras = (
        df[[
            "LSOA code", "month",
            "num_crimes_past_year_1km",
            "MedianPrice", "HECTARES"
        ]]
        .drop_duplicates(subset=["LSOA code", "month"])
    )
    features = pd.merge(
        crime_counts, extras,
        on=["LSOA code", "month"],
        how="left"
    )

    # 6) Coerce extras to numeric and fill missing
    for c in ["num_crimes_past_year_1km", "MedianPrice", "HECTARES"]:
        features[c] = pd.to_numeric(features[c], errors="coerce")
    features["num_crimes_past_year_1km"].fillna(0, inplace=True)
    features["MedianPrice"].fillna(features["MedianPrice"].median(), inplace=True)
    features["HECTARES"].fillna(features["HECTARES"].median(), inplace=True)

    # 7) Drop the first month (2010-12) for every LSOA
    first_mon = df["month"].min()  # e.g. 2010-12
    features = features[features["month"] != first_mon].reset_index(drop=True)

    # 8) Per-month z-scoring of dynamic features across LSOAs
    dyn_feats = [
        "crime_count_lag1",
        "num_crimes_past_year_1km",
        "MedianPrice"
    ]
    for col in dyn_feats:
        features[col] = features.groupby("month")[col] \
                                .transform(lambda x: (x - x.mean()) / x.std(ddof=0))

    # 9) Global z-score of static feature HECTARES
    mu, sigma = features["HECTARES"].mean(), features["HECTARES"].std(ddof=0)
    features["HECTARES"] = (features["HECTARES"] - mu) / sigma

    # 10) Compute a clean month number and (optionally) cyclical encoding
    features["month_num"] = features["month"].dt.month
    features["month_sin"] = np.sin(2 * np.pi * features["month_num"] / 12)
    features["month_cos"] = np.cos(2 * np.pi * features["month_num"] / 12)

    # 11) Reorder & save
    out_cols = [
        "LSOA code", "month",
        "y_true",
        "crime_count_lag1",
        "num_crimes_past_year_1km",
        "MedianPrice",
        "HECTARES",
        "month_sin", "month_cos"
    ]
    features[out_cols].to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Saved to {OUTPUT_CSV} ({features.shape[0]} rows).")


if __name__ == "__main__":
    main()
