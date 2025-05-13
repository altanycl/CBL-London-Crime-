import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import Fullscreen
from shapely.geometry import Polygon
from pathlib import Path
import sys

# === Paths ===
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR   = SCRIPT_DIR.parent  # project root
ACTUAL_CSV = ROOT_DIR / 'outputs' / 'actual_past_year_500m.csv'
WARD_SHP   = ROOT_DIR / 'London-wards-2018-ESRI' / 'London_Ward.shp'
OUT_HTML   = ROOT_DIR / 'outputs' / 'london_500m_actual_past_year_heatmap.html'

# Check inputs
for path in (ACTUAL_CSV, WARD_SHP):
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

# === Load past-year counts ===
# expects columns: cell_id, actual_past_year, year_end
actual = pd.read_csv(ACTUAL_CSV)
if not {'cell_id','actual_past_year','year_end'}.issubset(actual.columns):
    print(f"Error: CSV must contain 'cell_id','actual_past_year','year_end' columns", file=sys.stderr)
    sys.exit(1)
actual['year_end'] = pd.to_datetime(actual['year_end'])
year_label = actual['year_end'].dt.strftime('%b %Y').iloc[0]

# === Build 500m grid over wards extent ===
wards = gpd.read_file(str(WARD_SHP))
wards_m = wards.to_crs(epsg=27700)
bounds = wards_m.total_bounds  # [minx, miny, maxx, maxy]
step = 500
cells = []
minx, miny, maxx, maxy = bounds
for x in range(int(minx), int(maxx), step):
    for y in range(int(miny), int(maxy), step):
        cells.append(Polygon([(x,y),(x+step,y),(x+step,y+step),(x,y+step)]))
grid = gpd.GeoDataFrame({'geometry': cells}, crs=wards_m.crs)
grid['cell_id'] = grid.index
grid['area_km2'] = grid.geometry.area / 1e6

# === Merge counts ===
grid = grid.merge(actual[['cell_id','actual_past_year']], on='cell_id', how='left')
grid['actual_past_year'] = grid['actual_past_year'].fillna(0)

# Sanity check: print few non-zero examples
sample = grid[grid['actual_past_year']>0][['cell_id','actual_past_year']].head()
print("Sample non-zero cells:\n", sample.to_string(index=False))

# === Prepare GeoJSON ===
grid_wgs = grid.to_crs(epsg=4326)
geojson = grid_wgs.to_json()

# === Build Folium map ===
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
    legend_name=f'Total Crimes Past 12 Months (through {year_label})',
    name='500m Past-Year Heatmap'
).add_to(m)

# Overlay ward boundaries
folium.GeoJson(
    wards.to_crs(epsg=4326),
    name='Ward Boundaries',
    style_function=lambda feat: {'fillOpacity':0,'color':'black','weight':1}
).add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

# === Save map ===
m.save(str(OUT_HTML))
print(f"Map saved to {OUT_HTML}")
