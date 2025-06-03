# LSTM Evaluation for 3 LSOAs from Screenshot-defined Areas
# ==========================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import warnings
warnings.filterwarnings('ignore')

plt.switch_backend('Agg')

class ImprovedLSTM:
    def __init__(self, sequence_length=10, lr=1e-3):
        self.sequence_length = sequence_length
        self.scaler = MinMaxScaler()
        self.learning_rate = lr
        self.model = None

    def create_sequences(self, data):
        X, y = [], []
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i+self.sequence_length, 0])
            y.append(data[i+self.sequence_length, 0])
        return np.array(X), np.array(y)

    def prepare(self, series, test_frac=0.2, val_frac=0.1):
        if len(series) < self.sequence_length + 5:
            raise ValueError("Not enough data to form sequences")
        scaled = self.scaler.fit_transform(series.reshape(-1, 1))
        X, y = self.create_sequences(scaled)
        n_total = len(X)
        n_test = int(n_total * test_frac)
        n_val = int(n_total * val_frac)
        n_train = n_total - n_test - n_val
        X_train, y_train = X[:n_train], y[:n_train]
        X_val, y_val = X[n_train:n_train + n_val], y[n_train:n_train + n_val]
        X_test, y_test = X[-n_test:], y[-n_test:]
        return (X_train.reshape(-1, self.sequence_length, 1), y_train), \
               (X_val.reshape(-1, self.sequence_length, 1), y_val), \
               (X_test.reshape(-1, self.sequence_length, 1), y_test)

    def build(self):
        model = Sequential([
            LSTM(64, return_sequences=True, input_shape=(self.sequence_length, 1)),
            Dropout(0.2), BatchNormalization(),
            LSTM(32),
            Dropout(0.2), BatchNormalization(),
            Dense(16, activation='relu'), Dropout(0.1),
            Dense(1)
        ])
        model.compile(optimizer=Adam(self.learning_rate), loss='mse', metrics=['mae'])
        return model

    def fit(self, train, val, epochs=50, batch_size=32):
        X_tr, y_tr = train
        X_val, y_val = val
        self.model = self.build()
        actual_batch = max(1, min(batch_size, X_tr.shape[0]))
        callbacks = [
            EarlyStopping(patience=10, restore_best_weights=True),
            ReduceLROnPlateau(factor=0.5, patience=5, min_lr=1e-6)
        ]
        history = self.model.fit(
            X_tr, y_tr,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=actual_batch,
            callbacks=callbacks,
            verbose=0
        )
        return history

if __name__ == '__main__':
    df = pd.read_csv('crime_with_wards_num_crimes_past_year_1km_full_period.csv', parse_dates=['Month'])
    df['count'] = 1
    grp = df.groupby(['LSOA code', 'Month'], as_index=False)['count'].count()
    grp.rename(columns={'count': 'burglaries'}, inplace=True)

    # First 3 LSOAs from the screenshot
    target_lsoas = ['E01004713', 'E01000002', 'E01001381']

    results = []
    for lsoa in target_lsoas:
        series = grp.loc[grp['LSOA code'] == lsoa, 'burglaries'].values
        print(f"\nLSOA {lsoa}: {len(series)} months")
        try:
            model = ImprovedLSTM(sequence_length=10)
            train, val, test = model.prepare(series)
            model.fit(train, val)

            X_test, y_test = test
            y_pred_scaled = model.model.predict(X_test)
            y_pred = model.scaler.inverse_transform(y_pred_scaled)
            y_true = model.scaler.inverse_transform(y_test.reshape(-1, 1))

            # Metrics
            mad = np.median(np.abs(y_true - y_pred))
            mape = np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1))) * 100
            mse = mean_squared_error(y_true, y_pred)

            # Plot
            plt.figure(figsize=(10, 5))
            plt.plot(y_true, label='Actual', linewidth=2)
            plt.plot(y_pred, label='Predicted', linewidth=2)
            plt.title(f"LSOA {lsoa}: Actual vs Predicted")
            plt.xlabel("Time Step")
            plt.ylabel("Burglaries")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(f"lsoa_forecast_{lsoa}.png")

            results.append({
                'lsoa': lsoa,
                'MAD': mad,
                'MAPE': mape,
                'MSE': mse
            })
        except Exception as e:
            print(f"Skipping {lsoa} due to error: {e}")

    df_results = pd.DataFrame(results)
    print("\nLSOA Performance Summary:")
    print(df_results)
    df_results.to_csv('lsoa_comparison_specific.csv', index=False)
    print("Saved to lsoa_comparison_specific.csv")
