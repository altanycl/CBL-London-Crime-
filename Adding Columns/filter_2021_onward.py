import pandas as pd

# Paths – adjust as needed
input_csv  = r"C:\Users\borka\Downloads\London_burglaries_with_wards_correct.csv"
output_csv = r"C:\Users\borka\Downloads\London_burglaries_after2021.csv"

# Load, parsing the Month column as datetime at month resolution
df = pd.read_csv(input_csv)
df['Month'] = pd.to_datetime(df['Month'], format='%Y-%m')

# Filter: keep only dates strictly after 2021-12 (i.e. 2022-01-01 onward)
filtered = df[df['Month'] >= pd.Timestamp('2021-01-01')]

# (Optionally) drop the Month datetime if you want to revert to 'YYYY-MM' strings:
# filtered['Month'] = filtered['Month'].dt.strftime('%Y-%m')

# Save to CSV
filtered.to_csv(output_csv, index=False)
print(f"[DONE] Filtered data saved to: {output_csv}")
