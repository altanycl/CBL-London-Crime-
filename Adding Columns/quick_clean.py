import pandas as pd
import os

# --- CONFIG ---
INPUT_PATH = r"C:\Users\borka\Downloads\all_burglaries_london (2).csv"
BASE, EXT = os.path.splitext(INPUT_PATH)
OUTPUT_PATH = BASE + "_cleaned" + EXT

# --- Load ---
df = pd.read_csv(INPUT_PATH, low_memory=False)
print(f"[1] Loaded {len(df):,} rows")

# --- Clean column names ---
df.columns = df.columns.str.strip()

# --- Filter only 'Burglary' crimes if needed ---
# If you're certain the file only contains burglary, this line can be removed
df = df[df['Crime type'].str.strip().str.lower() == 'burglary']
print(f"[2] Rows with Crime type = Burglary: {len(df):,}")

# --- Convert coordinates ---
df['longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
df['latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')

# Drop rows with invalid coords
df = df.dropna(subset=['longitude', 'latitude'])
print(f"[3] Geo-valid rows: {len(df):,}")

# --- Parse 'Month' to datetime ---
df['dt'] = pd.to_datetime(df['Month'] + '-01', errors='coerce')
df = df[df['dt'].notna()]
print(f"[4] Rows with valid dates: {len(df):,}")

# --- Optional: Drop unnecessary columns ---
#columns_to_keep = ['Crime ID', 'dt', 'longitude', 'latitude', 'Location', 'LSOA name', 'Last outcome category']
#df_clean = df[columns_to_keep].copy()

# --- Save cleaned file ---
df.to_csv(OUTPUT_PATH, index=False)
print(f"[5] Cleaned file written to: {OUTPUT_PATH}")
