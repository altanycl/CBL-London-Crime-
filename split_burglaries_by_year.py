import pandas as pd
import os
from pathlib import Path
import time

def main():
    # Path configurations
    input_file = 'London_burglaries_with_wards_correct_with_price.csv'
    output_dir = Path('data/yearly_burglaries')
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True, parents=True)
    
    print(f"Starting to process {input_file}...")
    start_time = time.time()
    
    # Read the CSV file with optimized parameters
    # Using chunksize to handle large file in memory-efficient way
    chunk_size = 500000  # Process half a million rows at a time
    
    for i, chunk in enumerate(pd.read_csv(input_file, parse_dates=['Month'], chunksize=chunk_size)):
        print(f"Processing chunk {i+1}...")
        
        # Extract year from Month column
        chunk['Year'] = pd.to_datetime(chunk['Month']).dt.year
        
        # Group by year and save each group to a separate file
        for year, year_data in chunk.groupby('Year'):
            # Remove the Year column since it's redundant with Month
            year_data = year_data.drop(columns=['Year'])
            
            # Define output filename
            output_file = output_dir / f"london_burglaries_{year}.csv"
            
            # If file already exists, append without header
            if output_file.exists():
                year_data.to_csv(output_file, mode='a', header=False, index=False)
            else:
                year_data.to_csv(output_file, index=False)
    
    # Verify all files were created
    created_files = list(output_dir.glob('london_burglaries_*.csv'))
    created_files.sort()
    
    print(f"\nProcess completed in {time.time() - start_time:.2f} seconds")
    print(f"Created {len(created_files)} files:")
    
    # Show file details
    total_size = 0
    for file_path in created_files:
        file_size = file_path.stat().st_size / (1024 * 1024)  # Size in MB
        total_size += file_size
        
        # Count rows in each file
        with open(file_path, 'r') as f:
            row_count = sum(1 for _ in f) - 1  # Subtract 1 for header
        
        print(f"  {file_path.name}: {file_size:.2f} MB, {row_count:,} records")
    
    print(f"\nTotal size of split files: {total_size:.2f} MB")
    print(f"Original file size: {Path(input_file).stat().st_size / (1024 * 1024):.2f} MB")

if __name__ == "__main__":
    main() 