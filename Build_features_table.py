#!/usr/bin/env python3
"""
build_lsoa_features.py

Reads raw crime CSV, aggregates to LSOA × month (filling zeros),
builds lagged & extra features, drops the first month (2010-12),
normalizes inputs per-month (safely), computes a clean month feature,
filters out any LSOAs that intersect the Greater London bounding box,
adds two new features (rank by past-year crime and months since last crime),
and writes out a feature table for downstream GCN modeling.
Imputes missing extras from previous month per LSOA, or 0 if none.
"""

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import box


def main():
    INPUT_CSV = "London_burglaries_with_wards_correct_with_price.csv"
    OUTPUT_CSV = "lsoa_features_final.csv"
    SHP_PATH   = "LSOA_boundries/LSOA_2021_EW_BFE_V10.shp"
    N195_PATH = "N195.csv"
    POP_PATH = "Popdense.xlsx" 

    # 1) Load and parse CSV robustly
    df = pd.read_csv(
        INPUT_CSV,
        parse_dates=["Month_dt", "Month"],
        dtype={"LSOA code": str},
        na_values={"MedianPrice": [":", "", "NA", "N/A"]},
        low_memory=False
    )
    df['month'] = df['Month_dt'].dt.to_period('M')

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

    # 10) Attach IMD Decile and Rank London 
    imd = (
        pd.read_csv(
            N195_PATH,
            engine="python",        # tolerant parser
            on_bad_lines="skip",    # drop footer rows with too many commas
            dtype=str               # keep raw strings for now
        )
        .rename(columns=lambda c: c.strip())  # trim stray spaces in headers
    )

    # keep the two columns we want and one row per LSOA
    imd = imd[['LSOA code', 'IMD Rank London', 'IMD Decile London']].drop_duplicates('LSOA code')

    # make the two metrics numeric; blanks → 0
    for col in ['IMD Rank London', 'IMD Decile London']:
        imd[col] = pd.to_numeric(imd[col], errors='coerce').fillna(0)

    # merge into the main feature table
    features = features.merge(imd, on='LSOA code', how='left')

    # 11) Attach annual population metrics
    # 1) read the sheet (first sheet assumed)
    pop = (
        pd.read_excel(POP_PATH, dtype={'LSOA 2021 Code': str})
        .rename(columns=lambda c: c.strip())          # trim header spaces
        .dropna(subset=['LSOA 2021 Code'])            # guard against blank rows
    )

    # 2) identify the yearly columns
    pop_cols  = [c for c in pop.columns if c.endswith("Pop")]
    dens_cols = [c for c in pop.columns if c.endswith("PpSqKm")]

    # 3) reshape to long format  →  one row per (LSOA, year)
    pop_long = (
        pop.melt(
            id_vars=['LSOA 2021 Code'], value_vars=pop_cols,
            var_name='year_col', value_name='Population'
        )
    )
    pop_long['year'] = pop_long['year_col'].str.extract(r'(\d{4})').astype(int)
    pop_long = pop_long.drop(columns='year_col')

    dens_long = (
        pop.melt(
            id_vars=['LSOA 2021 Code'], value_vars=dens_cols,
            var_name='year_col', value_name='PopulationPerSqKm'
        )
    )
    dens_long['year'] = dens_long['year_col'].str.extract(r'(\d{4})').astype(int)
    dens_long = dens_long.drop(columns='year_col')

    # 4) merge the two metrics side-by-side
    pop_full = (
        pop_long.merge(dens_long, on=['LSOA 2021 Code', 'year'], how='inner')
                .rename(columns={'LSOA 2021 Code': 'LSOA code'})
    )

    # 5) bring year into the crime-feature table
    features['year'] = features['month'].dt.year

    # 6) merge annual population onto every month row
    features = features.merge(
        pop_full, on=['LSOA code', 'year'], how='left'
    )

    # 7) carry 2022 values forward to 2023-2025 (and back-fill if needed)
    features = features.sort_values(['LSOA code', 'year'])
    for col in ['Population', 'PopulationPerSqKm']:
        features[col] = (
            features.groupby('LSOA code')[col]
                    .ffill()            # forward-fill to future years
                    .bfill()            # (unlikely) back-fill if 2011 missing
                    .astype(float)
        )
    areas = (
        pop[['LSOA 2021 Code', 'AreaSqKm']]
        .rename(columns={'LSOA 2021 Code': 'LSOA code',
                        'AreaSqKm': 'AreaSqKm'})
        .drop_duplicates('LSOA code')
    )
    features = features.merge(areas, on='LSOA code', how='left') 

    # 8) clean-up helper column
    features = features.drop(columns='year')

    # 12) Normalize dynamic features per month safely (avoid division by zero)
    dyn_feats = [
        'crime_count_lag1', 'crime_count_lag3', 'crime_count_lag12',
        'num_crimes_past_year_1km', 'MedianPrice'
    ]
    for col in dyn_feats:
        group = features.groupby('month')[col]
        mu = group.transform('mean')
        sigma = group.transform(lambda x: x.std(ddof=0)).replace(0, 1)
        features[col] = (features[col] - mu) / sigma

    # 13) Cyclical month encoding
    features['month_num'] = features['month'].dt.month
    features['month_sin'] = np.sin(2 * np.pi * features['month_num'] / 12)
    features['month_cos'] = np.cos(2 * np.pi * features['month_num'] / 12)

    # 14) Filter LSOAs by intersecting the Greater London bbox
    # 14a) load full UK LSOA shapefile in British National Grid
    gdf = gpd.read_file(SHP_PATH).to_crs(epsg=27700)
    # 14b) define Greater London bounding box in WGS84
    min_lon, min_lat, max_lon, max_lat = -0.5103, 51.2868, 0.3340, 51.6919
    london_box = (
        gpd.GeoSeries([box(min_lon, min_lat, max_lon, max_lat)], crs="EPSG:4326")
           .to_crs(epsg=27700)
           .iloc[0]
    )
    # 14c) pick only LSOAs whose geometry intersects the London box
    london_lsoas = gdf[gdf.geometry.intersects(london_box)]
    valid_codes = set(london_lsoas['LSOA21CD'])
    before = len(features)
    features = features[features['LSOA code'].isin(valid_codes)].reset_index(drop=True)
    after = len(features)
    print(f"Filtered out {before-after} rows outside Greater London bbox")

    # ──────────────────────────────────────────────────────────────────
    # 15) ADDITIONAL FEATURES: 12-month ranking + months-since-last-crime (capped + z-scored)
    # ──────────────────────────────────────────────────────────────────

    # (a) Ensure sorted by LSOA & month
    features = features.sort_values(['LSOA code', 'month'])

    # (b) Compute “crimes in last 12 months” per LSOA (rolling sum of y_true)
    features['crimes_last_12m'] = (
        features
        .groupby('LSOA code')['y_true']
        .rolling(window=12, min_periods=1)
        .sum()
        .reset_index(level=0, drop=True)
    )

    # (c) Rank LSOAs, within each month, by crimes_last_12m (highest = rank 1)
    features['rank_last_year'] = (
        features
        .groupby('month')['crimes_last_12m']
        .rank(method='dense', ascending=False)
        .astype(int)
    )

    # (d) Compute “months since last crime” for each LSOA
    #     1) mark the month whenever y_true > 0, then ffill to carry forward last crime month
    features['last_crime_month'] = features['month'].where(features['y_true'] > 0)
    features['last_crime_month'] = (
        features
        .groupby('LSOA code')['last_crime_month']
        .ffill()
    )
    #     2) subtract current month – last_crime_month; convert to integer number of months
    delta = features['month'] - features['last_crime_month']
    features['months_since_last_crime'] = (
        delta.map(lambda x: x.n if pd.notnull(x) else np.nan)
             .astype('Int64')
    )

    # (e) Cap “months_since_last_crime” at 12 and fill any NaN with 12
    features['months_since_last_crime'] = (
        features['months_since_last_crime']
        .fillna(12)        # if no previous crime ever, set to 12
        .clip(upper=12)    # if >12, cap at 12
    )

    # (f) Convert “months_since_last_crime” to z-score (global)
    ms_mean = features['months_since_last_crime'].mean()
    ms_std  = features['months_since_last_crime'].std(ddof=0)
    if ms_std == 0:
        ms_std = 1
    features['months_since_last_crime'] = (
        (features['months_since_last_crime'] - ms_mean) / ms_std
    )

    # 16) Reorder & save (including the two new columns)
    out_cols = [
        'LSOA code', 'month', 'y_true',
        'crime_count_lag1', 'crime_count_lag3', 'crime_count_lag12',
        'num_crimes_past_year_1km', 'MedianPrice',
        'month_sin', 'month_cos',
        'rank_last_year', 'months_since_last_crime',
        'IMD Decile London', 'IMD Rank London',
        'AreaSqKm', 'Population', 'PopulationPerSqKm', 
    ]
    features[out_cols].to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Saved to {OUTPUT_CSV} ({features.shape[0]} rows)")


if __name__ == '__main__':
    main()
