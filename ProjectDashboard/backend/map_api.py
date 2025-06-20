import os
import pandas as pd
import geopandas as gpd
import json
import warnings
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
import time
import sys

# Add the project root to Python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from ProjectDashboard.backend.optimized_csv import CSVIndexManager, load_burglary_data, aggregate_by_area

# Suppress shapely warnings
warnings.filterwarnings("ignore", category=UserWarning, module="shapely")

app = Flask(__name__)
CORS(app)

# Define paths
BASE_PATH = Path(r"C:/Users/alexz/OneDrive - TU Eindhoven/CBL-London-Crime-")
ACTUAL_CSV = BASE_PATH / "data/London_burglaries_with_wards_correct_with_price.csv"
YEARLY_BURGLARIES_DIR = BASE_PATH / "data/yearly_burglaries"
FEBRUARY_2025_PREDICTIONS_CSV = BASE_PATH / "data/last_month_predictions_detailed_with_scores_and_hours.csv"
LSOA_SHP = BASE_PATH / "LSOA_boundries/LSOA_2021_EW_BFE_V10.shp"
WARD_SHP = BASE_PATH / "London-wards-2018-ESRI/London_Ward.shp"

# Flag to use yearly files (set to False to use the original file)
USE_YEARLY_FILES = True

# Global variables to store processed boundaries at different detail levels
LONDON_BOUNDARIES_HIGH = None  # LSOA boundaries for detailed view
LONDON_BOUNDARIES_MEDIUM = None  # LSOA boundaries for medium view
LONDON_BOUNDARIES_LOW = None  # Ward boundaries for overview

# Global cache for crime data by time period
CRIME_DATA_CACHE = {}

# Initialize CSV index manager for faster file access
CSV_INDEX_MANAGER = CSVIndexManager(YEARLY_BURGLARIES_DIR)

def get_cached_boundaries(detail_level="medium"):
    """Get boundaries from cache or load if not cached. Shared across all endpoints."""
    global LONDON_BOUNDARIES_HIGH, LONDON_BOUNDARIES_MEDIUM, LONDON_BOUNDARIES_LOW
    
    boundary_type = "LSOA" if detail_level in ['medium', 'high'] else "Ward"
    
    if detail_level == "high" and LONDON_BOUNDARIES_HIGH is not None:
        return LONDON_BOUNDARIES_HIGH
    elif detail_level == "medium" and LONDON_BOUNDARIES_MEDIUM is not None:
        return LONDON_BOUNDARIES_MEDIUM
    elif detail_level == "low" and LONDON_BOUNDARIES_LOW is not None:
        return LONDON_BOUNDARIES_LOW
    
    return load_london_boundaries(detail_level)

def initialize_boundaries():
    """Pre-load all boundary types and indices at startup to ensure sharing across endpoints"""
    print("Initializing boundary data...")
    
    try:
        get_cached_boundaries("low")
        get_cached_boundaries("medium") 
        get_cached_boundaries("high")
        
        # Load CSV indices for faster file access
        print("Checking CSV indices...")
        if not CSV_INDEX_MANAGER.indices:
            print("Building CSV indices for yearly files (first run)...")
            CSV_INDEX_MANAGER.build_indices(rebuild=False)
            print(f"Created indices for {len(CSV_INDEX_MANAGER.indices)} files")
        else:
            print(f"Loaded {len(CSV_INDEX_MANAGER.indices)} existing CSV indices")
        
    except Exception as e:
        print(f"Warning: Initialization failed: {e}")
        import traceback
        traceback.print_exc()

