import pandas as pd

# === CONFIG ===
INPUT_PATH = r"C:\Users\borka\Downloads\London_burglaries_with_wards.csv"
OUTPUT_PATH = r"C:\Users\borka\Downloads\London_burglaries_with_wards_2021_onward.csv"

# === LOAD CSV ===
df = pd.read_csv(INPUT_PATH)

# === PARSE AND FILTER ===
# Convert 'Month' to datetime format
df['Month'] = pd.to_datetime(df['Month'], format='%Y-%m', errors='coerce')

# Filter to include only rows from January 2021 onward
df_filtered = df[df['Month'] >= pd.Timestamp("2021-01")].copy()

# Format 'Month' back to YYYY-MM (string)
df_filtered['Month'] = df_filtered['Month'].dt.strftime('%Y-%m')

# === SAVE RESULT ===
df_filtered.to_csv(OUTPUT_PATH, index=False)
print(f"[DONE] Saved filtered data to: {OUTPUT_PATH}")
