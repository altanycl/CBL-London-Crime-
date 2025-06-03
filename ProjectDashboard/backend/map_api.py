import os
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

# Suppress shapely warnings
warnings.filterwarnings("ignore", category=UserWarning, module="shapely")

app = Flask(__name__)
CORS(app)

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
        return jsonify({"error": str(e)}), 500

@app.route('/api/predicted-burglaries', methods=['GET'])
def predicted_burglaries():
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 