def load_london_boundaries(detail_level="medium"):
    """Load and process London boundaries with different levels of detail"""
    global LONDON_BOUNDARIES_HIGH, LONDON_BOUNDARIES_MEDIUM, LONDON_BOUNDARIES_LOW
    
    # Configure parameters based on detail level
    if detail_level == "high":
        if LONDON_BOUNDARIES_HIGH is not None:
            return LONDON_BOUNDARIES_HIGH
        shapefile_path = LSOA_SHP
        tolerance = 0.0001
        max_features = None
        boundary_type = "LSOA"
    elif detail_level == "low":
        if LONDON_BOUNDARIES_LOW is not None:
            return LONDON_BOUNDARIES_LOW
        shapefile_path = WARD_SHP
        tolerance = 0.0005
        max_features = None
        boundary_type = "Ward"
    else:  # medium (default)
        if LONDON_BOUNDARIES_MEDIUM is not None:
            return LONDON_BOUNDARIES_MEDIUM
        shapefile_path = LSOA_SHP
        tolerance = 0.0002
        max_features = None
        boundary_type = "LSOA"
    
    try:
        # Load the shapefile
        gdf = gpd.read_file(str(shapefile_path))
        
        if boundary_type == "LSOA":
            # Filter LSOA boundaries to London area using BNG coordinates
            london_bounds_bng = {
                'min_east': 503000,
                'max_east': 560000,
                'min_north': 155000,
                'max_north': 200000
            }
            
            london_gdf = gdf[
                (gdf['BNG_E'] >= london_bounds_bng['min_east']) & 
                (gdf['BNG_E'] <= london_bounds_bng['max_east']) & 
                (gdf['BNG_N'] >= london_bounds_bng['min_north']) & 
                (gdf['BNG_N'] <= london_bounds_bng['max_north'])
            ]
        else:
            london_gdf = gdf
        
        # Limit number of features for performance (if specified)
        if max_features and len(london_gdf) > max_features:
            london_gdf = london_gdf.sample(n=max_features, random_state=42)
        
        # Convert to WGS84 for the web map
        london_gdf_web = london_gdf.to_crs(epsg=4326)
        
        # Simplify geometries and remove small areas
        london_gdf_web['geometry'] = london_gdf_web.geometry.simplify(tolerance)
        
        areas = london_gdf_web.geometry.area
        min_area = areas.quantile(0.02)
        london_gdf_web = london_gdf_web[areas >= min_area]
        
        # Keep essential columns based on boundary type
        if boundary_type == "LSOA":
            essential_columns = ['geometry', 'LSOA21CD', 'LSOA21NM', 'LAD20NM']
        else:
            essential_columns = ['geometry', 'NAME', 'GSS_CODE', 'BOROUGH']
        
        available_columns = [col for col in essential_columns if col in london_gdf_web.columns]
        if available_columns:
            london_gdf_web = london_gdf_web[available_columns]
        
        # Convert to GeoJSON and cache the result
        boundaries_geojson = json.loads(london_gdf_web.to_json())
        
        if detail_level == "high":
            LONDON_BOUNDARIES_HIGH = boundaries_geojson
        elif detail_level == "low":
            LONDON_BOUNDARIES_LOW = boundaries_geojson
        else:
            LONDON_BOUNDARIES_MEDIUM = boundaries_geojson
        
        return boundaries_geojson
        
    except Exception as e:
        print(f"Error loading {boundary_type} boundaries: {e}")
        return create_fallback_boundaries()

def create_fallback_boundaries():
    """Create a simple fallback boundary structure when loading fails"""
    return {
        "type": "FeatureCollection",
        "features": []
    }
    
    return updated_boundaries, heatmap_features

