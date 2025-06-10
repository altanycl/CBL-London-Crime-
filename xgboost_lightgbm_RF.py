import pandas as pd
import numpy as np
import xgboost as xgb

# Attempt to import LightGBM. If unavailable, we skip it.
try:
    import lightgbm as lgb
    has_lgb = True
except ModuleNotFoundError:
    has_lgb = False

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt

# ─── 1) Load & preprocess the CSV ────────────────────────────────────────────────
csv_path = r"combined_features.csv"
df = pd.read_csv(csv_path)

# 1.1) Rename "LSOA code" → "LSOA_code", encode if needed
df.rename(columns={"LSOA code": "LSOA_code"}, inplace=True)
if df['LSOA_code'].dtype == 'object':
    le = LabelEncoder()
    df['LSOA_code'] = le.fit_transform(df['LSOA_code'])

# Encode WD24CD and WD24NM if they are object type
if 'WD24CD' in df.columns and df['WD24CD'].dtype == 'object':
    le_ward_code = LabelEncoder()
    df['WD24CD'] = le_ward_code.fit_transform(df['WD24CD'])
if 'WD24NM' in df.columns and df['WD24NM'].dtype == 'object':
    le_ward_name = LabelEncoder()
    df['WD24NM'] = le_ward_name.fit_transform(df['WD24NM'])

# 1.2) Parse "month" → datetime
df['month_parsed'] = pd.to_datetime(df['month'], format="%Y-%m", errors='coerce')
# 1.3) Create "year_month" string
df['year_month'] = df['month_parsed'].dt.to_period('M').astype(str)
# 1.4) Count rows in Feb 2025
counts = df['year_month'].value_counts().sort_index()
feb_2025_count = counts.get("2025-02", 0)
print(f"Rows for 2025-02: {feb_2025_count}")
# 1.5) Extract numeric year & month
df['year'] = df['month_parsed'].dt.year
df['month_num'] = df['month_parsed'].dt.month
# 1.6) Drop original month & nulls
df = df.drop(columns=['month']).dropna()

# ─── 2) Time-based split: train vs. last-month ─────────────────────────────────
last_month_date = df['month_parsed'].max()
df_train_time = df[df['month_parsed'] < last_month_date].copy()
df_last_time  = df[df['month_parsed'] == last_month_date].copy()
print(f"Last month → {last_month_date.year}-{last_month_date.month:02d}")

# ─── 3) Features & target ───────────────────────────────────────────────────────
features = [
    'LSOA_code',
    'crime_count_lag1','crime_count_lag3','crime_count_lag12',
    'num_crimes_past_year_1km','MedianPrice',
    'month_sin','month_cos',
    'rank_last_year','months_since_last_crime','year','month_num',
    'WD24CD','WD24NM',
    'IMD Rank London', 'IMD Decile London', 'Population', 'PopulationPerSqKm', 'AreaSqKm',
    'crime_count_lag1_z','crime_count_lag3_z','crime_count_lag12_z',
    'num_crimes_past_year_1km_z','MedianPrice_z','months_since_last_crime_z'
]
X_train_time, y_train_time = df_train_time[features], df_train_time['y_true']
X_last_time,  y_last_time  = df_last_time[features],  df_last_time['y_true']

