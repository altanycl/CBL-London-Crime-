import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import Fullscreen

# === Normalization function for ward names ===
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

# === Load data ===

# Load prediction results
preds = pd.read_csv("outputs/next_month_predictions.csv")
prediction_month = pd.to_datetime(preds["Month"].iloc[0]).strftime("%B %Y")

# Load shapefile for London wards
wards = gpd.read_file("London-wards-2018_ESRI/London_Ward.shp")

# Clean ward names for matching
preds["ward_clean"] = preds["ward"].apply(normalize)
wards["NAME_clean"] = wards["NAME"].apply(normalize)

# Merge datasets on cleaned names
merged = wards.merge(preds, left_on="NAME_clean", right_on="ward_clean", how="left")
merged = merged.dropna(subset=["prediction"])  # Keep only matched predictions

# Reproject for folium
merged = merged.to_crs(epsg=4326)
merged_json = merged.to_json()

# === Create interactive map ===

m = folium.Map(location=[51.5074, -0.1278], zoom_start=10, tiles="cartodbpositron")
Fullscreen().add_to(m)

# Choropleth: prediction intensity
choropleth = folium.Choropleth(
    geo_data=merged_json,
    data=merged,
    columns=["NAME", "prediction"],
    key_on="feature.properties.NAME",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name=f"Predicted Residential Burglaries – {prediction_month}",
    name="Prediction Intensity",
)
choropleth.add_to(m)

# Tooltip layer: show ward name on hover
tooltip_layer = folium.GeoJson(
    merged_json,
    name="Ward Labels (hover)",
    tooltip=folium.GeoJsonTooltip(fields=["NAME"], aliases=["Ward:"]),
)
tooltip_layer.add_to(m)

# Popup marker layer: show predicted value on click
popup_group = folium.FeatureGroup(name="Predicted Counts (clickable)")
for _, row in merged.iterrows():
    centroid = row["geometry"].centroid
    popup_text = f"<b>{row['NAME']}</b><br>Predicted burglaries: {row['prediction']:.1f}"
    folium.Marker(
        location=[centroid.y, centroid.x],
        popup=popup_text,
        icon=folium.Icon(icon="info-sign", color="blue"),
    ).add_to(popup_group)
popup_group.add_to(m)

# Title box at top-left
title_html = f"""
     <h4 style="position:fixed; top:10px; left:10px; z-index:9999; background-color:white;
     padding:10px; border:2px solid gray;">London Residential Burglary Forecast – {prediction_month}</h4>
"""
m.get_root().html.add_child(folium.Element(title_html))

# Enable layer control panel
folium.LayerControl(collapsed=False).add_to(m)

# Save to file
m.save("outputs/london_burglary_prediction_map.html")
print("✔ Interactive map saved with toggle layers.")

# Optional: Show which wards still failed to merge
all_cleaned = wards[["NAME", "NAME_clean"]].copy()
missing = all_cleaned[~all_cleaned["NAME_clean"].isin(merged["NAME_clean"])]
# print("⚠️ Wards still missing after normalization:", missing["NAME"].tolist())

import pandas as pd
preds = pd.read_csv("outputs/next_month_predictions.csv")
print(sorted(preds["ward"].unique()))