def load_crime_data_for_period(csv_path, boundary_type="LSOA", year=2024, month=3):
    """Load and cache crime data for a specific time period using optimized methods"""
    # Create a cache key that includes whether we're using yearly files
    cache_key = f"{'yearly' if USE_YEARLY_FILES else 'original'}-{csv_path.name}-{boundary_type}-{year}-{month}"
    
    if cache_key in CRIME_DATA_CACHE:
        return CRIME_DATA_CACHE[cache_key]
    
    # Handle predictions file separately
    if csv_path == FEBRUARY_2025_PREDICTIONS_CSV:
        return load_prediction_data(csv_path, boundary_type, year, month, cache_key)
    
    try:
        # Check if we should use yearly files for this request
        if USE_YEARLY_FILES and csv_path == ACTUAL_CSV:
            # Get the correct file using our index manager (much faster than just assuming the filename)
            start_time = time.time()
            
            # Find the appropriate file for this year/month
            yearly_file = CSV_INDEX_MANAGER.get_file_for_date(year, month)
            
            if not yearly_file or not yearly_file.exists():
                print(f"No indexed file found for {year}-{month}, trying direct file lookup")
                # Try direct file approach as fallback
                yearly_file = YEARLY_BURGLARIES_DIR / f"london_burglaries_{year}.csv"
                
                if not yearly_file.exists():
                    print(f"Yearly file for {year} not found: {yearly_file}")
                    # Fall back to the original file if yearly file doesn't exist
                    return load_from_original_file(csv_path, boundary_type, year, month, cache_key)
            
            print(f"Using yearly file: {yearly_file} (found in {time.time() - start_time:.4f}s)")
            
            # Determine which columns to load based on boundary type
            if boundary_type == "LSOA":
                boundary_columns = ['LSOA code', 'LSOA11CD', 'LSOA21CD', 'lsoa_code', 'LSOA_code', 'Lower_Super_Output_Area']
            else:  # Ward
                boundary_columns = ['WD24CD', 'WD24NM', 'Ward_Code', 'ward_code']
            
            # Load only the columns we need with optimized loading
            # Include all possible boundary columns to ensure we get the data
            columns_to_load = ['Month'] + boundary_columns
            
            print(f"Loading data for {boundary_type} level, using columns: {columns_to_load}")
            filters = {'Month': (year, month)}
            
            # Use our optimized CSV loading function
            crime_data = load_burglary_data(
                yearly_file, 
                columns=columns_to_load, 
                filters=filters
            )
            
            if len(crime_data) == 0:
                print(f"No data found for {year}-{month} in {yearly_file}")
                CRIME_DATA_CACHE[cache_key] = ({}, 0)
                return {}, 0
                
            # Aggregate by area using our utility function
            crime_counts = aggregate_by_area(crime_data, boundary_type)
            max_value = max(crime_counts.values()) if crime_counts else 0
            
            print(f"Found {len(crime_counts)} areas with data, max value: {max_value}")
            print(f"Total processing time: {time.time() - start_time:.4f}s")
            
            CRIME_DATA_CACHE[cache_key] = (crime_counts, max_value)
            return crime_counts, max_value
        else:
            # Use the original method if yearly files are disabled
            return load_from_original_file(csv_path, boundary_type, year, month, cache_key)
        
    except Exception as e:
        print(f"Error processing crime data: {e}")
        import traceback
        traceback.print_exc()
        CRIME_DATA_CACHE[cache_key] = ({}, 0)
        return {}, 0

def load_prediction_data(csv_path, boundary_type, year, month, cache_key):
    """Handle prediction data loading and processing"""
    if not csv_path.exists():
        print(f"Prediction CSV file not found: {csv_path}")
        return {}, 0
    
    try:
        # Load prediction data
        crime_data = pd.read_csv(csv_path)
        
        # Ward level predictions - sum LSOA predictions by ward
        if boundary_type == "Ward" and "WD24CD" in crime_data.columns and "y_pred_lgb" in crime_data.columns:
            ward_predictions = crime_data.groupby("WD24CD")["y_pred_lgb"].sum().reset_index()
            
            crime_counts = {}
            for _, row in ward_predictions.iterrows():
                ward_code = str(row["WD24CD"])
                ward_pred_sum = row["y_pred_lgb"]
                crime_counts[ward_code] = round(float(ward_pred_sum), 2)
            
            max_value = max(crime_counts.values()) if crime_counts else 0
            
            CRIME_DATA_CACHE[cache_key] = (crime_counts, max_value)
            return crime_counts, max_value
        
        # LSOA-level predictions
        elif "y_pred_lgb" in crime_data.columns:
            code_columns = ['LSOA code', 'LSOA11CD', 'LSOA21CD', 'lsoa_code', 'LSOA_code', 'Lower_Super_Output_Area', 'LSOA', 'LSOAC']
            
            crime_code_column = None
            for col in code_columns:
                if col in crime_data.columns:
                    crime_code_column = col
                    break
            
            if not crime_code_column:
                print(f"Warning: No LSOA code column found in prediction data")
                print(f"Available columns: {list(crime_data.columns)}")
                CRIME_DATA_CACHE[cache_key] = ({}, 0)
                return {}, 0
            
            crime_counts = {}
            for _, row in crime_data.iterrows():
                area_code = str(row[crime_code_column])
                pred_value = row['y_pred_lgb']
                if not pd.isna(pred_value):
                    crime_counts[area_code] = round(float(pred_value), 2)
            
            max_value = max(crime_counts.values()) if crime_counts else 0
            
            CRIME_DATA_CACHE[cache_key] = (crime_counts, max_value)
            return crime_counts, max_value
        
        # Standard prediction file format not found
        print(f"Warning: Prediction file doesn't have expected format. Missing 'y_pred_lgb' column.")
        print(f"Available columns: {list(crime_data.columns)}")
        CRIME_DATA_CACHE[cache_key] = ({}, 0)
        return {}, 0
        
    except Exception as e:
        print(f"Error processing prediction data: {e}")
        import traceback
        traceback.print_exc()
        CRIME_DATA_CACHE[cache_key] = ({}, 0)
        return {}, 0

