#!/usr/bin/env python3
"""
visualize_gcn_predictions.py (Raw‐MSE Focused)

1) Loads GCN-derived embeddings + y_true from CSV.
2) Splits into train/validation/test (last two months).
3) Baseline: constant-mean predictor MSE on raw counts.
4) Fits a PoissonRegressor on embeddings → raw counts.
5) Predicts on held-out test month.
6) Prints raw‐MSE, MAE, R², and also log(1+y)‐MSE for comparison.
7) Computes per‐LSOA performance (MAD, MAPE, MSE) for three specified LSOAs.
8) Saves:
   - gcn_true_vs_pred_scatter.png      (raw counts)
   - gcn_true_vs_pred_scatter_log.png  (log(1+y))
   - gcn_pred_and_resid_map.png        (absolute residual map)
Suppresses joblib core-count warning via env var.
"""
import os
os.environ["LOKY_MAX_CPU_COUNT"] = "1"  # suppress joblib warning

import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)


def main():
    # 1) Load embeddings + y_true
    feats = pd.read_csv("lsoa_gcn_hidden_layer2.csv")
    feats["month"] = pd.to_datetime(feats["month"]).dt.to_period("M")
    emb_cols = [c for c in feats.columns if c.startswith("gcn2_emb_")]

    # 2) Split train/val/test
    months = sorted(feats["month"].unique())
    train = feats[feats["month"] < months[-2]]
    val   = feats[feats["month"] == months[-2]]
    test  = feats[feats["month"] == months[-1]]

    X_train, y_train = train[emb_cols], train["y_true"]
    X_val,   y_val   = val[emb_cols],   val["y_true"]
    X_test,  y_test  = test[emb_cols],  test["y_true"]

    # 2a) How many zeros in the test month?
    zeros = (y_test == 0).sum()
    print(f"Held-out test month {months[-1]}: {zeros} areas with zero true crimes.")

    # 3) Baseline: constant-mean predictor from TRAIN
    baseline_pred = np.full_like(y_test.values, y_train.mean())
    mse_baseline  = mean_squared_error(y_test, baseline_pred)
    print(f"Baseline (constant mean) MSE: {mse_baseline:.3f}")

    # 4) Train PoissonRegressor on (TRAIN + VAL) → raw counts
    pr = PoissonRegressor(alpha=1e-2, max_iter=500)
    pr.fit(
        pd.concat([X_train, X_val], ignore_index=True),
        pd.concat([y_train, y_val], ignore_index=True)
    )

    # 5) Predict on TEST month
    y_pred = pr.predict(X_test)

    # 6) Compute metrics on TEST (raw counts)
    mse_raw = mean_squared_error(y_test, y_pred)
    mae     = mean_absolute_error(y_test, y_pred)
    r2      = r2_score(y_test, y_pred)
    print(f"Test month {months[-1]} | Raw‐count MSE: {mse_raw:.3f}, MAE: {mae:.3f}, R²: {r2:.3f}")

    # 6a) Also compute log(1 + counts) MSE
    y_test_log = np.log1p(y_test)
    y_pred_log = np.log1p(np.clip(y_pred, a_min=0, a_max=None))
    mse_log    = mean_squared_error(y_test_log, y_pred_log)
    print(f"Test month {months[-1]} | log(1+y) MSE: {mse_log:.3f}")

    # 7) Compute per‐LSOA performance (MAD, MAPE, MSE) for three specific LSOAs
    #    First, assemble full summary for all LSOAs in the test set
    node_codes     = test["LSOA21CD"].tolist()
    y_true_series  = pd.Series(y_test.values, index=node_codes)
    y_pred_series  = pd.Series(y_pred,        index=node_codes)

    mad  = (y_true_series - y_pred_series).abs()
    mape = ((y_true_series - y_pred_series).abs() / y_true_series.replace(0, np.nan)) * 100
    mse  = (y_true_series - y_pred_series) ** 2

    summary_df = pd.DataFrame({
        "lsoa": node_codes,
        "MAD":  mad.values.round(4),
        "MAPE": mape.values.round(3),
        "MSE":  mse.values.round(4)
    })

    # Now filter to just the three LSOAs of interest
    focus_lsos = ["E01004713", "E01000002", "E01001381"]
    subset_df  = summary_df[summary_df["lsoa"].isin(focus_lsos)]

    print("\nSelected LSOA Performance Stats:\n", subset_df.to_string(index=False))

    # 8) Scatter: raw counts
    plt.figure(figsize=(6, 6))
    plt.scatter(y_test, y_pred, alpha=0.4)
    mn, mx = min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())
    plt.plot([mn, mx], [mn, mx], 'k--')
    plt.xlabel("True crime count")
    plt.ylabel("Predicted crime count")
    plt.title(f"True vs Predicted (raw counts) ({months[-1]})")
    plt.tight_layout()
    plt.savefig("gcn_true_vs_pred_scatter.png", dpi=150)
    plt.close()

    # 8a) Scatter: log(1 + counts)
    plt.figure(figsize=(6, 6))
    plt.scatter(y_test_log, y_pred_log, alpha=0.4, color="tab:purple")
    mnl, mxl = min(y_test_log.min(), y_pred_log.min()), max(y_test_log.max(), y_pred_log.max())
    plt.plot([mnl, mxl], [mnl, mxl], 'k--')
    plt.xlabel("log(1 + true)")
    plt.ylabel("log(1 + predicted)")
    plt.title(f"True vs Predicted (log‐scale) ({months[-1]})")
    plt.tight_layout()
    plt.savefig("gcn_true_vs_pred_scatter_log.png", dpi=150)
    plt.close()

    # 9) GeoDataFrame + absolute‐error map (raw counts)
    shp = r"C:\Coding\CBL-London-Crime-\LSOA_boundries\LSOA_2021_EW_BFE_V10.shp"
    gdf = gpd.read_file(shp).to_crs(epsg=27700)
    gdf = (
        gdf[gdf["LSOA21CD"].isin(test["LSOA21CD"])]
           .set_index("LSOA21CD")
           .loc[test["LSOA21CD"]]
           .reset_index()
    )
    gdf["y_pred"]   = y_pred
    gdf["y_true"]   = y_test.values
    gdf["residual"] = gdf["y_pred"] - gdf["y_true"]

    # Drop outliers (96th percentile by centroid distance)
    center = gdf.geometry.unary_union.centroid
    dists  = gdf.geometry.centroid.distance(center)
    thresh = dists.quantile(0.96)
    removed = len(gdf) - (dists <= thresh).sum()
    gdf    = gdf[dists <= thresh].reset_index(drop=True)
    print(f"Removed {removed} outliers by distance filter")

    # 10) Plot predicted counts & absolute residual map
    minx, miny, maxx, maxy = gdf.total_bounds
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax = axes[0]
    gdf.plot(
        column="y_pred",
        cmap="viridis",
        linewidth=0.2,
        edgecolor="white",
        legend=True,
        ax=ax
    )
    ax.set_title(f"Predicted crime count ({months[-1]})")
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.axis("off")

    ax = axes[1]
    gdf.plot(
        column="residual",
        cmap="RdBu",
        linewidth=0.2,
        edgecolor="white",
        legend=True,
        ax=ax
    )
    ax.set_title("Absolute residuals (pred – true)")
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.axis("off")

    plt.tight_layout()
    plt.savefig("gcn_pred_and_resid_map.png", dpi=150)
    plt.close()
    print("Saved scatter → gcn_true_vs_pred_scatter.png, "
          "scatter_log → gcn_true_vs_pred_scatter_log.png, "
          "map → gcn_pred_and_resid_map.png")


if __name__ == "__main__":
    main()
