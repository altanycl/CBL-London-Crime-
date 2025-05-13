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
INPUT_PATH  = r"C:\Users\borka\Downloads\crime_with_wards.csv"
BASE, EXT   = os.path.splitext(INPUT_PATH)
OUTPUT_PATH = BASE + "_num_crimes_past_year_1km_full_period" + EXT

# --- Phase 1: Load CSV ---
df = pd.read_csv(INPUT_PATH, low_memory=False)
print(f"[1] Loaded {len(df):,} rows")

# --- Phase 2: Parse Month → dt; drop invalid dates (but keep all valid dates) ---
df['dt'] = pd.to_datetime(df['Month'] + '-01',
                          format='%Y-%m-%d',
                          errors='coerce')
df_time = df[df['dt'].notna()].copy()
print(f"[2] Rows with valid dt: {len(df_time):,}")

# --- Phase 3: Parse coords & filter valid geometry ---
df_time['longitude'] = pd.to_numeric(df_time['Longitude'], errors='coerce')
df_time['latitude']  = pd.to_numeric(df_time['Latitude'],  errors='coerce')
df_valid = df_time.dropna(subset=['longitude','latitude']).reset_index()
print(f"[3] Geo-valid rows: {len(df_valid):,}")

# keep original indices for later
valid_idx = df_valid['index'].to_numpy()

# --- Phase 4: Sort by time & extract arrays ---
df_valid = df_valid.sort_values('dt').reset_index(drop=True)
n = len(df_valid)
print(f"[4] Processing {n:,} sorted rows…")
lats = df_valid['latitude'].to_numpy()
lons = df_valid['longitude'].to_numpy()
dts  = df_valid['dt'].to_numpy()

# --- Phase 5: Sliding-window count (past 12 months, within 1 km) ---
R_km     = 1.0
cell_deg = R_km / 111.32    # approx degrees per km

def cell_coord(i):
    return (int(lons[i] // cell_deg),
            int(lats[i] // cell_deg))

buckets = {}
counts  = [0] * n
start   = 0

print("[5] Counting neighbors in the previous 12 months for each point…")
for i in range(n):
    cutoff = dts[i] - DateOffset(months=12)
    # expire points older than 12 months
    while start < i and dts[start] < cutoff:
        ck = cell_coord(start)
        buckets[ck].remove(start)
        if not buckets[ck]:
            del buckets[ck]
        start += 1

    # count neighbors within 1 km in neighboring cells
    cx, cy = cell_coord(i)
    cnt = 0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for j in buckets.get((cx+dx, cy+dy), []):
                if haversine(lats[i], lons[i], lats[j], lons[j]) <= R_km:
                    cnt += 1
    counts[i] = cnt

    # add current point
    buckets.setdefault((cx, cy), []).append(i)

    if i and i % 50000 == 0:
        print(f"  processed {i:,} / {n:,}")

print(f"[5] Sample counts: {counts[:5]}")

# --- Phase 6: Reattach counts & save ---
col_name = 'num_crimes_past_year_1km_full_period'
df[col_name] = 0
df.loc[valid_idx, col_name] = counts
print(f"[6] Non-zero counts: {(df[col_name] > 0).sum():,}")

df.to_csv(OUTPUT_PATH, index=False)
print(f"[7] Wrote output to: {OUTPUT_PATH}")
