import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import Fullscreen
import re
from fuzzywuzzy import process, fuzz


def normalize(name):
    """Normalize ward names for consistent matching"""
    if pd.isna(name):
        return ""
    name = str(name).lower()
    name = re.sub(r"[\u2018\u2019'']", "'", name)  # normalize apostrophes
    name = re.sub(r"[&]", "and", name)
    name = re.sub(r"[^a-z0-9 ]", "", name)  # remove punctuation
    name = re.sub(r"\s+", " ", name).strip()  # trim and normalize whitespace
    return name


# Load known incorrect matches to be excluded
def load_exclusions():
    """Define known incorrect matches to be excluded"""
    # Format: {"shapefile_name_clean": ["prediction_name_clean_to_exclude", ...]}
    return {
        "eltham south": ["east ham south"],
        "eltham north": ["feltham north"],
        "eltham west": ["feltham west"],
        "bickley": ["brockley"],
        "harefield": ["thamesfield"],
        "west ruislip": ["south ruislip"],
        "wealdstone": ["headstone"],
        "earlsfield": ["chelsfield"],
        "sutton west": ["heston west"],
        "cheap": ["cheam"],
        "greenwich west": ["west green"],
        "southgate green": ["southall green"]
    }


# Define manual mappings for problematic wards
def load_manual_mappings():
    """Define manual mappings for known problematic wards"""
    # Format: {"shapefile_name_clean": "prediction_name_clean"}
    return {
        "eltham south": "eltham south",
        "eltham north": "eltham north",
        "eltham west": "eltham west",
        "bickley": "bickley",
        "harefield": "harefield",
        "west ruislip": "west ruislip",
        "wealdstone": "wealdstone",
        "earlsfield": "earlsfield",
        "sutton west": "sutton west",
        "cheap": "cheap",
        "greenwich west": "greenwich west",
        "southgate green": "southgate green"
        # Add more manual mappings as needed
    }


# === Load data ===

# Load prediction results
preds = pd.read_csv("outputs/next_month_predictions.csv")
prediction_month = pd.to_datetime(preds["Month"].iloc[0]).strftime("%B %Y")

# Load shapefile for London wards
wards = gpd.read_file("London-wards-2018_ESRI/London_Ward.shp")

# Create a copy of the original ward names for reference
wards["original_NAME"] = wards["NAME"].copy()
preds["original_ward"] = preds["ward"].copy()

# Clean ward names for matching - crucial for consistent matching
preds["ward_clean"] = preds["ward"].apply(normalize)
wards["NAME_clean"] = wards["NAME"].apply(normalize)

# Load exclusions and manual mappings
exclusions = load_exclusions()
manual_mappings = load_manual_mappings()

# === IMPROVED MATCHING METHOD ===

# First try direct matching on clean names
print("Attempting direct matching first...")
merged = wards.merge(preds, left_on="NAME_clean", right_on="ward_clean", how="left")

# Check exact match results
matched_count = merged["ward_clean"].notna().sum()
print(f"Direct matching succeeded for {matched_count} out of {len(wards)} wards")

# Try manual mappings for those that have them
print("\nApplying manual mappings...")
manual_match_count = 0

# Create a mask for unmatched rows
unmatched_mask = pd.isna(merged["ward_clean"])
unmatched_wards = wards[unmatched_mask].copy()

# Apply manual mappings if available
for idx, ward in unmatched_wards.iterrows():
    ward_name_clean = ward["NAME_clean"]
    if ward_name_clean in manual_mappings:
        mapping = manual_mappings[ward_name_clean]
        matching_preds = preds[preds["ward_clean"] == mapping]

        if not matching_preds.empty:
            pred_row = matching_preds.iloc[0]
            # Find the corresponding row in the merged DataFrame
            merged_idx = merged.index[merged["NAME_clean"] == ward_name_clean].tolist()

            if merged_idx:
                # Update all columns from the prediction dataframe
                for col in preds.columns:
                    merged.at[merged_idx[0], col] = pred_row[col]

                print(f"Manual mapped: '{ward['NAME']}' -> '{pred_row['ward']}'")
                manual_match_count += 1

