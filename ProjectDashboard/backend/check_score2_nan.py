import pandas as pd

csv_path = "data/last_month_predictions_detailed_with_scores.csv"
df = pd.read_csv(csv_path)
nan_count = df['score2'].isna().sum()
 
if nan_count > 0:
    print(f"Found {nan_count} NaN values in the 'score2' column.")
    print(df[df['score2'].isna()])
else:
    print("No NaN values found in the 'score2' column.") 