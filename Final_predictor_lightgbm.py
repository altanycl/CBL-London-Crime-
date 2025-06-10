import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split, TimeSeriesSplit, GridSearchCV
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import joblib
import os

# ─── 1) Load & preprocess the CSV ────────────────────────────────────────────────
csv_path = r"combined_features.csv"
df = pd.read_csv(csv_path)

# Keep original string columns for export
original_cols = df[['LSOA code', 'WD24CD', 'WD24NM', 'month']].copy()

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
    'LSOA_code','crime_count_lag1','crime_count_lag3','crime_count_lag12',
    'num_crimes_past_year_1km','MedianPrice','month_sin','month_cos',
    'rank_last_year','months_since_last_crime','year','month_num',
    'crime_count_lag1_z','crime_count_lag3_z','crime_count_lag12_z',
    'num_crimes_past_year_1km_z','MedianPrice_z','months_since_last_crime_z'
]
X_train_time, y_train_time = df_train_time[features], df_train_time['y_true']
X_last_time,  y_last_time  = df_last_time[features],  df_last_time['y_true']

# ─── 4) Train LightGBM model (time-based) ───────────────────────────────────────
# Reduced grid search for faster execution
param_grid = {
    'n_estimators': [100, 200],
    'max_depth': [4, 8],
    'learning_rate': [0.05, 0.1],
    'subsample': [0.8, 1.0],
    'colsample_bytree': [0.8, 1.0],
    'min_child_samples': [20, 50]
}
tscv = TimeSeriesSplit(n_splits=3)

base_model = lgb.LGBMRegressor(
    objective="regression",
    random_state=42
)

print("\nStarting grid search (should be much faster)...")
grid_search = GridSearchCV(
    estimator=base_model,
    param_grid=param_grid,
    cv=tscv,
    scoring='neg_mean_squared_error',
    n_jobs=-1,
    verbose=1
)
grid_search.fit(X_train_time, y_train_time)
best_params = grid_search.best_params_
print("\nBest parameters:", best_params)

# Train final model with best parameters and non-negative constraints
lgb_model = lgb.LGBMRegressor(
    **best_params,
    random_state=42,
    min_child_weight=0.001,
    min_split_gain=0.0,
    reg_alpha=0.1,
    reg_lambda=0.1
)
lgb_model.fit(X_train_time, y_train_time)

# Save the trained model
model_dir = "models"
os.makedirs(model_dir, exist_ok=True)
joblib.dump(lgb_model, os.path.join(model_dir, "lgb_model.joblib"))
print(f"Model saved to {os.path.join(model_dir, 'lgb_model.joblib')}")