def load_from_original_file(csv_path, boundary_type, year, month, cache_key):
    """Original method to load crime data from the full CSV file with optimizations"""
    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        return {}, 0
    
    try:
        print(f"Using original file method for {year}-{month}")
        start_time = time.time()
        
        # Determine which columns to load based on boundary type
        if boundary_type == "LSOA":
            boundary_columns = ['LSOA code', 'LSOA11CD', 'LSOA21CD']
        else:  # Ward
            boundary_columns = ['WD24CD', 'WD24NM']
        
        # Create an optimized filter for the date
        columns_to_load = ['Month'] + boundary_columns
        filters = {'Month': (year, month)}
        
        # Use our optimized CSV loading function with the full file
        crime_data = load_burglary_data(
            csv_path, 
            columns=columns_to_load, 
            filters=filters
        )
        
        if len(crime_data) == 0:
            print(f"No data found for {year}-{month} in original file")
            CRIME_DATA_CACHE[cache_key] = ({}, 0)
            return {}, 0
            
        # Aggregate by area using our utility function
        crime_counts = aggregate_by_area(crime_data, boundary_type)
        max_value = max(crime_counts.values()) if crime_counts else 0
        
        print(f"Found {len(crime_counts)} areas with data in original file, max value: {max_value}")
        print(f"Original file processing time: {time.time() - start_time:.4f}s")
        
        CRIME_DATA_CACHE[cache_key] = (crime_counts, max_value)
        return crime_counts, max_value
        
    except Exception as e:
        print(f"Error processing crime data from original file: {e}")
        import traceback
        traceback.print_exc()
        CRIME_DATA_CACHE[cache_key] = ({}, 0)
        return {}, 0

def combine_boundaries_with_crime_data(boundary_geojson, crime_counts, boundary_type="LSOA"):
    """Combine pre-loaded boundaries with crime data"""
    if not boundary_geojson or 'features' not in boundary_geojson:
        return boundary_geojson, []
    
    # Determine the boundary code column
    if boundary_type == "LSOA":
        boundary_code_columns = ['LSOA21CD', 'LSOA11CD', 'lsoa_code']
    else:  # Ward
        boundary_code_columns = ['GSS_CODE', 'Ward_Code', 'NAME', 'ward_code']
    
    # Create heatmap features (areas with crime counts > 0)
    heatmap_features = []
    updated_features = []
    
    for feature in boundary_geojson['features']:
        # Find the boundary code
        boundary_code = None
        for col in boundary_code_columns:
            if col in feature['properties']:
                boundary_code = feature['properties'][col]
                break
        
        # Get crime count for this boundary
        crime_count = crime_counts.get(boundary_code, 0) if boundary_code else 0
        
        # Add crime count to feature properties
        updated_feature = {
            "type": feature["type"],
            "geometry": feature["geometry"],
            "properties": {
                **feature["properties"],
                "crime_count": crime_count
            }
        }
        updated_features.append(updated_feature)
        
        # Add to heatmap if has crimes
        if crime_count > 0:
            heatmap_feature = {
                "type": "Feature",
                "geometry": feature['geometry'],
                "properties": {
                    "actual_past_year": crime_count,
                    "crime_count": crime_count,
                    "area_type": boundary_type,
                    "area_code": boundary_code or 'Unknown'
                }
            }
            heatmap_features.append(heatmap_feature)
    
    # Create GeoJSON wrapper for updated features
    updated_boundaries = {
        "type": "FeatureCollection",
        "features": updated_features
    }
    
    return updated_boundaries, heatmap_features

