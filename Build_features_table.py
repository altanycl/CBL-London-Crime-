#!/usr/bin/env python3
"""
build_lsoa_features.py

Reads raw crime CSV, aggregates to LSOA × month (filling zeros),
builds lagged & extra features, drops the first month (2010-12),
normalizes inputs per-month (safely), computes a clean month feature,
filters out any LSOAs that intersect the Greater London bounding box,
adds features including rolling stats, changes, spatial context and
ranks, then writes out a feature table for downstream GCN modeling.
Imputes missing extras from previous month per LSOA, or 0 if none.
Also saves ward code and ward name (WD24CD, WD24NM) as raw features.
Derived metrics added:
  - 6-month rolling mean/std of y_true
  - Month-over-month percent change
  - Year-over-year change
  - Ward-level average lagged by one month and deviation
"""

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import box


def main():
    INPUT_CSV = "London_burglaries_with_wards_correct_with_price.csv"
    Z_OUTPUT = "lsoa_features.csv"
    RAW_OUTPUT = "non_Z_score_feature_table.csv"
    COMBINED_OUTPUT = "combined_features.csv"
    SHP_PATH   = "LSOA_boundries/LSOA_2021_EW_BFE_V10.shp"

    # 1) Load and parse CSV robustly
    df = pd.read_csv(
        INPUT_CSV,
        parse_dates=["Month_dt", "Month"],
        dtype={"LSOA code": str},
        na_values={"MedianPrice": [":", "", "NA", "N/A"]},
        low_memory=False
    )
    df['month'] = df['Month_dt'].dt.to_period('M')

    # Extract ward code & name per LSOA (static)
    ward_info = (
        df[['LSOA code', 'WD24CD', 'WD24NM']]
          .drop_duplicates(subset=['LSOA code'])
    )

    # 2) Crime counts per LSOA × month
    crime_counts = (
        df.groupby(['LSOA code', 'month'])
          .size()
          .rename('crime_count')
          .reset_index()
    )

    # 3) Ensure every LSOA × month combination
    all_ls = crime_counts['LSOA code'].unique()
    all_months = pd.period_range(df['month'].min(), df['month'].max(), freq='M')
    full_idx = pd.MultiIndex.from_product([all_ls, all_months], names=['LSOA code', 'month'])
    crime_counts = (
        crime_counts.set_index(['LSOA code', 'month'])
                     .reindex(full_idx, fill_value=0)
                     .reset_index()
    )

    # 4) Rename & create 1-month lag
    crime_counts = crime_counts.rename(columns={'crime_count': 'y_true'})
    crime_counts['crime_count_lag1'] = (
        crime_counts.groupby('LSOA code')['y_true']
                    .shift(1)
                    .fillna(0)
    )

    # 5) Create additional lag features (3-month & 12-month)
    for lag in [3, 12]:
        crime_counts[f'crime_count_lag{lag}'] = (
            crime_counts.groupby('LSOA code')['y_true']
                        .shift(lag)
                        .fillna(0)
        )

    # 6) Extract extra features
    extras = (
        df[['LSOA code', 'month', 'num_crimes_past_year_1km', 'MedianPrice']]
          .drop_duplicates(subset=['LSOA code', 'month'])
    )
    features = pd.merge(crime_counts, extras, on=['LSOA code', 'month'], how='left')

    # 7) Coerce to numeric
    for col in ['num_crimes_past_year_1km', 'MedianPrice']:
        features[col] = pd.to_numeric(features[col], errors='coerce')

    # 8) Impute missing extras: ffill per LSOA then 0
    features = features.sort_values(['LSOA code', 'month'])
    for col in ['num_crimes_past_year_1km', 'MedianPrice']:
        features[col] = (
            features.groupby('LSOA code')[col]
                    .ffill()
                    .fillna(0)
        )

    # 9) Drop initial month of data
    first_month = df['month'].min()
    features = features[features['month'] != first_month].reset_index(drop=True)

    # 10) Cyclical month encoding
    features['month_num'] = features['month'].dt.month
    features['month_sin'] = np.sin(2 * np.pi * features['month_num'] / 12)
    features['month_cos'] = np.cos(2 * np.pi * features['month_num'] / 12)

    # 11) Filter LSOAs by intersecting the Greater London bbox
    gdf = gpd.read_file(SHP_PATH).to_crs(epsg=27700)
    min_lon, min_lat, max_lon, max_lat = -0.5103, 51.2868, 0.3340, 51.6919
    london_box = (
        gpd.GeoSeries([box(min_lon, min_lat, max_lon, max_lat)], crs="EPSG:4326")
           .to_crs(epsg=27700)
           .iloc[0]
    )
    london_lsoas = gdf[gdf.geometry.intersects(london_box)]
    valid_codes = set(london_lsoas['LSOA21CD'])
    features = features[features['LSOA code'].isin(valid_codes)].reset_index(drop=True)

    # 12) Additional temporal & ranking features
    features = features.sort_values(['LSOA code', 'month'])
    # 12a) 12-month rolling sum (for rank)
    features['crimes_last_12m'] = (
        features.groupby('LSOA code')['y_true']
                .rolling(window=12, min_periods=1)
                .sum().reset_index(level=0, drop=True)
    )
    features['rank_last_year'] = (
        features.groupby('month')['crimes_last_12m']
                .rank(method='dense', ascending=False).astype(int)
    )
    # 12b) Months since last crime (RAW VALUE AT THIS POINT)
    features['last_crime_month'] = features['month'].where(features['y_true'] > 0)
    features['last_crime_month'] = (
        features.groupby('LSOA code')['last_crime_month'].ffill()
    )
    delta = features['month'] - features['last_crime_month']
    features['months_since_last_crime'] = (
        delta.map(lambda x: x.n if pd.notnull(x) else np.nan)
             .astype('Int64')
             .fillna(12).clip(upper=12)
    )
    # NOTE: 'months_since_last_crime' is RAW at this point. Z-scoring happens later.

    # Merge static ward info
    features = features.merge(ward_info, on='LSOA code', how='left')

    # 13) Derived rolling & change metrics
    # 13a) 6-month rolling mean & std of y_true
    features['roll_mean_6m'] = (
        features.groupby('LSOA code')['y_true']
                .rolling(window=6, min_periods=1)
                .mean().reset_index(level=0, drop=True)
    )
    features['roll_std_6m'] = (
        features.groupby('LSOA code')['y_true']
                .rolling(window=6, min_periods=1)
                .std(ddof=0).reset_index(level=0, drop=True).fillna(0)
    )
    # 13b) Month-over-month percent change
    features['pct_change_1m'] = (
        features.groupby('LSOA code')['y_true']
                .pct_change(1).fillna(0)
    )
    # 13c) Year-over-year change
    features['yoy_change'] = features['y_true'] - features['crime_count_lag12']

    # 13d) Ward-level mean of last month & deviation
    ward_month = (
        features.groupby(['WD24CD','month'])['y_true']
                .mean().rename('ward_mean').reset_index()
    )
    ward_month['ward_mean_lag1'] = (
        ward_month.groupby('WD24CD')['ward_mean'].shift(1).fillna(0)
    )
    features = features.merge(
        ward_month[['WD24CD','month','ward_mean_lag1']],
        on=['WD24CD','month'], how='left'
    )
    features['diff_from_ward_last_month'] = (
        features['y_true'] - features['ward_mean_lag1']
    )

    # --- Prepare outputs from the fully-featured RAW DataFrame ---
    # At this point, 'features' contains all raw (non-z-scored) features
    raw_features_df = features.copy()
    lsoa_features_df = features.copy()
    combined_features_df = features.copy()

    # Define dynamic features for z-scoring
    dyn_feats = [
        'crime_count_lag1', 'crime_count_lag3', 'crime_count_lag12',
        'num_crimes_past_year_1km', 'MedianPrice'
    ]

    # Z-score 'lsoa_features_df' in place
    for col in dyn_feats:
        group = lsoa_features_df.groupby('month')[col]
        mu = group.transform('mean')
        sigma = group.transform(lambda x: x.std(ddof=0)).replace(0, 1)
        lsoa_features_df[col] = (lsoa_features_df[col] - mu) / sigma

    # Z-score 'months_since_last_crime' in place for lsoa_features_df
    ms_mean_lsoa = lsoa_features_df['months_since_last_crime'].mean()
    ms_std_lsoa = lsoa_features_df['months_since_last_crime'].std(ddof=0) or 1
    lsoa_features_df['months_since_last_crime'] = (
        (lsoa_features_df['months_since_last_crime'] - ms_mean_lsoa) / ms_std_lsoa
    )

    # Add _z columns to 'combined_features_df' (using its raw values for calculation)
    for col in dyn_feats:
        group = combined_features_df.groupby('month')[col]
        mu = group.transform('mean')
        sigma = group.transform(lambda x: x.std(ddof=0)).replace(0, 1)
        combined_features_df[col + '_z'] = (combined_features_df[col] - mu) / sigma

    # Add 'months_since_last_crime_z' to 'combined_features_df'
    ms_mean_combined = combined_features_df['months_since_last_crime'].mean()
    ms_std_combined = combined_features_df['months_since_last_crime'].std(ddof=0) or 1
    combined_features_df['months_since_last_crime_z'] = (
        (combined_features_df['months_since_last_crime'] - ms_mean_combined) / ms_std_combined
    )

    # Define base output columns
    base_cols = [
        'LSOA code','WD24CD','WD24NM','month','y_true',
        'crime_count_lag1','crime_count_lag3','crime_count_lag12',
        'num_crimes_past_year_1km','MedianPrice',
        'month_sin','month_cos',
        'rank_last_year','months_since_last_crime',
        'roll_mean_6m','roll_std_6m','pct_change_1m','yoy_change',
        'ward_mean_lag1','diff_from_ward_last_month'
    ]

    # Save raw features
    raw_features_df[base_cols].to_csv(RAW_OUTPUT, index=False)
    print(f"✅ Saved raw features to {RAW_OUTPUT} ({raw_features_df.shape[0]} rows)")

    # Save z-scored features
    lsoa_features_df[base_cols].to_csv(Z_OUTPUT, index=False)
    print(f"✅ Saved z-scored features to {Z_OUTPUT} ({lsoa_features_df.shape[0]} rows)")

    # Save combined features
    combined_out_cols = base_cols.copy()
    combined_out_cols.extend([col + '_z' for col in dyn_feats])
    combined_out_cols.append('months_since_last_crime_z')

    combined_features_df[combined_out_cols].to_csv(COMBINED_OUTPUT, index=False)
    print(f"✅ Saved combined features to {COMBINED_OUTPUT} ({combined_features_df.shape[0]} rows)")


if __name__ == '__main__':
    main()