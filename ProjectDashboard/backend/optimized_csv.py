import pandas as pd
import os
import json
from pathlib import Path
import time
from io import StringIO

# Column data types to avoid type inference (major performance improvement)
COLUMN_DTYPES = {
    'Crime ID': str,
    'Month': str,  # Will be parsed separately
    'Reported by': str,
    'Falls within': str,
    'LSOA code': str,
    'LSOA name': str,
    'Crime type': str,
    'Last outcome category': str,
    'Context': str,
    'WD24NM': str,
    'WD24CD': str,
    'LAD24NM': str,
    'LAGSSCODE': str,
    'Period': str,
    'MedianPrice': float,
    'longitude': float,
    'latitude': float,
    'num_crimes_past_year_1km': float,
    'HECTARES': float,
    'NONLD_AREA': float
}

# Columns that are most commonly used in filtering/aggregation
ESSENTIAL_COLUMNS = [
    'Month', 'LSOA code', 'WD24CD', 'longitude', 'latitude', 
    'num_crimes_past_year_1km', 'MedianPrice'
]

class CSVIndexManager:
    """Manages indices for faster CSV lookups"""
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.index_file = self.data_dir / "csv_indices.json"
        self.indices = self._load_indices()
        
    def _load_indices(self):
        """Load existing indices or create empty dict"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_indices(self):
        """Save indices to file"""
        with open(self.index_file, 'w') as f:
            json.dump(self.indices, f)
    
    def build_indices(self, rebuild=False):
        """Build indices for all yearly CSV files"""
        csv_files = list(self.data_dir.glob("london_burglaries_*.csv"))
        
        if not csv_files:
            print("No CSV files found to index")
            return
            
        for csv_file in csv_files:
            file_name = csv_file.name
            
            # Skip if index exists and rebuild not requested
            if file_name in self.indices and not rebuild:
                continue
                
            print(f"Building index for {file_name}...")
            start_time = time.time()
            
            # Create a basic index with file stats and month info
            file_stats = os.stat(csv_file)
            
            try:
                # Try to read the first 100 rows to get a sample of dates
                df_sample = pd.read_csv(csv_file, nrows=100)
                
                # Make sure Month column exists
                if 'Month' not in df_sample.columns:
                    print(f"Warning: No Month column in {file_name}, available columns: {df_sample.columns.tolist()}")
                    continue
                
                # Parse Month column
                df_sample['Month'] = pd.to_datetime(df_sample['Month'], errors='coerce')
                
                # Read the whole file just for Month column to get unique values
                all_months = pd.read_csv(csv_file, usecols=['Month'])['Month'].unique()
                all_months_parsed = pd.to_datetime(all_months, errors='coerce')
                
                # Get min/max dates after parsing
                min_date = pd.to_datetime(all_months, errors='coerce').min()
                max_date = pd.to_datetime(all_months, errors='coerce').max()
                
                # Create and store the index
                self.indices[file_name] = {
                    'size_bytes': file_stats.st_size,
                    'modified_time': file_stats.st_mtime,
                    'first_month': min_date.strftime('%Y-%m'),
                    'last_month': max_date.strftime('%Y-%m'),
                    'months': sorted([d.strftime('%Y-%m') for d in all_months_parsed if pd.notna(d)])
                }
                
            except Exception as e:
                print(f"Error indexing {file_name}: {e}")
                continue
            
            print(f"Completed indexing {file_name} in {time.time() - start_time:.2f} seconds")
            
        # Save all indices
        self.save_indices()
        print(f"All indices built and saved to {self.index_file}")
    
    def get_file_for_date(self, year, month):
        """Get the appropriate file for a given year/month"""
        target_month = f"{year}-{month:02d}"
        
        # First, try the year-specific file (most efficient)
        year_file = f"london_burglaries_{year}.csv"
        
        if year_file in self.indices:
            # Check if this file has the month we need
            if target_month in self.indices[year_file].get('months', []) or \
               (self.indices[year_file].get('first_month', '') <= target_month <= 
                self.indices[year_file].get('last_month', '')):
                return self.data_dir / year_file
        
        # If we didn't find a match, search all indices
        for file_name, index in self.indices.items():
            if 'months' in index and target_month in index['months']:
                return self.data_dir / file_name
            
            # Fallback to range check
            if index.get('first_month', '') <= target_month <= index.get('last_month', ''):
                return self.data_dir / file_name
        
        # If no specific file found, return None
        return None

def load_burglary_data(file_path, columns=None, filters=None):
    """
    Efficiently load burglary data with optimizations
    
    Args:
        file_path: Path to the CSV file
        columns: List of columns to load (defaults to essential columns)
        filters: Dict of column-value pairs to filter by
        
    Returns:
        Pandas DataFrame with requested data
    """
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return pd.DataFrame()
    
    # Use provided columns or default to essential ones
    columns_to_load = columns or ESSENTIAL_COLUMNS
    
    # First, check what columns actually exist in the file
    # Read just the header to get column names
    try:
        header_df = pd.read_csv(file_path, nrows=0)
        available_cols = header_df.columns.tolist()
        
        # Filter to only columns that exist
        valid_columns = [col for col in columns_to_load if col in available_cols]
        
        if not valid_columns:
            print(f"Warning: None of the requested columns {columns_to_load} exist in {file_path}")
            print(f"Available columns: {available_cols}")
            # Load a minimal set of columns
            valid_columns = ['Month'] if 'Month' in available_cols else available_cols[:1]
    except Exception as e:
        print(f"Error reading header: {e}, attempting to load with original columns")
        valid_columns = columns_to_load
    
    # Create a dict of only the datatypes we need
    dtypes = {col: COLUMN_DTYPES.get(col, object) for col in valid_columns if col != 'Month'}
    
    # Determine if we need to parse dates
    parse_dates = ['Month'] if 'Month' in valid_columns else None
    
    print(f"Loading columns: {valid_columns} from {file_path}")
    
    # Only read the needed columns with correct types
    try:
        df = pd.read_csv(
            file_path,
            usecols=valid_columns,
            dtype=dtypes,
            parse_dates=parse_dates,
            low_memory=False
        )
    except Exception as e:
        print(f"Error with optimized loading: {e}, falling back to basic loading")
        # Fall back to basic loading without column restrictions
        df = pd.read_csv(file_path, low_memory=False)
        
        # Parse dates if needed
        if 'Month' in df.columns:
            df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    
    # Apply filters if provided
    if filters:
        for column, value in filters.items():
            if column in df.columns:
                try:
                    if column == 'Month' and isinstance(value, tuple) and len(value) == 2:
                        # Handle date range filter
                        year, month = value
                        # Make sure Month is datetime
                        if not pd.api.types.is_datetime64_dtype(df['Month']):
                            df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
                            
                        print(f"Filtering for {year}-{month} in column Month")
                        df = df[df['Month'].dt.year == year]
                        df = df[df['Month'].dt.month == month]
                    else:
                        # Simple equality filter
                        print(f"Filtering {column} == {value}")
                        df = df[df[column] == value]
                except Exception as e:
                    print(f"Error filtering on {column}: {e}")
    
    print(f"After filtering: {len(df)} rows")
    return df

def aggregate_by_area(df, boundary_type="LSOA"):
    """
    Aggregate crime data by area (LSOA or Ward)
    
    Args:
        df: DataFrame containing crime data
        boundary_type: "LSOA" or "Ward"
        
    Returns:
        Dict mapping area codes to crime counts
    """
    # Determine column to use for grouping
    if boundary_type == "LSOA":
        code_columns = ['LSOA code', 'LSOA11CD', 'LSOA21CD', 'lsoa_code', 'LSOA_code', 'Lower_Super_Output_Area']
    else:  # Ward
        code_columns = ['WD24CD', 'WD24NM', 'Ward_Code', 'ward_code', 'Ward', 'ward', 'ward_name', 'Ward_Name']
    
    # Find the first available column
    code_column = None
    for col in code_columns:
        if col in df.columns:
            code_column = col
            break
    
    if not code_column:
        print(f"Warning: No {boundary_type} code column found in {df.columns.tolist()}")
        return {}
    
    # Aggregate and convert to dict
    crime_counts = df[code_column].value_counts().to_dict()
    
    # Debug info
    print(f"Aggregated {len(df)} records by {code_column}, found {len(crime_counts)} areas")
    
    return crime_counts 