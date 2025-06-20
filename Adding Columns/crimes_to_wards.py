import pandas as pd
import geopandas as gpd

# Paths
ward_shp   = r"C:\Coding\CBL-London-Crime-\London-wards-2018-ESRI\London_Ward.shp"
crime_csv  = r"C:\Users\borka\Downloads\all_burglaries_london_cleaned.csv"
output_csv = r"C:\Users\borka\Downloads\London_burglaries_with_wards_correct.csv"


# Load shapefile (convert to WGS84) and crime CSV
wards = gpd.read_file(ward_shp).to_crs("EPSG:4326")
df    = pd.read_csv(crime_csv)

# Turn crimes into a GeoDataFrame
gdf_crimes = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df.longitude, df.latitude),
    crs="EPSG:4326"
)

# Spatial join: attach ward polygons’ attributes to each crime point
gdf = gpd.sjoin(
    gdf_crimes,
    wards,
    how="left",
    predicate="within"
)

# Derive Month from dt
gdf['Month'] = pd.to_datetime(gdf['dt']).dt.strftime('%Y-%m')

# Drop the original dt and spatial/index columns
gdf = gdf.drop(columns=['dt', 'geometry', 'index_right'], errors='ignore')

# Rename shapefile fields to your target codes:
#   NAME       → WD24NM (ward name)
#   GSS_CODE   → WD24CD (ward code)
#   DISTRICT   → LAD24NM (borough name)
gdf.rename(columns={
    'NAME':      'WD24NM',
    'GSS_CODE':  'WD24CD',
    'DISTRICT':  'LAD24NM'
}, inplace=True)

# Reorder so Month is second
cols = list(gdf.columns)
cols.remove('Month')
cols = [cols[0], 'Month'] + cols[1:]

# Save to CSV
gdf[cols].to_csv(output_csv, index=False)
print(f"[DONE] Saved output to: {output_csv}")
