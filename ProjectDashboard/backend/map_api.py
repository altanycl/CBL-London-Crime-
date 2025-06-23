import os
<<<<<<< HEAD
import sys
import pandas as pd
import geopandas as gpd
import json
import networkx as nx
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
import random
from shapely.geometry import Point, Polygon
import math  # Import math for trig functions
import warnings
=======
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
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb

# Suppress shapely warnings
warnings.filterwarnings("ignore", category=UserWarning, module="shapely")

app = Flask(__name__)
CORS(app)

<<<<<<< HEAD
# Get the project root directory
ROOT_DIR = Path(__file__).resolve().parent.parent

# Define paths
OUTPUTS_DIR = ROOT_DIR / "outputs"
ACTUAL_CSV = OUTPUTS_DIR / "actual_past_year_500m.csv"
PREDICTIONS_CSV = OUTPUTS_DIR / "next_month_predictions.csv"
LSOA_GRAPH = ROOT_DIR / "london_lsoa_graph.gexf"
LSOA_SHP = ROOT_DIR / "LSOA_boundries" / "LSOA_2021_EW_BFE_V10.shp"

# Global variable to store node positions so they're consistent across API calls
NODE_POSITIONS = {}
# Global variable to store the LSOA boundaries
LSOA_BOUNDARIES = None

def load_lsoa_boundaries():
    """Load LSOA boundaries from shapefile"""
    global LSOA_BOUNDARIES, NODE_POSITIONS
    
    # If we already loaded the boundaries, return them
    if LSOA_BOUNDARIES is not None:
        print("Using cached LSOA boundaries")
        return LSOA_BOUNDARIES, NODE_POSITIONS
    
    try:
        print(f"Loading LSOA shapefile from {LSOA_SHP}")
        # Load the shapefile
        lsoas = gpd.read_file(str(LSOA_SHP))
        print(f"Loaded {len(lsoas)} LSOA areas")
        
        # Filter by the approx. London bounding box in degrees
        # West = -0.5103, East = +0.3340
        # South = 51.2868, North = 51.6919
        london_lsoas = lsoas[
            (lsoas["LONG"] >= -0.5103) &
            (lsoas["LONG"] <= 0.3340) &
            (lsoas["LAT"] >= 51.2868) &
            (lsoas["LAT"] <= 51.6919)
        ].copy()
        
        print(f"Filtered to {len(london_lsoas)} London LSOA areas")
        
        # Convert to WGS84 for web mapping
        london_lsoas_wgs84 = london_lsoas.to_crs(epsg=4326)
        
        # Extract centroids for node positions
        pos = {}
        for idx, row in london_lsoas_wgs84.iterrows():
            # Use the centroid of each LSOA as its position
            centroid = row.geometry.centroid
            pos[idx] = (centroid.x, centroid.y)
        
        # Store the positions globally
        NODE_POSITIONS = pos
        
        # Convert to GeoJSON
        geojson = json.loads(london_lsoas_wgs84.to_json())
        
        # Store the boundaries globally
        LSOA_BOUNDARIES = geojson
        
        return geojson, pos
    except Exception as e:
        print(f"Error loading LSOA shapefile: {e}", file=sys.stderr)
        return create_london_lsoa_boundaries(), NODE_POSITIONS

def create_london_lsoa_boundaries():
    """Create simplified London LSOA boundaries"""
    global NODE_POSITIONS
    
    print("Creating simplified London LSOA boundaries")
    
    # London center
    center_lat, center_lon = 51.5074, -0.1278
    
    # Create a grid of hexagonal LSOAs covering London
    features = []
    
    # Set a fixed random seed for reproducibility
    random.seed(42)
    
    # Create positions if they don't exist
    if not NODE_POSITIONS:
        pos = {}
        # Create a grid of positions
        rows, cols = 20, 20
        for i in range(rows):
            for j in range(cols):
                # Calculate position in a grid
                x = center_lon + (j - cols/2) * 0.01
                y = center_lat + (i - rows/2) * 0.01
                
                # Add some jitter to make it look more natural
                jitter_x = random.uniform(-0.001, 0.001)
                jitter_y = random.uniform(-0.001, 0.001)
                
                pos[i*cols + j] = (x + jitter_x, y + jitter_y)
        
        NODE_POSITIONS = pos
    else:
        pos = NODE_POSITIONS
    
    # Create polygon features
    for node_id, (x, y) in pos.items():
        # Create a hexagon instead of a square for more natural look
        # Size varies slightly to make it look more natural
        size = 0.005 * (0.8 + 0.4 * random.random())
        
        # Create a polygon with 6-8 sides (hexagon to octagon)
        sides = random.randint(6, 8)
        points = []
        for i in range(sides):
            angle = 2 * math.pi * i / sides
            # Vary the radius slightly for each point
            radius = size * (0.9 + 0.2 * random.random())
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            points.append([px, py])
        
        # Close the polygon
        points.append(points[0])
        
        # Create a feature for this LSOA
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [points]
            },
            "properties": {
                "LSOA21CD": f"E01{node_id:05d}",
                "LSOA21NM": f"London LSOA {node_id}",
                "LAD20NM": "London Borough",
                "node_id": node_id
            }
        })
    
    return {
        "type": "FeatureCollection",
        "features": features
    }