@app.route('/api/past-burglaries', methods=['GET'])
def past_burglaries():
    """API endpoint for past burglary data with optimized boundary/crime data separation"""
    try:
        # Get detail level from query parameters (default: medium)
        detail_level = request.args.get('detail', 'medium')
        if detail_level not in ['low', 'medium', 'high']:
            detail_level = 'medium'
        
        # Get year and month parameters (default: March 2024)
        year = int(request.args.get('year', 2024))
        month = int(request.args.get('month', 3))
        
        # Allow override of the USE_YEARLY_FILES setting through query param
        global USE_YEARLY_FILES
        use_yearly = request.args.get('use_yearly_files', None)
        original_setting = USE_YEARLY_FILES
        
        if use_yearly is not None:
            USE_YEARLY_FILES = use_yearly.lower() in ['true', '1', 'yes']
        
        # Step 1: Load boundaries (cached after first load) - respect the detail level
        london_boundaries = get_cached_boundaries(detail_level)
        
        if not london_boundaries or 'features' not in london_boundaries:
            # Restore original setting
            USE_YEARLY_FILES = original_setting
            return jsonify({"error": "Boundary data not available"}), 500
        
        # Step 2: Load crime data for the specific time period (cached by time period)
        boundary_type = "LSOA" if detail_level in ['medium', 'high'] else "Ward"
        crime_counts, max_value = load_crime_data_for_period(
            ACTUAL_CSV, boundary_type, year, month
        )
        
        # Restore original setting
        USE_YEARLY_FILES = original_setting
        
        # Step 3: Combine boundaries with crime data
        updated_boundaries, heatmap_features = combine_boundaries_with_crime_data(
            london_boundaries, crime_counts, boundary_type
        )
        
        # Generate time label based on actual parameters
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        
        # Check if we're displaying February 2025
        is_feb_2025 = (year == 2025 and month == 2)
        
        # Set time label
        if is_feb_2025:
            time_label = "February 2025 Burglaries"
        else:
            time_label = f"{month_names[month - 1]} {year} Burglaries"
        
        # Update heatmap features to include data type flag
        for feature in heatmap_features:
            # Add a flag to indicate if this is February 2025 data (special case)
            feature['properties']['is_prediction'] = is_feb_2025
            
            # Format data based on whether it's February 2025 or not
            if 'crime_count' in feature['properties']:
                if is_feb_2025:
                    # For February 2025, show with 2 decimal places (like predictions)
                    feature['properties']['crime_count'] = round(float(feature['properties']['crime_count']), 2)
                    feature['properties']['display_value'] = feature['properties']['crime_count']
                else:
                    # For historical data, store as integers
                    feature['properties']['crime_count'] = int(feature['properties']['crime_count'])
                    feature['properties']['display_value'] = feature['properties']['crime_count']
        
        response_data = {
            "features": {
                "type": "FeatureCollection",
                "features": heatmap_features
            },
            "maxValue": float(max_value) if max_value > 0 else 30.0,
            "timeLabel": time_label,
            "wardBoundaries": updated_boundaries,
            "detailLevel": detail_level,
            "boundaryCount": len(updated_boundaries.get('features', [])),
            "isPrediction": is_feb_2025  # Global flag for frontend - true only for Feb 2025
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in past_burglaries: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/predicted-burglaries', methods=['GET'])
def predicted_burglaries():
    """API endpoint for predicted burglary data with optimized boundary/crime data separation"""
    try:
        # Get detail level from query parameters (default: medium)
        detail_level = request.args.get('detail', 'medium')
        if detail_level not in ['low', 'medium', 'high']:
            detail_level = 'medium'
        
        # Get year and month parameters (default: March 2024)
        year = int(request.args.get('year', 2024))
        month = int(request.args.get('month', 3))
        
        # Allow override of the USE_YEARLY_FILES setting through query param
        global USE_YEARLY_FILES
        use_yearly = request.args.get('use_yearly_files', None)
        original_setting = USE_YEARLY_FILES
        
        if use_yearly is not None:
            USE_YEARLY_FILES = use_yearly.lower() in ['true', '1', 'yes']
        
        # Step 1: Load boundaries (cached after first load) - respect the detail level
        boundaries = get_cached_boundaries(detail_level)
        
        if not boundaries or 'features' not in boundaries:
            # Restore original setting
            USE_YEARLY_FILES = original_setting
            return jsonify({"error": "Boundary data not available"}), 500
        
        # Step 2: Determine boundary type and load prediction data
        boundary_type = "LSOA" if detail_level in ['medium', 'high'] else "Ward"
        
        # Always use February 2025 for predictions
        is_feb_2025 = True
        prediction_year = 2025
        prediction_month = 2
        
        if FEBRUARY_2025_PREDICTIONS_CSV.exists():
            # Load crime data appropriate for the boundary type
            # For Ward level, this will sum LSOA predictions by ward
            prediction_counts, max_value = load_crime_data_for_period(
                FEBRUARY_2025_PREDICTIONS_CSV, boundary_type, prediction_year, prediction_month
            )
        else:
            return jsonify({"error": "February 2025 predictions file not found"}), 404
        
        # Step 3: Combine boundaries with prediction data
        updated_boundaries, heatmap_features = combine_boundaries_with_crime_data(
            boundaries, prediction_counts, boundary_type
        )
        
        # Step 4: Convert crime_count to prediction format for frontend compatibility
        prediction_heatmap_features = []
        for feature in heatmap_features:
            prediction_feature = {
                "type": "Feature",
                "geometry": feature['geometry'],
                "properties": {
                    "prediction": feature['properties']['crime_count'],
                    "pred_per_km2": feature['properties']['crime_count'],
                    "area_type": boundary_type,
                    "area_code": feature['properties']['area_code'],
                    "is_prediction": True
                }
            }
            
            # Add boundary-specific properties
            if boundary_type == "Ward":
                prediction_feature['properties']['ward'] = feature['properties']['area_code']
            else:
                prediction_feature['properties']['lsoa'] = feature['properties']['area_code']
                
            # Add name property if available in original feature
            if 'name' in feature['properties']:
                prediction_feature['properties']['name'] = feature['properties']['name']
                
            # Format prediction values to 2 decimal places
            raw_value = prediction_feature['properties']['prediction']
            formatted_value = round(float(raw_value), 2)
            prediction_feature['properties']['prediction'] = formatted_value
            prediction_feature['properties']['pred_per_km2'] = formatted_value
            prediction_feature['properties']['display_value'] = formatted_value
            
            prediction_heatmap_features.append(prediction_feature)
        
        # Set time label for February 2025 predictions
        time_label = "February 2025 Predictions"
        
        response_data = {
            "features": {
                "type": "FeatureCollection",
                "features": prediction_heatmap_features
            },
            "maxValue": float(max_value) if max_value > 0 else 40.0,
            "timeLabel": time_label,
            "wardBoundaries": updated_boundaries,
            "detailLevel": detail_level,
            "boundaryCount": len(updated_boundaries.get('features', [])),
            "isPrediction": True,  # Global flag for frontend
            "dataSource": "ML Prediction Model"
        }
        
        # Restore original setting
        USE_YEARLY_FILES = original_setting
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in predicted_burglaries: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/duty-sheet')
def get_duty_sheet():
    """Get duty sheet data with hours per week and tier classification based on score2."""
    try:
        # Read the predictions file
        df = pd.read_csv(FEBRUARY_2025_PREDICTIONS_CSV)

        # Fill NaN values with 0 to ensure valid JSON
        df = df.fillna(0)
        
        # Check if required columns exist
        if 'LSOA code' not in df.columns:
            return jsonify({"error": "Required column 'LSOA code' not found"}), 500

        # Determine tier based on predicted value (y_pred_lgb), not score2
        def get_tier(pred):
            if pred > 3.6:
                return "Tier 1"
            elif pred > 2.6:
                return "Tier 2"
            else:
                return "Tier 3"
        df['tier'] = df['y_pred_lgb'].apply(get_tier)
        # Sort by hours per week in descending order
        df = df.sort_values('hours', ascending=False)

        # Format the response
        result = []
        for _, row in df.iterrows():
            result.append({
                'lsoa_code': row['LSOA code'],
                'lsoa_name': row['lsoa_name'],
                'ward_code': row['WD24CD'],  # Add ward code
                'ward_name': row['WD24NM'],  # Rename for clarity
                'hours_per_week': round(float(row['hours']), 2),
                'tier': row['tier']
            })
        return jsonify({"duty_sheet": result})

    except Exception as e:
        print(f"Error in duty sheet endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Initialize boundaries at startup for optimal sharing
    initialize_boundaries()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 