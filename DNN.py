import pandas as pd
import numpy as np

# === Step 1: Load only needed columns === #
columns_needed = ['Month', 'WD24CD', 'HECTARES', 'NONLD_AREA']
df = pd.read_csv('London_burglaries_with_wards_correct.csv', usecols=columns_needed, parse_dates=['Month'])

# === Step 2: Aggregate burglaries per ward-month === #
df_grouped = df.groupby(['Month', 'WD24CD'], as_index=False).agg({
    'HECTARES': 'first',
    'NONLD_AREA': 'first'
})

# Add burglary count by counting rows in each group
df_grouped['burglaries'] = df.groupby(['Month', 'WD24CD']).size().values


# Add time-based features
df_grouped['year'] = df_grouped['Month'].dt.year
df_grouped['month'] = df_grouped['Month'].dt.month

# Cyclical encoding for seasonality
df_grouped['month_sin'] = np.sin(2 * np.pi * df_grouped['month'] / 12)
df_grouped['month_cos'] = np.cos(2 * np.pi * df_grouped['month'] / 12)

#  Add lag and rolling features
df_grouped = df_grouped.sort_values(by=['WD24CD', 'Month'])

# Add lag features
for lag in [1, 2, 3]:
    df_grouped[f'lag_{lag}'] = df_grouped.groupby('WD24CD')['burglaries'].shift(lag)

# Rolling average of past 3 months
df_grouped['rolling_mean_3'] = df_grouped.groupby('WD24CD')['burglaries'] \
    .transform(lambda x: x.shift(1).rolling(window=3, min_periods=1).mean())

# Drop rows with missing lag values
df_features = df_grouped.dropna().reset_index(drop=True)

# Save result
df_features.to_csv('ward_month_features.csv', index=False)


print(df_features.head())
