import pandas as pd
import geopandas as gpd

# Load predictions CSV from the correct path
pred_df = pd.read_csv("data/last_month_predictions_detailed_with_scores_and_hours.csv")

# Load shapefile from the correct path
shp = gpd.read_file("LSOA_boundries/LSOA_2021_EW_BFE_V10.shp")

# Use the same columns as the frontend: 'LSOA21CD' for code and 'LSOA21NM' for name
lookup_df = shp[["LSOA21CD", "LSOA21NM"]].rename(columns={"LSOA21CD": "LSOA code", "LSOA21NM": "lsoa_name"})

# Merge on 'LSOA code'
merged = pred_df.merge(lookup_df, on="LSOA code", how="left")

# Save the result to the data directory
merged.to_csv("data/last_month_predictions_detailed_with_scores_and_hours_with_names.csv", index=False)

print("Done! Output: data/last_month_predictions_detailed_with_scores_and_hours_with_names.csv") 