def fallback_to_graph():
    """Fallback to using the graph if shapefile fails"""
    global NODE_POSITIONS
    
    try:
        # Load the graph
        G = nx.read_gexf(str(LSOA_GRAPH))
        print(f"Falling back to graph with {len(G.nodes())} nodes and {len(G.edges())} edges")
        
        # Create a visualization of the graph
        features = []
        center_lat, center_lon = 51.5074, -0.1278  # London center
        
        # If we don't have node positions yet, create them
        if not NODE_POSITIONS:
            # Create a force-directed layout for visualization
            pos = {}
            nodes = list(G.nodes())
            n = len(nodes)
            
            # Use a deterministic seed for reproducibility
            random.seed(42)
            
            # Create a circular layout
            radius = 0.1  # About 10km at London's latitude
            for i, node in enumerate(nodes):
                angle = 2 * 3.14159 * i / n
                x = center_lon + radius * math.cos(angle)
                y = center_lat + radius * math.sin(angle)
                pos[node] = (x, y)
                
                # Add some jitter to avoid perfect circle
                jitter_x = random.uniform(-0.005, 0.005)
                jitter_y = random.uniform(-0.005, 0.005)
                pos[node] = (x + jitter_x, y + jitter_y)
            
            # Store the positions globally
            NODE_POSITIONS = pos
        else:
            pos = NODE_POSITIONS
        
        # Create polygon features for each LSOA
        for node in G.nodes():
            if node in pos:
                x, y = pos[node]
                size = 0.005  # Roughly 500m at London's latitude
                
                # Create a hexagon instead of a square for more natural look
                hex_points = []
                for i in range(6):
                    angle = 2 * 3.14159 * i / 6
                    hex_x = x + size * math.cos(angle)
                    hex_y = y + size * math.sin(angle)
                    hex_points.append([hex_x, hex_y])
                
                # Close the polygon
                hex_points.append(hex_points[0])
                
                # Get LSOA code from node attributes
                lsoa_code = G.nodes[node].get('lsoa_code', f"LSOA_{node}")
                
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [hex_points]
                    },
                    "properties": {
                        "LSOA21CD": lsoa_code,
                        "LSOA21NM": f"LSOA {node}",
                        "node_id": node
                    }
                })
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    except Exception as e:
        print(f"Error in fallback to graph: {e}", file=sys.stderr)
        return create_mock_lsoa_boundaries()

def create_mock_lsoa_boundaries():
    """Create mock LSOA boundaries if all else fails"""
    global NODE_POSITIONS
    
    print("Creating mock LSOA boundaries as last resort")
    features = []
    center_lat, center_lon = 51.5074, -0.1278
    
    # If we don't have node positions yet, create them
    if not NODE_POSITIONS:
        # Create a grid of mock LSOAs with consistent positions
        pos = {}
        for i in range(20):
            for j in range(20):
                node_id = i * 20 + j
                x = center_lon + (i - 10) * 0.01
                y = center_lat + (j - 10) * 0.01
                pos[node_id] = (x, y)
        
        # Store globally
        NODE_POSITIONS = pos
    else:
        pos = NODE_POSITIONS
    
    # Create features using the positions
    for node_id, (x, y) in pos.items():
        size = 0.005
        
        coords = [
            [x - size, y - size],
            [x + size, y - size],
            [x + size, y + size],
            [x - size, y + size],
            [x - size, y - size]
        ]
        
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            },
            "properties": {
                "LSOA21CD": f"E01{node_id:05d}",
                "LSOA21NM": f"Mock LSOA {node_id}",
                "node_id": node_id
            }
        })
    
    return {
        "type": "FeatureCollection",
        "features": features
    }

