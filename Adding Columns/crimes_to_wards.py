import pandas as pd
import geopandas as gpd

# Paths
ward_shp = r"C:\Coding\CBL-London-Crime-\London-wards-2018-ESRI\London_Ward.shp"
crime_csv = r"C:\Users\borka\Downloads\all_burglaries_london_cleaned_num_crimes_past_year_1km.csv"
output_csv = r"C:\Users\borka\Downloads\London burglaries with ward names.csv"

# Load shapefile and crime data
wards = gpd.read_file(ward_shp).to_crs("EPSG:4326")
df = pd.read_csv(crime_csv)

# Convert crimes to GeoDataFrame
gdf_crimes = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df.longitude, df.latitude),
    crs="EPSG:4326"
)

# Check column names in ward file
print("[INFO] Ward columns:", wards.columns)

# Spatial join
gdf_joined = gpd.sjoin(gdf_crimes, wards, how="left", predicate="within")

# Rename columns
gdf_joined = gdf_joined.rename(columns={
    'NAME': 'Ward name',
    'DISTRICT': 'Borough name'
})

# Save result
gdf_joined.drop(columns='geometry').to_csv(output_csv, index=False)
# Format dt → Month (YYYY-MM)
gdf_joined['Month'] = pd.to_datetime(gdf_joined['dt']).dt.strftime('%Y-%m')
gdf_joined = gdf_joined.drop(columns='dt')

# Reorder columns: keep Month as second column
cols = list(gdf_joined.columns)
cols.remove('Month')
cols = [cols[0], 'Month'] + cols[1:]  # insert Month after the first column

# Final write
gdf_joined = gdf_joined[cols]
gdf_joined.drop(columns='geometry', errors='ignore').to_csv(output_csv, index=False)
print(f"[DONE] Saved with reordered Month column to: {output_csv}")

