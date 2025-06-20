# LSTM Evaluation with Report-Style Metrics Summary (Wards & LSOAs)
# ================================================================

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
        self.model.fit(
            X_tr, y_tr,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=actual_batch,
            callbacks=callbacks,
            verbose=0
        )

    def score(self, test):
        X_test, y_test = test
        y_pred_scaled = self.model.predict(X_test)
        y_pred = self.scaler.inverse_transform(y_pred_scaled)
        y_true = self.scaler.inverse_transform(y_test.reshape(-1, 1))
        mad = np.median(np.abs(y_true - y_pred))
        mape = np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1))) * 100
        mse = mean_squared_error(y_true, y_pred)
        return mse, mad, mape

if __name__ == '__main__':
    df = pd.read_csv('London_burglaries_with_wards_correct.csv', parse_dates=['Month'])
    df['count'] = 1

    # === Ward-level evaluation ===
    df_w = df.groupby(['WD24CD', 'Month'], as_index=False)['count'].count()
    df_w.rename(columns={'count': 'burglaries'}, inplace=True)
    top_wards = df_w['WD24CD'].value_counts().head(5).index.tolist()

    ward_metrics = []
    for code in top_wards:
        series = df_w.loc[df_w['WD24CD'] == code, 'burglaries'].values
        model = ImprovedLSTM()
        try:
            train, val, test = model.prepare(series)
            model.fit(train, val)
            mse, mad, mape = model.score(test)
            ward_metrics.append((code, mse, mad, mape))
        except:
            ward_metrics.append((code, np.nan, np.nan, np.nan))

    # === LSOA-level evaluation ===
    df_l = df.groupby(['LSOA code', 'Month'], as_index=False)['count'].count()
    df_l.rename(columns={'count': 'burglaries'}, inplace=True)
    top_lsoas = df_l['LSOA code'].value_counts().head(5).index.tolist()

    lsoa_metrics = []
    for code in top_lsoas:
        series = df_l.loc[df_l['LSOA code'] == code, 'burglaries'].values
        model = ImprovedLSTM()
        try:
            train, val, test = model.prepare(series)
            model.fit(train, val)
            mse, mad, mape = model.score(test)
            lsoa_metrics.append((code, mse, mad, mape))
        except:
            lsoa_metrics.append((code, np.nan, np.nan, np.nan))

    # === Output formatted like screenshot ===
    print("\n================== Ward-level LSTM metrics ==================")
    print(f"{'Ward':<12} {'MSE':>8} {'MAD':>8} {'MAPE':>8}")
    for name, mse, mad, mape in ward_metrics:
        print(f"{name:<12} {mse:8.2f} {mad:8.2f} {mape:8.2f}")

    print("\n================== LSOA-level LSTM metrics ==================")
    print(f"{'LSOA':<12} {'MSE':>8} {'MAD':>8} {'MAPE':>8}")
    for name, mse, mad, mape in lsoa_metrics:
        print(f"{name:<12} {mse:8.2f} {mad:8.2f} {mape:8.2f}")

    # === Averages ===
    ward_avg = pd.DataFrame(ward_metrics, columns=['label','mse','mad','mape']).mean(numeric_only=True)
    lsoa_avg = pd.DataFrame(lsoa_metrics, columns=['label','mse','mad','mape']).mean(numeric_only=True)
    print("\n------------------ Averages ------------------")
    print(f"Wards  => MSE={ward_avg['mse']:.2f}, MAD={ward_avg['mad']:.2f}, MAPE={ward_avg['mape']:.2f}")
    print(f"LSOAs  => MSE={lsoa_avg['mse']:.2f}, MAD={lsoa_avg['mad']:.2f}, MAPE={lsoa_avg['mape']:.2f}")