@app.route('/api/past-burglaries', methods=['GET'])
def past_burglaries():
    try:
        # Read the actual past year data
        actual_data = pd.read_csv(ACTUAL_CSV)
        
        # Load LSOA boundaries and node positions from shapefile
        lsoa_boundaries, node_positions = load_lsoa_boundaries()
        
        # Convert to GeoJSON using the node positions from the shapefile
        grid_cells = []
        max_value = actual_data['actual_past_year'].max()
        
        # Get a list of node IDs from the positions dictionary
        node_ids = list(node_positions.keys())
        
        for _, row in actual_data.iterrows():
            cell_id = row['cell_id']
            value = row['actual_past_year']
            
            # Use node positions from the shapefile instead of random points
            # Map the cell_id to a node ID (modulo the number of nodes)
            node_idx = cell_id % len(node_ids) if node_ids else 0
            node_id = node_ids[node_idx] if node_ids else 0
            
            if node_id in node_positions:
                center_lon, center_lat = node_positions[node_id]
                
                # Create a simple square cell around this position
                size = 0.003  # Smaller than the LSOA polygons
                coords = [
                    [center_lon - size, center_lat - size],
                    [center_lon + size, center_lat - size],
                    [center_lon + size, center_lat + size],
                    [center_lon - size, center_lat + size],
                    [center_lon - size, center_lat - size]
                ]
                
                grid_cells.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [coords]
                    },
                    "properties": {
                        "cell_id": int(cell_id),
                        "actual_past_year": float(value),
                        "area_km2": 0.25,  # 500m x 500m = 0.25 km²
                        "node_id": str(node_id)  # Include the node ID for reference
                    }
                })
        
        # Get time label from data
        time_label = pd.to_datetime(actual_data['year_end'].iloc[0]).strftime('%b %Y') if 'year_end' in actual_data.columns else 'Past Year'
        
        return jsonify({
            "features": {
                "type": "FeatureCollection",
                "features": grid_cells
            },
            "maxValue": float(max_value),
            "timeLabel": time_label,
            "wardBoundaries": lsoa_boundaries  # We keep the key name for compatibility
        })
    except Exception as e:
        print(f"Error in past_burglaries: {e}", file=sys.stderr)
=======
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
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
        return jsonify({"error": str(e)}), 500

@app.route('/api/predicted-burglaries', methods=['GET'])
def predicted_burglaries():
<<<<<<< HEAD
    try:
        # Load LSOA boundaries and node positions from shapefile
        lsoa_boundaries, node_positions = load_lsoa_boundaries()
        
        # Read the prediction data
        if PREDICTIONS_CSV.exists():
            pred_data = pd.read_csv(PREDICTIONS_CSV)
            
            # Convert to GeoJSON using the node positions from the shapefile
            grid_cells = []
            max_value = pred_data['prediction'].max() if 'prediction' in pred_data.columns else 30
            
            # Get a list of node IDs from the positions dictionary
            node_ids = list(node_positions.keys())
            
            for _, row in pred_data.iterrows():
                # Map each row to a node in the shapefile
                node_idx = row.name % len(node_ids) if node_ids else 0
                node_id = node_ids[node_idx] if node_ids else 0
                
                if node_id in node_positions:
                    center_lon, center_lat = node_positions[node_id]
                    
                    # Create a simple square cell around this position
                    size = 0.003  # Smaller than the LSOA polygons
                    coords = [
                        [center_lon - size, center_lat - size],
                        [center_lon + size, center_lat - size],
                        [center_lon + size, center_lat + size],
                        [center_lon - size, center_lat + size],
                        [center_lon - size, center_lat - size]
                    ]
                    
                    # Get LSOA code from the shapefile if available
                    lsoa_code = row.get('LSOA21CD', f"LSOA_{node_id}")
                    pred_value = row.get('prediction', random.randint(1, 30))
                    
                    grid_cells.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [coords]
                        },
                        "properties": {
                            "cell_id": int(row.name),
                            "pred_per_km2": float(pred_value),
                            "area_km2": 0.25,  # 500m x 500m = 0.25 km²
                            "LSOA21CD": lsoa_code,
                            "node_id": str(node_id)  # Include the node ID for reference
                        }
                    })
            
            # Get time label from data
            time_label = pd.to_datetime(pred_data['Month'].iloc[0]).strftime('%b %Y') if 'Month' in pred_data.columns else 'Next Month'
            
            return jsonify({
                "features": {
                    "type": "FeatureCollection",
                    "features": grid_cells
                },
                "maxValue": float(max_value),
                "timeLabel": time_label,
                "wardBoundaries": lsoa_boundaries  # We keep the key name for compatibility
            })
        else:
            # If prediction file doesn't exist, return mock data
            return jsonify({
                "features": {
                    "type": "FeatureCollection",
                    "features": []
                },
                "maxValue": 30,
                "timeLabel": "Next Month (Mock Data)",
                "wardBoundaries": lsoa_boundaries
            })
    except Exception as e:
        print(f"Error in predicted_burglaries: {e}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
=======
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
    
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 