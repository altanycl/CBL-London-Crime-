import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

# === Load and aggregate === #
columns_needed = ['Month', 'WD24CD']
df = pd.read_csv('London_burglaries_with_wards_correct.csv', usecols=columns_needed, parse_dates=['Month'])

# Add 1 count per burglary record
df['count'] = 1

# Group by ward and month
df_grouped = df.groupby(['WD24CD', 'Month'], as_index=False)['count'].count()
df_grouped = df_grouped.rename(columns={'count': 'burglaries'})

# Sort
df_grouped = df_grouped.sort_values(by=['WD24CD', 'Month'])

# === Choose one ward to model first === #
ward_id = df_grouped['WD24CD'].unique()[0]  # First ward for demo
ward_df = df_grouped[df_grouped['WD24CD'] == ward_id].copy()

# Drop ID (not needed now)
ward_df = ward_df[['Month', 'burglaries']].reset_index(drop=True)

# Normalize burglaries (for LSTM stability)
scaler = MinMaxScaler()
ward_df['scaled_burglaries'] = scaler.fit_transform(ward_df[['burglaries']])

# === Create sequences === #
def create_sequences(data, window):
    X, y = [], []
    for i in range(len(data) - window):
        X.append(data[i:i+window])
        y.append(data[i+window])
    return np.array(X), np.array(y)

window_size = 6  # Use past 6 months to predict next
X, y = create_sequences(ward_df['scaled_burglaries'].values, window_size)

# Reshape for LSTM: (samples, time_steps, features)
X = X.reshape((X.shape[0], X.shape[1], 1))
y = y.reshape((-1, 1))

print(f"X shape: {X.shape}, y shape: {y.shape}")
