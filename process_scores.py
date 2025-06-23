import pandas as pd
import numpy as np

# ─── 1) Load input ──────────────────────────────────────────────────────────────
df = pd.read_csv('last_month_predictions_detailed.csv')

# ─── 2) Compute global thresholds ──────────────────────────────────────────────
threshold_1pct = np.percentile(df['y_pred_lgb'], 99)
threshold_3pct = np.percentile(df['y_pred_lgb'], 97)

print(f"Threshold for top 1%: {threshold_1pct:.3f}")
print(f"Threshold for top 3%: {threshold_3pct:.3f}\n")

# ─── 3) Allocation parameters ──────────────────────────────────────────────────
T   = 800.0    # total hours per ward per week
phi = 20.0     # fixed floor per LSOA in any ward (h/week)
p   = 2        # power for risk weighting

# ─── 4) Initialize new columns ─────────────────────────────────────────────────
df['score1']   = 0.0
df['score1_5'] = 0.0
df['score2']   = 0.0
df['rec_1pct'] = 0
df['rec_3pct'] = 0
df['hours']    = 0.0

# ─── 5) Process each ward ──────────────────────────────────────────────────────
for ward_code, ward_data in df.groupby('WD24CD'):
    idx = ward_data.index
    y   = ward_data['y_pred_lgb']
    
    # 5.1) Compute the three power-based scores
    sum1   = y.sum()
    sum1_5 = (y ** 1.5).sum()
    sum2   = (y ** p).sum()
    
    if sum1   > 0: df.loc[idx, 'score1']   = y / sum1
    if sum1_5 > 0: df.loc[idx, 'score1_5'] = (y ** 1.5) / sum1_5
    if sum2   > 0: df.loc[idx, 'score2']   = (y ** p) / sum2
    
    # 5.2) Flag wards for intervention
    if (y >= threshold_1pct).any():
        df.loc[idx, 'rec_1pct'] = 1
    if (y >= threshold_3pct).any():
        df.loc[idx, 'rec_3pct'] = 1
    
    # 5.3) Allocate hours
    N = len(ward_data)
    if df.loc[idx, 'rec_3pct'].iloc[0] == 1:
        # hot ward: floor + risk-weighted top-up
        min_total = N * phi
        if min_total > T:
            raise ValueError(
                f"Ward {ward_code!r}: need {min_total:.1f}h floor > {T}h avail."
            )
        leftover = T - min_total
        if sum2 > 0:
            hours = phi + leftover * ((y ** p) / sum2)
        else:
            hours = np.full(N, phi)
    else:
        # cold ward: fixed 20 h/week per LSOA
        hours = np.full(N, phi)
    
    df.loc[idx, 'hours'] = hours

# ─── 6) Save allocation output ─────────────────────────────────────────────────
out_csv = 'last_month_predictions_detailed_with_scores_and_hours.csv'
df.to_csv(out_csv, index=False)
print(f"Saved allocation file: {out_csv}\n")

# ─── 7) Quality checks ─────────────────────────────────────────────────────────
print("Running quality checks...")

# 7.1) Ward totals = 800?
totals = df.groupby('WD24CD')['hours'].sum()

# 7.2) Compute leftover per ward
leftovers = (T - totals).rename('leftover')

# 7.3) Print leftover summary
count_600_plus = (leftovers >= 600).sum()
count_500_plus = (leftovers >= 500).sum()
count_strictly_positive = (leftovers > 0).sum()
count_zero     = (leftovers == 0).sum()
total_leftover = leftovers.sum()

print(f"Wards with leftover ≥ 600 h: {count_600_plus}")
print(f"Wards with leftover ≥ 500 h: {count_500_plus}")
print(f"Wards with leftover > 0 h: {count_strictly_positive}")
print(f"Wards with leftover = 0 h: {count_zero}")
print(f"Total leftover hours across all wards: {total_leftover:.1f} h\n")

# 7.4) Other checks (optional)
bad_totals = totals[np.abs(totals - T) > 1e-6]
if bad_totals.empty:
    print("✔ All wards sum to 800 h.")
else:
    print("✖ Wards with total ≠ 800 h:")
    print(bad_totals)

print("Quality checks complete.")