print(f"Applied {manual_match_count} manual mappings")

# For remaining unmatched wards, try fuzzy matching
unmatched_mask = pd.isna(merged["ward_clean"])
unmatched_wards = wards[unmatched_mask].copy()

if len(unmatched_wards) > 0:
    print(f"\nAttempting fuzzy matching for {len(unmatched_wards)} remaining wards...")

    # Create a map to store fuzzy matches
    fuzzy_matches = {}

    # Get list of all prediction ward names for matching against
    pred_ward_names = list(preds["ward_clean"].unique())

    # For each unmatched ward, find the best fuzzy match
    for _, ward in unmatched_wards.iterrows():
        ward_name = ward["NAME_clean"]
        if ward_name:  # Only process non-empty names
            # Check if this ward has exclusions
            excluded_matches = exclusions.get(ward_name, [])

            # Find best match with cutoff score
            matches = process.extract(ward_name, pred_ward_names,
                                      limit=5,  # Get more candidates to filter
                                      scorer=fuzz.token_sort_ratio)

            # Filter out excluded matches
            valid_matches = [(match, score) for match, score in matches
                             if match not in excluded_matches]

            if valid_matches and valid_matches[0][1] >= 85:  # Increased threshold
                best_match, score = valid_matches[0]
                fuzzy_matches[ward_name] = best_match
                print(
                    f"Fuzzy matched: '{ward['NAME']}' -> '{preds[preds['ward_clean'] == best_match]['ward'].iloc[0]}' (score: {score})")

    print(f"Found {len(fuzzy_matches)} fuzzy matches above threshold score of 85")

    if fuzzy_matches:
        # Apply fuzzy mapping to all wards
        for ward_name, match in fuzzy_matches.items():
            # Find all prediction rows with this cleaned name
            matching_preds = preds[preds["ward_clean"] == match]
            if not matching_preds.empty:
                pred_row = matching_preds.iloc[0]
                # Find the corresponding row in the merged DataFrame
                merged_idx = merged.index[merged["NAME_clean"] == ward_name].tolist()

                if merged_idx:
                    # Update all columns from the prediction dataframe
                    for col in preds.columns:
                        merged.at[merged_idx[0], col] = pred_row[col]

# Remove rows that still have no predictions
matched_before = len(merged)
merged = merged.dropna(subset=["prediction"])
print(f"\nFinal result: {len(merged)} of {len(wards)} wards matched ({len(wards) - len(merged)} unmatched)")

# Reproject for folium
merged = merged.to_crs(epsg=4326)
merged_json = merged.to_json()

# Identify wards that are still unmatched
still_unmatched = wards[~wards["NAME"].isin(merged["NAME"])]

# Save unmatched wards for inspection
if len(still_unmatched) > 0:
    still_unmatched.to_csv("outputs/unmatched_wards.csv", index=False)
    print(f"⚠️ {len(still_unmatched)} wards could not be matched, details saved to 'outputs/unmatched_wards.csv'")

    # Create a CSV with all unmatched wards for easier manual mapping
    unmatched_for_mapping = pd.DataFrame({
        "shapefile_ward": still_unmatched["NAME"],
        "shapefile_ward_clean": still_unmatched["NAME_clean"],
        "manual_mapping": ""  # Empty column for users to fill in
    })
    unmatched_for_mapping.to_csv("outputs/manual_mapping_template.csv", index=False)
    print("✔ Manual mapping template created at 'outputs/manual_mapping_template.csv'")

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

# Add layer with transparency to show unmatched wards
if len(still_unmatched) > 0:
    unmatched_json = still_unmatched.to_crs(epsg=4326).to_json()
    folium.GeoJson(
        unmatched_json,
        name="Unmatched Wards",
        style_function=lambda x: {
            'fillColor': 'gray',
            'color': 'red',
            'weight': 1,
            'fillOpacity': 0.3
        },
        tooltip=folium.GeoJsonTooltip(fields=["NAME"], aliases=["Unmatched Ward:"])
    ).add_to(m)

