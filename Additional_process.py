#!/usr/bin/env python3
"""
clean_burglaries.py

A script to clean and normalize a raw London burglary CSV dataset.

Usage:
    python clean_burglaries.py [input.csv] [output.csv]

If no arguments are provided, defaults to:
    Input:  C:/Users/borka/Downloads/all_burglaries_london.csv
    Output: C:/Users/borka/Downloads/cleaned_burglaries_london.csv

This version parses the 'month' string, splits into 'year' and 'month_num',
and drops any intermediate date column so only numeric year/month remain.
"""
import sys
import pandas as pd

def clean_burglaries(in_csv: str, out_csv: str):
    # --- 1. Read as str to catch misaligned rows ---
    df = pd.read_csv(in_csv, dtype=str, na_values=["", " "])

    # --- 2. Remove stray headers mid-file ---
    if "Month" in df.columns:
        df = df[df["Month"].str.lower() != "month"]

    # --- 3. Normalize column names & drop unnamed cols ---
    df = df.loc[:, ~df.columns.str.contains(r"^Unnamed")]
    df.columns = (
        df.columns
          .str.strip()
          .str.lower()
          .str.replace(" ", "_")
    )

    # --- 4. Parse and validate the 'month' field ---
    parsed = pd.to_datetime(df['month'], format='%Y-%m', errors='coerce')
    bad = df[parsed.isna()]
    if not bad.empty:
        print(f"Found {len(bad)} rows where 'month' wasn't YYYY-MM.")
        print(bad.head()[['month']])
    df = df[parsed.notna()].copy()

    # --- 4b. Split into year & month_num, drop original month ---
    df['year'] = parsed[parsed.notna()].dt.year
    df['month_num'] = parsed[parsed.notna()].dt.month
    df.drop(columns=['month'], inplace=True)

    # --- 5. Trim whitespace in all string columns ---
    obj_cols = df.select_dtypes(['object']).columns
    df[obj_cols] = df[obj_cols].apply(lambda col: col.str.strip())

    # --- 6. Coerce numeric fields ---
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df['latitude']  = pd.to_numeric(df['latitude'],  errors='coerce')

    # --- 7. Handle missing data ---
    df = df.dropna(subset=['longitude', 'latitude'], how='all')
    if 'last_outcome_category' in df:
        df.loc[:, 'last_outcome_category'] = df['last_outcome_category'].fillna('Unknown')
    if 'context' in df and df['context'].isna().all():
        df.drop(columns=['context'], inplace=True)

    # --- 8. Remove duplicates & filter to London bounds ---
    df.drop_duplicates(inplace=True)
    lon_min, lon_max = -0.51, 0.33
    lat_min, lat_max = 51.29, 51.69
    df = df[
        df['longitude'].between(lon_min, lon_max) &
        df['latitude'].between(lat_min, lat_max)
    ]

    # --- 9. Reorder columns: place 'year' and 'month_num' after 'crime_id' ---
    core = ['crime_id', 'year', 'month_num']
    others = [c for c in df.columns if c not in core]
    df = df[core + others]

    # --- 10. Output cleaned CSV ---
    df.to_csv(out_csv, index=False)
    print(f"Wrote {len(df)} rows to '{out_csv}'")

if __name__ == '__main__':
    default_input  = "C:/Users/borka/Downloads/all_burglaries_london.csv"
    default_output = "C:/Users/borka/Downloads/cleaned_burglaries_london.csv"

    if len(sys.argv) == 3:
        in_csv, out_csv = sys.argv[1], sys.argv[2]
    else:
        in_csv, out_csv = default_input, default_output
        print(f"No arguments provided; using default:\n  Input: {in_csv}\n  Output: {out_csv}")

    clean_burglaries(in_csv, out_csv)
