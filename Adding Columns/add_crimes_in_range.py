import os
import pandas as pd
from pandas.tseries.offsets import DateOffset
from math import radians, sin, cos, sqrt, asin

# Haversine: great-circle distance (km) between two (lat, lon) points
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))

# === CONFIG ===
INPUT_PATH  = r"C:\Users\borka\Downloads\all_burglaries_london (2)_cleaned.csv"
BASE, EXT   = os.path.splitext(INPUT_PATH)
OUTPUT_PATH = BASE + "_num_crimes_past_year_1km" + EXT


# --- Phase 1: Load Cleaned CSV ---
df = pd.read_csv(INPUT_PATH, low_memory=False)
print(f"[1] Loaded {len(df):,} cleaned rows")

# --- Phase 2: Use pre-parsed dt and coords ---
df_valid = df.copy()
n = len(df_valid)
print(f"[2] Proceeding with {n:,} rows")

# Extract arrays
lats = df_valid['latitude'].to_numpy()
lons = df_valid['longitude'].to_numpy()
dts  = pd.to_datetime(df_valid['dt']).to_numpy()

# --- Phase 3: Sliding-window count (past 12 months, within 1 km) ---
R_km     = 1.0
cell_deg = R_km / 111.32    # approx degrees per km

def cell_coord(i):
    return (int(lons[i] // cell_deg),
            int(lats[i] // cell_deg))

buckets = {}
counts  = [0] * n
start   = 0

print("[3] Counting neighbors in the previous 12 months for each point…")
for i in range(n):
    cutoff = dts[i] - DateOffset(months=12)
    while start < i and dts[start] < cutoff:
        ck = cell_coord(start)
        buckets[ck].remove(start)
        if not buckets[ck]:
            del buckets[ck]
        start += 1

    cx, cy = cell_coord(i)
    cnt = 0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for j in buckets.get((cx+dx, cy+dy), []):
                if haversine(lats[i], lons[i], lats[j], lons[j]) <= R_km:
                    cnt += 1
    counts[i] = cnt

    buckets.setdefault((cx, cy), []).append(i)

    if i and i % 50000 == 0:
        print(f"  processed {i:,} / {n:,}")

print(f"[3] Sample counts: {counts[:5]}")

# --- Phase 4: Save results ---
col_name = 'num_crimes_past_year_1km'
df[col_name] = counts
print(f"[4] Non-zero counts: {(df[col_name] > 0).sum():,}")

df.to_csv(OUTPUT_PATH, index=False)
print(f"[5] Wrote output to: {OUTPUT_PATH}")