# Tooltip layer: show ward name on hover
tooltip_layer = folium.GeoJson(
    merged_json,
    name="Ward Labels (hover)",
    tooltip=folium.GeoJsonTooltip(fields=["NAME", "ward"],
                                  aliases=["Ward (shapefile):", "Ward (predictions):"]),
)
tooltip_layer.add_to(m)

# Popup marker layer: show predicted value on click
popup_group = folium.FeatureGroup(name="Predicted Counts (clickable)")
for _, row in merged.iterrows():
    centroid = row["geometry"].centroid
    popup_text = f"""<b>{row['NAME']}</b><br>
                   Prediction dataset: {row['ward']}<br>
                   Predicted burglaries: {row['prediction']:.1f}"""
    folium.Marker(
        location=[centroid.y, centroid.x],
        popup=popup_text,
        icon=folium.Icon(icon="info-sign", color="blue"),
    ).add_to(popup_group)
popup_group.add_to(m)

# Title box with status display
title_html = f"""
     <h4 style="position:fixed; top:10px; left:10px; z-index:9999; background-color:white;
     padding:10px; border:2px solid gray;">London Residential Burglary Forecast – {prediction_month}</h4>
     <div style="position:fixed; bottom:10px; left:10px; z-index:9999; background-color:white;
     padding:10px; border:2px solid gray;">
     <p>Matched: {len(merged)} wards | Unmatched: {len(still_unmatched)} wards</p>
     </div>
"""
m.get_root().html.add_child(folium.Element(title_html))

# Enable layer control panel
folium.LayerControl(collapsed=False).add_to(m)

# Save to file
m.save("outputs/london_burglary_prediction_map.html")
print(f"✔ Interactive map saved with {len(merged)} matched wards and {len(still_unmatched)} unmatched wards.")

# Generate a CSV to help manually map the remaining wards
if len(still_unmatched) > 0:
    # Get remaining prediction ward names
    remaining_pred_wards = preds[~preds["ward_clean"].isin(merged["ward_clean"])]

    # For each unmatched ward, suggest top 3 potential matches
    match_suggestions = []
    for _, ward in still_unmatched.iterrows():
        ward_name = ward["NAME_clean"]
        if ward_name and len(remaining_pred_wards) > 0:
            matches = process.extract(ward_name,
                                      list(remaining_pred_wards["ward_clean"]),
                                      limit=3,
                                      scorer=fuzz.token_sort_ratio)

            for match_name, score in matches:
                # Find all prediction rows with this cleaned name
                matching_preds = remaining_pred_wards[remaining_pred_wards["ward_clean"] == match_name]
                if not matching_preds.empty:
                    match_row = matching_preds.iloc[0]
                    match_suggestions.append({
                        "shapefile_ward": ward["NAME"],
                        "shapefile_ward_clean": ward_name,
                        "prediction_ward": match_row["ward"],
                        "prediction_ward_clean": match_name,
                        "match_score": score,
                        "prediction_value": match_row["prediction"]
                    })

    if match_suggestions:
        suggestions_df = pd.DataFrame(match_suggestions)
        suggestions_df.to_csv("outputs/ward_match_suggestions.csv", index=False)
        print("✔ Matching suggestions saved to 'outputs/ward_match_suggestions.csv'")

# Save the final matching reference
match_reference = merged[["NAME", "ward", "NAME_clean", "ward_clean", "prediction"]].copy()
match_reference.to_csv("outputs/ward_matching_reference.csv", index=False)
print("✔ Final matching reference saved to 'outputs/ward_matching_reference.csv'")

# Save prediction statistics
if len(merged) > 0:
    stats = {
        "Total wards": len(wards),
        "Matched wards": len(merged),
        "Unmatched wards": len(still_unmatched),
        "Matching percentage": f"{(len(merged) / len(wards) * 100):.1f}%",
        "Average prediction": f"{merged['prediction'].mean():.2f}",
        "Max prediction": f"{merged['prediction'].max():.2f}",
        "Min prediction": f"{merged['prediction'].min():.2f}"
    }

    with open("outputs/prediction_stats.txt", "w") as f:
        for key, value in stats.items():
            f.write(f"{key}: {value}\n")

    print("✔ Prediction statistics saved to 'outputs/prediction_stats.txt'")