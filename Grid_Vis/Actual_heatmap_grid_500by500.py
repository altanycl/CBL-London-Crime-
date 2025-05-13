import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import Fullscreen
from shapely.geometry import Polygon
from pathlib import Path
import sys

# === Paths ===
SCRIPT_DIR    = Path(__file__).resolve().parent
ROOT_DIR      = SCRIPT_DIR.parent
ACTUAL_CSV    = ROOT_DIR / 'outputs' / 'actual_past_year_500m.csv'
WARD_SHP      = ROOT_DIR / 'London-wards-2018-ESRI' / 'London_Ward.shp'
OUT_HTML      = ROOT_DIR / 'outputs' / 'london_500m_actual_past_year_heatmap.html'

# Validate file presence
for p in (ACTUAL_CSV, WARD_SHP):
    if not p.exists():
        print(f"Error: file not found: {p}", file=sys.stderr)
        sys.exit(1)

# === Load past-year aggregated counts ===
actual = pd.read_csv(ACTUAL_CSV)
assert {'cell_id','actual_past_year','year_end'}.issubset(actual.columns), \
    "CSV must have cell_id, actual_past_year, year_end"
actual['year_end'] = pd.to_datetime(actual['year_end'])
label = actual['year_end'].dt.strftime('%b %Y').iloc[0]

# === Build 500m grid from wards’ extent (to match aggregation) ===
wards = gpd.read_file(str(WARD_SHP)).to_crs(epsg=27700)
minx, miny, maxx, maxy = wards.total_bounds
step = 500
cells = []
for x in range(int(minx), int(maxx)+1, step):
    for y in range(int(miny), int(maxy)+1, step):
        cells.append(Polygon([(x, y), (x+step, y), (x+step, y+step), (x, y+step)]))
grid = gpd.GeoDataFrame({'geometry': cells}, crs=wards.crs)
grid['cell_id']  = grid.index

# === Merge counts into grid ===
# Remove any prior 'actual_past_year' column to avoid suffixes
if 'actual_past_year' in grid.columns:
    grid = grid.drop(columns=['actual_past_year'])

grid = grid.merge(
    actual[['cell_id','actual_past_year']],
    on='cell_id', how='left'
)
# Fill missing cells with zero
grid['actual_past_year'] = grid['actual_past_year'].fillna(0)

# Sanity check: print a few non-zero cells
nz = grid.loc[grid['actual_past_year']>0, ['cell_id','actual_past_year']].head(10)
print("Non-zero sample:\n", nz.to_string(index=False))

# === Prepare for Folium ===
grid_wgs = grid.to_crs(epsg=4326)
geojson = grid_wgs.to_json()

# === Draw Folium map ===
m = folium.Map(location=[51.5074, -0.1278], zoom_start=10, tiles='cartodbpositron')
Fullscreen().add_to(m)

folium.Choropleth(
    geo_data=geojson,
    data=grid_wgs,
    columns=['cell_id','actual_past_year'],
    key_on='feature.properties.cell_id',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.1,
    legend_name=f'Total Crimes Past 12 Months (through {label})',
    name='500 m Past-Year Heatmap'
).add_to(m)

# Ward boundaries overlay
folium.GeoJson(
    wards.to_crs(epsg=4326),
    name='Ward Boundaries',
    style_function=lambda feat: {'fillOpacity': 0, 'color': 'black', 'weight': 1}
).add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

# === Save ===
m.save(str(OUT_HTML))
print(f"✔ Saved actual 500 m past-year heatmap through {label} to {OUT_HTML}")
