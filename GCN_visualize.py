import pandas as pd
import geopandas as gpd
import networkx as nx
import torch
import matplotlib.pyplot as plt
from torch_geometric.data import Data
from torch_geometric.utils import from_networkx
from sklearn.metrics import mean_squared_error, r2_score

# 1) Rebuild filtered graph exactly as in training
shp_path = r"C:\Coding\CBL-London-Crime-\LSOA_boundries\LSOA_2021_EW_BFE_V10.shp"
feat_df = pd.read_csv("lsoa_features.csv")
# rename your code column
code_col = next(c for c in feat_df.columns if "LSOA" in c.upper())
feat_df = feat_df.rename(columns={code_col: "LSOA21CD"})
feat_df["month"] = pd.to_datetime(feat_df["month"]).dt.to_period("M")

full_gdf = gpd.read_file(shp_path).to_crs(epsg=27700)
codes = feat_df["LSOA21CD"].unique().tolist()
gdf = full_gdf[full_gdf["LSOA21CD"].isin(codes)].reset_index(drop=True)

# build contiguity graph
sindex = gdf.sindex
G = nx.Graph()
for idx, row in gdf.iterrows():
    G.add_node(idx, lsoa_code=row["LSOA21CD"])
for idx, geom in gdf.geometry.items():
    for nbr in sindex.intersection(geom.bounds):
        if nbr!=idx and geom.touches(gdf.geometry.iloc[nbr]):
            G.add_edge(idx, nbr)

pyg       = from_networkx(G)
edge_index= pyg.edge_index
node_codes= gdf["LSOA21CD"].tolist()

# 2) Prepare test Data for 2016-01
feat_cols = [
    "crime_count_lag1",
    "num_crimes_past_year_1km",
    "MedianPrice",
    "HECTARES",
    "month_sin",
    "month_cos",
]
months = sorted(feat_df["month"].unique())
test_month = months[-1]

sub = (
    feat_df[feat_df["month"] == test_month]
    .set_index("LSOA21CD")
    .reindex(node_codes)
)

x_test = torch.tensor(sub[feat_cols].values, dtype=torch.float)
y_true = sub["y_true"].values
test_data = Data(x=x_test, edge_index=edge_index).to('cpu')  # or 'cuda'

# 3) Load model & predict
from gcn_train import GCN  # or copy the class definition
model = GCN(in_ch=len(feat_cols), hidden=32, out_ch=1)
model.load_state_dict(torch.load("gcn_lsoa_model.pt", map_location='cpu'))
model.eval()
with torch.no_grad():
    y_pred = model(test_data).numpy()

# 4) Compute metrics
mse = mean_squared_error(y_true, y_pred)
r2  = r2_score(y_true, y_pred)
print(f"Test month {test_month}: MSE = {mse:.3f}, R² = {r2:.3f}")

# 5) Scatter plot true vs. pred
plt.figure(figsize=(6,6))
plt.scatter(y_true, y_pred, alpha=0.3)
lims = [min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())]
plt.plot(lims, lims, 'k--')
plt.xlabel("True crime count")
plt.ylabel("Predicted crime count")
plt.title(f"True vs Predicted ({test_month})")
plt.show()

# 6) Choropleth of residuals
gdf["residual"] = y_pred - y_true
ax = gdf.plot(column="residual", cmap="RdBu", legend=True, figsize=(8,8))
ax.set_axis_off()
ax.set_title(f"Prediction residuals ({test_month})")
plt.show()