# ─── 4) Train models (time-based) ───────────────────────────────────────────────
xgb_model = xgb.XGBRegressor(objective="reg:squarederror", n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
xgb_model.fit(X_train_time, y_train_time)
if has_lgb:
    lgb_model = lgb.LGBMRegressor(objective="regression", n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
    lgb_model.fit(X_train_time, y_train_time)
rf_model = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)
rf_model.fit(X_train_time, y_train_time)

# ─── 5) Evaluate on last-month (time-based) ────────────────────────────────────
def evaluate_and_print(model, X_test, y_test, name):
    y_pred = model.predict(X_test)
    print(f"{name:<10} MSE: {mean_squared_error(y_test, y_pred):.4f} | MAE: {mean_absolute_error(y_test, y_pred):.4f}")
print("\n=== Time-based hold-out (last-month) ===")
evaluate_and_print(xgb_model, X_last_time, y_last_time, "XGBoost")
if has_lgb:
    evaluate_and_print(lgb_model, X_last_time, y_last_time, "LightGBM")
evaluate_and_print(rf_model, X_last_time, y_last_time, "RandomForest")

# ─── 5.1) Export last-month predictions ─────────────────────────────────────────
df_last_time = df_last_time.copy()
df_last_time['y_pred_xgb'] = xgb_model.predict(X_last_time)
if has_lgb: df_last_time['y_pred_lgb'] = lgb_model.predict(X_last_time)
df_last_time['y_pred_rf']  = rf_model.predict(X_last_time)
export_cols = ['LSOA_code','WD24CD','WD24NM','year_month','y_true','y_pred_xgb','y_pred_rf']
if has_lgb: export_cols.insert(4,'y_pred_lgb')
results_df = df_last_time[export_cols]
results_df.to_csv('last_month_predictions.csv', index=False)
print("Saved: last_month_predictions.csv")

# ─── 6) Random 80/20 split ─────────────────────────────────────────────────────
X_full, y_full = df[features], df['y_true']
X_train_rand, X_test_rand, y_train_rand, y_test_rand = train_test_split(X_full, y_full, test_size=0.2, random_state=42)

# ─── 7) Train models (random split) ─────────────────────────────────────────────
xgb_model_rand = xgb.XGBRegressor(objective="reg:squarederror", n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
xgb_model_rand.fit(X_train_rand, y_train_rand)
if has_lgb:
    lgb_model_rand = lgb.LGBMRegressor(objective="regression", n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
    lgb_model_rand.fit(X_train_rand, y_train_rand)
rf_model_rand = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)
rf_model_rand.fit(X_train_rand, y_train_rand)
print("\n=== Random 80/20 split metrics ===")
evaluate_and_print(xgb_model_rand, X_test_rand, y_test_rand, "XGBoost")
if has_lgb:
    evaluate_and_print(lgb_model_rand, X_test_rand, y_test_rand, "LightGBM")
evaluate_and_print(rf_model_rand, X_test_rand, y_test_rand, "RandomForest")

# ─── 8) Feature importances (time-based) ───────────────────────────────────────
xgb_imp = pd.Series(xgb_model.feature_importances_, index=features).sort_values()
rf_imp = pd.Series(rf_model.feature_importances_, index=features).sort_values()
if has_lgb:
    lgb_imp = pd.Series(lgb_model.feature_importances_, index=features).sort_values()
n_plots = 3 if has_lgb else 2
fig, axes = plt.subplots(1, n_plots, figsize=(5*n_plots,6))
ax = axes[0] if n_plots>1 else axes
xgb_imp.plot(kind='barh', ax=ax); ax.set_title("XGBoost Importance (time)")
if has_lgb:
    ax = axes[1]; lgb_imp.plot(kind='barh', ax=ax); ax.set_title("LightGBM Importance (time)"); ax=axes[2]
else:
    ax = axes[1] if n_plots>1 else axes
rf_imp.plot(kind='barh', ax=ax); ax.set_title("RF Importance (time)")
plt.tight_layout(); plt.show()

# ─── 9) Feature importances (random split) ─────────────────────────────────────
xgb_imp_rand = pd.Series(xgb_model_rand.feature_importances_, index=features).sort_values()
rf_imp_rand = pd.Series(rf_model_rand.feature_importances_, index=features).sort_values()
if has_lgb:
    lgb_imp_rand = pd.Series(lgb_model_rand.feature_importances_, index=features).sort_values()
n_plots_rand = 3 if has_lgb else 2
fig2, axes2 = plt.subplots(1, n_plots_rand, figsize=(5*n_plots_rand,6))
ax2 = axes2[0] if n_plots_rand>1 else axes2
xgb_imp_rand.plot(kind='barh', ax=ax2); ax2.set_title("XGBoost Importance (80/20)")
if has_lgb:
    ax2 = axes2[1]; lgb_imp_rand.plot(kind='barh', ax=ax2); ax2.set_title("LightGBM Importance (80/20)"); ax2=axes2[2]
else:
    ax2 = axes2[1] if n_plots_rand>1 else axes2
rf_imp_rand.plot(kind='barh', ax=ax2); ax2.set_title("RF Importance (80/20)")
plt.tight_layout(); plt.show()