# ─── 5) Evaluate on last-month (time-based) ────────────────────────────────────
def evaluate_and_print(model, X_test, y_test, name):
    # Get predictions and correct negatives
    y_pred = model.predict(X_test)
    y_pred = np.maximum(y_pred, 0)  # Replace negatives with 0
    
    # Calculate metrics on corrected predictions
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"\n{name} Performance Metrics:")
    print(f"MSE:  {mse:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"MAE:  {mae:.4f}")
    print(f"R²:   {r2:.4f}")
    
    # Print feature importances
    importances = pd.Series(model.feature_importances_, index=features)
    print("\nTop 5 Most Important Features:")
    print(importances.sort_values(ascending=False).head())
    
    return y_pred  # Return corrected predictions

print("\n=== Time-based hold-out (last-month): LightGBM ===")
y_pred_time = evaluate_and_print(lgb_model, X_last_time, y_last_time, "LightGBM")

# ─── 5.1) Export last-month predictions with more details ───────────────────────
df_last_time = df_last_time.copy()
df_last_time['y_pred_lgb'] = y_pred_time  # Use corrected predictions

# Restore original string columns for export (time-based)
last_time_idx = df_last_time.index
original_last = original_cols.loc[last_time_idx].reset_index(drop=True)
results_df = pd.concat([
    original_last[['LSOA code', 'WD24CD', 'WD24NM', 'month']],
    df_last_time[['year_month', 'y_true', 'y_pred_lgb', 'month_num', 'year']].reset_index(drop=True)
], axis=1)
results_df['absolute_error'] = abs(results_df['y_true'] - results_df['y_pred_lgb'])
results_df['squared_error'] = (results_df['y_true'] - results_df['y_pred_lgb'])**2
results_df.to_csv('last_month_predictions_detailed.csv', index=False)
print("Saved: last_month_predictions_detailed.csv")

# Save performance statistics for both models
stats_time = {
    'MSE': mean_squared_error(results_df['y_true'], results_df['y_pred_lgb']),
    'RMSE': np.sqrt(mean_squared_error(results_df['y_true'], results_df['y_pred_lgb'])),
    'MAE': mean_absolute_error(results_df['y_true'], results_df['y_pred_lgb']),
    'R2': r2_score(results_df['y_true'], results_df['y_pred_lgb']),
    'Best Parameters': best_params
}

# Get top 10 important features for both models
imp_time = pd.Series(lgb_model.feature_importances_, index=features).sort_values(ascending=False)

with open('model_performance_stats.txt', 'w') as f:
    f.write("Model Performance Statistics\n")
    f.write("==========================\n\n")
    f.write("Time-based Model (Last Month Hold-out)\n")
    f.write("------------------------------------\n")
    f.write(f"MSE:  {stats_time['MSE']:.4f}\n")
    f.write(f"RMSE: {stats_time['RMSE']:.4f}\n")
    f.write(f"MAE:  {stats_time['MAE']:.4f}\n")
    f.write(f"R²:   {stats_time['R2']:.4f}\n\n")
    f.write("Top 10 Most Important Features:\n")
    for i, (feat, val) in enumerate(imp_time.head(10).items(), 1):
        f.write(f"{i}. {feat}: {val}\n")
    f.write("\n")
    f.write("Best Parameters (used for both models):\n")
    for param, value in stats_time['Best Parameters'].items():
        f.write(f"{param}: {value}\n")
print("Saved: model_performance_stats.txt")

# ─── 6) Random 80/20 split ─────────────────────────────────────────────────────
X_full, y_full = df[features], df['y_true']
X_train_rand, X_test_rand, y_train_rand, y_test_rand = train_test_split(X_full, y_full, test_size=0.2, random_state=42)

# ─── 7) Train LightGBM model (random split) ─────────────────────────────────────
lgb_model_rand = lgb.LGBMRegressor(**best_params, random_state=42)
lgb_model_rand.fit(X_train_rand, y_train_rand)
print("\n=== Random 80/20 split metrics: LightGBM ===")
y_pred_rand = evaluate_and_print(lgb_model_rand, X_test_rand, y_test_rand, "LightGBM")

# Restore original string columns for export (random split)
rand_idx = X_test_rand.index
original_rand = original_cols.loc[rand_idx].reset_index(drop=True)
results_rand_df = pd.concat([
    original_rand[['LSOA code', 'WD24CD', 'WD24NM', 'month']],
    pd.DataFrame({
        'y_true': y_test_rand.values,
        'y_pred_lgb': y_pred_rand,
    }).reset_index(drop=True)
], axis=1)
results_rand_df['absolute_error'] = abs(results_rand_df['y_true'] - results_rand_df['y_pred_lgb'])
results_rand_df['squared_error'] = (results_rand_df['y_true'] - results_rand_df['y_pred_lgb'])**2
results_rand_df.to_csv('random_split_predictions_detailed.csv', index=False)
print("Saved: random_split_predictions_detailed.csv")

# ─── 8) Save all visualizations ───────────────────────────────────────────────
# Save feature importance plots
# Time-based model
plt.figure(figsize=(10, 6))
lgb_imp = pd.Series(lgb_model.feature_importances_, index=features).sort_values()
lgb_imp.plot(kind='barh')
plt.title("Feature Importance (Time-based Model)")
plt.tight_layout()
plt.savefig('feature_importance_time.png')
plt.close()

# Random split model
plt.figure(figsize=(10, 6))
lgb_imp_rand = pd.Series(lgb_model_rand.feature_importances_, index=features).sort_values()
lgb_imp_rand.plot(kind='barh')
plt.title("Feature Importance (Random Split Model)")
plt.tight_layout()
plt.savefig('feature_importance_random.png')
plt.close()

# Create and save prediction vs actual plot (using corrected predictions)
plt.figure(figsize=(10, 6))
plt.scatter(results_df['y_true'], results_df['y_pred_lgb'], alpha=0.5)
plt.plot([0, results_df['y_true'].max()], [0, results_df['y_true'].max()], 'r--')
plt.xlabel('Actual Values')
plt.ylabel('Predicted Values')
plt.title('Predicted vs Actual Values')
plt.tight_layout()
plt.savefig('predicted_vs_actual.png')
plt.close()

print("Saved visualization plots:")
print("- feature_importance_time.png")
print("- feature_importance_random.png")
print("- predicted_vs_actual.png")

# ─── 9) Feature importances (time-based) ───────────────────────────────────────
lgb_imp = pd.Series(lgb_model.feature_importances_, index=features).sort_values()
fig, ax = plt.subplots(1, 1, figsize=(8,6))
lgb_imp.plot(kind='barh', ax=ax); ax.set_title("LightGBM Importance (time)")
plt.tight_layout(); plt.show()

# ─── 9) Feature importances (random split) ─────────────────────────────────────
lgb_imp_rand = pd.Series(lgb_model_rand.feature_importances_, index=features).sort_values()
fig2, ax2 = plt.subplots(1, 1, figsize=(8,6))
lgb_imp_rand.plot(kind='barh', ax=ax2); ax2.set_title("LightGBM Importance (80/20)")
plt.tight_layout(); plt.show()
