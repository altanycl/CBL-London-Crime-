#!/usr/bin/env python3
"""
update_cleaned_burglaries.py

A small post-processing script to tweak an existing cleaned London burglaries CSV.

It will:
 1. Rename a "month_num" column back to "month" (if present).
 2. Re-add the dropped "context" column at the end (as empty strings), so you retain the original structure.

Usage:
    python update_cleaned_burglaries.py [input_cleaned.csv] [output_updated.csv]

If no arguments are provided, defaults to:
    Input:  C:/Users/borka/Downloads/cleaned_burglaries_london.csv
    Output: C:/Users/borka/Downloads/updated_burglaries_london.csv
"""
import sys
import pandas as pd

def update_cleaned(in_csv: str, out_csv: str):
    # Read the already-cleaned file
    df = pd.read_csv(in_csv)

    # 1. Rename month_num to month, if that column exists
    if 'month_num' in df.columns:
        df.rename(columns={'month_num': 'month'}, inplace=True)

    # 2. Ensure a 'context' column at the end
    if 'context' not in df.columns:
        df['context'] = ''

    # Move context to be the last column
    cols = [c for c in df.columns if c != 'context'] + ['context']
    df = df[cols]

    # Write updated file
    df.to_csv(out_csv, index=False)
    print(f"Wrote updated file to '{out_csv}' with 'month' renamed and 'context' re-added.")

if __name__ == '__main__':
    # Default file paths
    default_input  = r"C:/Users/borka/Downloads/cleaned_burglaries_london.csv"
    default_output = r"C:/Users/borka/Downloads/updated_burglaries_london.csv"

    if len(sys.argv) == 3:
        in_csv, out_csv = sys.argv[1], sys.argv[2]
    else:
        in_csv, out_csv = default_input, default_output
        print(f"No arguments provided; using defaults:\n  Input:  {in_csv}\n  Output: {out_csv}")

    update_cleaned(in_csv, out_csv)
