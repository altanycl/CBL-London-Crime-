import argparse, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import lightgbm as lgb
from shapely.geometry import Polygon

warnings.filterwarnings("ignore", category=FutureWarning)

def build_grid(geom_bounds, cell_size, crs):
    minx, miny, maxx, maxy = geom_bounds
    cells = []
    for x in range(int(minx), int(maxx), cell_size):
        for y in range(int(miny), int(maxy), cell_size):
            cells.append(
                Polygon([(x, y), (x+cell_size, y), (x+cell_size, y+cell_size), (x, y+cell_size)])
            )
    grid = gpd.GeoDataFrame({'geometry': cells}, crs=crs)
    grid['cell_id'] = grid.index
    grid['area'] = grid.geometry.area
    return grid


def main(csv_path: str, grid_size: int, outdir: str = 'outputs'):
    outdir = Path(outdir)
    outdir.mkdir(exist_ok=True)

    # 1) Load and clean incident-level data
    df = pd.read_csv(csv_path, parse_dates=['Month'], low_memory=False)
    df = df.dropna(subset=['Month', 'Longitude', 'Latitude'])

    # 2) GeoDataFrame of incidents
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.Longitude, df.Latitude),
        crs='EPSG:4326'
    )

    # 3) Reproject to metric CRS
    gdf_m = gdf.to_crs(epsg=27700)

    # 4) Build fishnet grid
    grid = build_grid(gdf_m.total_bounds, grid_size, gdf_m.crs)

    # 5) Spatial join incidents→cells
    join = gpd.sjoin(
        gdf_m[['Month','geometry']],
        grid[['cell_id','geometry']],
        how='inner', predicate='within'
    )

    # 6) Aggregate counts per cell-month
    cell_month = (
        join.groupby(['cell_id','Month'], as_index=False)
            .size().rename(columns={'size':'y_count'})
    )

    # 7) Complete cell×month grid
    all_cells = grid['cell_id'].unique()
    months = pd.date_range(cell_month['Month'].min(), cell_month['Month'].max(), freq='MS')
    full_index = pd.MultiIndex.from_product([all_cells, months], names=['cell_id','Month'])
    df_cm = (
        cell_month.set_index(['cell_id','Month'])
                  .reindex(full_index, fill_value=0)
                  .reset_index()
    )

    # 8) Save actual table for last month
    last_month = df_cm['Month'].max()
    actual_last = (
        df_cm[df_cm['Month'] == last_month]
        [['cell_id','Month','y_count']]
        .rename(columns={'y_count':'actual'})
    )
    actual_csv = outdir / f'actual_last_month_{grid_size}m.csv'
    actual_last.to_csv(actual_csv, index=False)
    print(f"✔ Saved actual counts for last month to {actual_csv}")

    # 9) Feature engineering
    df_cm = df_cm.sort_values(['cell_id','Month']).reset_index(drop=True)
    df_cm['lag1']  = df_cm.groupby('cell_id')['y_count'].shift(1)
    df_cm['lag3']  = df_cm.groupby('cell_id')['y_count'].shift(3)
    df_cm['lag12'] = df_cm.groupby('cell_id')['y_count'].shift(12)
    df_cm['roll3'] = (
        df_cm.groupby('cell_id')['y_count']
            .rolling(3, min_periods=1)
            .mean()
            .reset_index(level=0, drop=True)
    )
    df_cm['month_sin'] = np.sin(2 * np.pi * df_cm['Month'].dt.month / 12)
    df_cm['month_cos'] = np.cos(2 * np.pi * df_cm['Month'].dt.month / 12)

    # 10) Split train vs predict
    next_month = last_month + pd.DateOffset(months=1)
    train = df_cm[df_cm['Month'] <= last_month].dropna()
    predict_df = df_cm[df_cm['Month'] == last_month].copy()
    predict_df['Month'] = next_month

    features = ['lag1','lag3','lag12','roll3','month_sin','month_cos']
    X_train = train[features]
    y_train = train['y_count']
    X_pred  = predict_df[features]

    # 11) Attempt to train & predict, but catch errors
    try:
        dtrain = lgb.Dataset(X_train, y_train)
        params = {
            'objective':'poisson','metric':'rmse',
            'learning_rate':0.05,'num_leaves':15,
            'min_data_in_leaf':1,'feature_fraction':0.8,
            'bagging_fraction':0.8,'bagging_freq':5
        }
        model = lgb.train(params, dtrain, num_boost_round=300)
        predict_df['prediction'] = model.predict(X_pred)
        # 12) Save prediction table
        pred_csv = outdir / f'predictions_next_month_{grid_size}m.csv'
        predict_df[['cell_id','Month','prediction']].to_csv(pred_csv, index=False)
        print(f"✔ Saved next-month predictions to {pred_csv}")
    except Exception as e:
        print(f"⚠️ Predict step failed: {e}")

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default='crime_with_wards_num_crimes_past_year_1km_full_period.csv')
    parser.add_argument('--grid-size', type=int, default=500)
    parser.add_argument('--outdir', default='outputs')
    args = parser.parse_args()
    main(args.csv, args.grid_size, args.outdir)
