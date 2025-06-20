import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import Fullscreen
from shapely.geometry import Polygon
from pathlib import Path

# === 1) Normalization function ===
def normalize(name):
    return (
        str(name)
        .lower()
        .replace("’", "'")
        .replace("‘", "'")
        .replace("–", "-")
        .replace("—", "-")
        .replace("&", "and")
        .replace(".", "")
        .replace(",", "")
        .replace("’s", "s")
        .strip()
    )

# === 2) Paths ===
BASE = Path(__file__).resolve().parent
PRED_CSV = BASE / "outputs" / "next_month_predictions.csv"
WARD_SHP = BASE / "London-wards-2018-ESRI" / "London_Ward.shp"
OUT_HTML = BASE / "outputs" / "london_1km_heatmap.html"

# === 3) Load & clean predictions ===
preds = pd.read_csv(PRED_CSV)
preds["ward_clean"] = preds["ward"].apply(normalize)
prediction_month = pd.to_datetime(preds["Month"].iloc[0]).strftime("%B %Y")

# === 4) Load & clean ward geometries ===
wards = gpd.read_file(str(WARD_SHP))
wards["NAME_clean"] = wards["NAME"].apply(normalize)

# === 5) Merge ward geometries with your predictions ===
merged = (
    wards
    .merge(preds, left_on="NAME_clean", right_on="ward_clean", how="left")
    .dropna(subset=["prediction"])
)

# === 6) Reproject to a metric CRS (British National Grid) ===
merged_m = merged.to_crs(epsg=27700)

# === 7) Build a 1 000 m × 1 000 m fishnet grid ===
minx, miny, maxx, maxy = merged_m.total_bounds
step = 1000  # metres

cells = []
for x in range(int(minx), int(maxx), step):
    for y in range(int(miny), int(maxy), step):
        cells.append(Polygon([
            (x,   y),
            (x+step, y),
            (x+step, y+step),
            (x,   y+step),
        ]))

grid = gpd.GeoDataFrame({"geometry": cells}, crs=merged_m.crs)
grid["cell_id"] = grid.index
# **HERE** we compute and store each cell’s area in m²
grid["area_grid"] = grid.area

# === 8) Intersect wards with grid cells ===
intersect = gpd.overlay(
    merged_m[["geometry", "prediction"]],
    grid[["cell_id", "geometry", "area_grid"]],
    how="intersection"
)

# === 9) Compute intersection area and weight ===
intersect["area_int"] = intersect.area
# weighted_pred = ward_prediction * (intersection_area / cell_area)
intersect["weighted_pred"] = (
    intersect["prediction"] 
    * (intersect["area_int"] / intersect["area_grid"])
)

# === 10) Sum contributions per cell ===
cell_preds = (
    intersect
    .groupby("cell_id", as_index=False)["weighted_pred"]
    .sum()
    .rename(columns={"weighted_pred": "pred_burglaries_per_m2"})
)

# merge back onto grid
grid = grid.merge(cell_preds, on="cell_id", how="left")
grid["pred_burglaries_per_m2"] = grid["pred_burglaries_per_m2"].fillna(0)

# for convenience, scale to per km²
grid["pred_per_km2"] = grid["pred_burglaries_per_m2"] * 1e6

# === 11) Back to WGS84 & to GeoJSON ===
grid_wgs = grid.to_crs(epsg=4326)
grid_json = grid_wgs.to_json()

# === 12) Build the Folium map ===
m = folium.Map(location=[51.5074, -0.1278], zoom_start=10, tiles="cartodbpositron")
Fullscreen().add_to(m)

folium.Choropleth(
    geo_data=grid_json,
    data=grid_wgs,
    columns=["cell_id", "pred_per_km2"],
    key_on="feature.properties.cell_id",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.1,
    legend_name=f"Predicted Burglaries per km² – {prediction_month}",
    name="1 km Grid Heatmap",
).add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

# === 13) Save ===
m.save(str(OUT_HTML))
print(f"✔ 1 km heatmap written to {OUT_HTML}")
