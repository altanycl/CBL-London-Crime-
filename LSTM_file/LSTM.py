
# Improved LSTM Pipeline for London Burglary Forecasting
# =====================================================
# This script loads monthly burglary counts per ward, trains an improved LSTM model,
# evaluates performance, and saves diagnostic plots.

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import warnings
warnings.filterwarnings('ignore')

# Use non-interactive backend for saving plots
plt.switch_backend('Agg')

class ImprovedLSTM:
    def __init__(self, sequence_length=10, lr=1e-3):
        self.sequence_length = sequence_length
        self.scaler = MinMaxScaler(feature_range=(0,1))
        self.learning_rate = lr
        self.model = None

    def create_sequences(self, data):
        X, y = [], []
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i+self.sequence_length, 0])
            y.append(data[i+self.sequence_length, 0])
        return np.array(X), np.array(y)

    def prepare(self, series, test_frac=0.2, val_frac=0.1):
        # Scale the data
        scaled = self.scaler.fit_transform(series.reshape(-1,1))
        X, y = self.create_sequences(scaled)
        n_total = len(X)
        n_test = int(n_total * test_frac)
        n_val = int(n_total * val_frac)
        n_train = n_total - n_test - n_val

        X_train, y_train = X[:n_train], y[:n_train]
        X_val, y_val     = X[n_train:n_train+n_val], y[n_train:n_train+n_val]
        X_test, y_test   = X[-n_test:], y[-n_test:]

        # Reshape for LSTM: (samples, time_steps, features)
        X_train = X_train.reshape(-1, self.sequence_length, 1)
        X_val   = X_val.reshape(-1, self.sequence_length, 1)
        X_test  = X_test.reshape(-1, self.sequence_length, 1)

        print(f"Data prepared: train={X_train.shape[0]}, val={X_val.shape[0]}, test={X_test.shape[0]}")
        return (X_train, y_train), (X_val, y_val), (X_test, y_test)

    def build(self):
        model = Sequential([
            LSTM(64, return_sequences=True, input_shape=(self.sequence_length,1)),
            Dropout(0.2), BatchNormalization(),
            LSTM(32, return_sequences=False),
            Dropout(0.2), BatchNormalization(),
            Dense(16, activation='relu'), Dropout(0.1),
            Dense(1)
        ])
        model.compile(optimizer=Adam(self.learning_rate), loss='mse', metrics=['mae'])
        return model

    def fit(self, train, val, epochs=100, batch_size=32):
        X_tr, y_tr = train
        X_v, y_v   = val
        self.model = self.build()
        actual_batch = max(1, min(batch_size, X_tr.shape[0]))
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True, verbose=1),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10, min_lr=1e-6, verbose=1)
        ]
        history = self.model.fit(
            X_tr, y_tr,
            validation_data=(X_v, y_v),
            epochs=epochs,
            batch_size=actual_batch,
            callbacks=callbacks,
            verbose=2
        )
        return history

    def evaluate(self, test):
        X_te, y_te = test
        y_pred_scl = self.model.predict(X_te)
        y_pred = self.scaler.inverse_transform(y_pred_scl)
        y_true = self.scaler.inverse_transform(y_te.reshape(-1,1))
        mse = mean_squared_error(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true, y_pred)
        print(f"Test results -> MSE: {mse:.3f}, MAE: {mae:.3f}, RMSE: {rmse:.3f}, R2: {r2:.3f}")
        return y_true, y_pred

    def plot(self, hist, y_true, y_pred, fname='lstm_diagnostics.png'):
        plt.figure(figsize=(12,8))
        # Plot loss curves
        plt.subplot(2,1,1)
        plt.plot(hist.history['loss'], label='Train Loss')
        plt.plot(hist.history['val_loss'], label='Val Loss')
        plt.title('Loss Over Epochs')
        plt.legend(); plt.grid(True)
        # Plot predictions vs actual
        plt.subplot(2,1,2)
        plt.plot(y_true, label='Actual')
        plt.plot(y_pred, label='Predicted')
        plt.title('Actual vs Predicted')
        plt.legend(); plt.grid(True)
        plt.tight_layout()
        plt.savefig(fname, dpi=300)
        print(f"Diagnostics saved to {fname}")

# === Main Execution ===
if __name__ == '__main__':
    # Load data
    df = pd.read_csv('crime_with_wards_num_crimes_past_year_1km_full_period.csv', parse_dates=['Month'])
    df['count'] = 1
    grp = df.groupby(['WD24CD','Month'], as_index=False)['count'].count()
    grp.rename(columns={'count':'burglaries'}, inplace=True)

    # Select ward with most data
    ward_counts = grp['WD24CD'].value_counts()
    ward = ward_counts.idxmax()
    series = grp.loc[grp['WD24CD']==ward, 'burglaries'].values
    print(f"Using ward {ward} with {len(series)} months of data")

    # Initialize and run
    model = ImprovedLSTM(sequence_length=10, lr=1e-3)
    train, val, test = model.prepare(series)
    history = model.fit(train, val, epochs=50)
    y_true, y_pred = model.evaluate(test)
    model.plot(history, y_true, y_pred)

