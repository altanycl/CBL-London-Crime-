#!/usr/bin/env python3
"""
gcn_lsoa.py

1) Builds a 3-layer GCN so that each node sees up to 3-hop neighbours.
2) Trains on months 2011-01 … 2015-12 to predict next-month crime.
3) Saves the model.
4) Extracts the first hidden layer (h1) for every (LSOA, month) plus y_true
   and writes a new CSV of size (n_LSOA * n_months) × (hidden_dim + 1).
"""

import pandas as pd
import geopandas as gpd
import networkx as nx
import torch

from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.nn import GCNConv
from torch_geometric.utils import from_networkx


class GCN3(torch.nn.Module):
    def __init__(self, in_ch, hid1, hid2, out_ch):
        super().__init__()
        self.conv1 = GCNConv(in_ch,  hid1)
        self.conv2 = GCNConv(hid1,   hid2)
        self.conv3 = GCNConv(hid2,   out_ch)
    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        h1 = torch.relu(self.conv1(x, edge_index))   # 1-hop smoothing
        h2 = torch.relu(self.conv2(h1, edge_index))  # 2-hop smoothing
        y  =        self.conv3(h2, edge_index).view(-1)  # 3-hop → prediction
        return y, h1, h2


def main():
    # 1) Load & clean feature CSV
    feat_df = pd.read_csv("lsoa_features.csv")
    code_col = next(c for c in feat_df.columns if "LSOA" in c.upper())
    feat_df = feat_df.rename(columns={code_col: "LSOA21CD"})
    feat_df["month"] = pd.to_datetime(feat_df["month"]).dt.to_period("M")

    feat_cols = [
        "crime_count_lag1",
        "num_crimes_past_year_1km",
        "MedianPrice",
        "HECTARES",
        "month_sin",
        "month_cos",
    ]

    # 2) Read & filter shapefile to only the codes in the CSV
    shp_path = r"C:\Coding\CBL-London-Crime-\LSOA_boundries\LSOA_2021_EW_BFE_V10.shp"
    full_gdf = gpd.read_file(shp_path).to_crs(epsg=27700)
    codes    = feat_df["LSOA21CD"].unique().tolist()
    gdf      = full_gdf[full_gdf["LSOA21CD"].isin(codes)].reset_index(drop=True)

    # 3) Build Queen-contiguity graph
    sindex = gdf.sindex
    G      = nx.Graph()
    for idx, row in gdf.iterrows():
        G.add_node(idx, lsoa_code=row["LSOA21CD"])
    for idx, geom in gdf.geometry.items():
        for nbr in sindex.intersection(geom.bounds):
            if nbr!=idx and geom.touches(gdf.geometry.iloc[nbr]):
                G.add_edge(idx, nbr)

    pyg        = from_networkx(G)
    edge_index = pyg.edge_index
    node_codes = gdf["LSOA21CD"].tolist()

    # 4) Build one Data() per month (train on all but last month)
    months    = sorted(feat_df["month"].unique())
    data_list = []
    for mo in months[:-1]:
        sub = (
            feat_df[feat_df["month"] == mo]
            .set_index("LSOA21CD")
            .reindex(node_codes)
        )
        x = torch.tensor(sub[feat_cols].values, dtype=torch.float)
        y = torch.tensor(sub["y_true"].values, dtype=torch.float)
        data_list.append(Data(x=x, edge_index=edge_index, y=y))

    # 5) Train a 3-layer GCN
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model  = GCN3(in_ch=len(feat_cols), hid1=32, hid2=16, out_ch=1).to(device)
    loader = DataLoader(data_list, batch_size=1, shuffle=True)
    opt     = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = torch.nn.MSELoss()

    for epoch in range(1, 51):
        model.train()
        tot = 0
        for batch in loader:
            batch = batch.to(device)
            opt.zero_grad()
            y_pred, _, _ = model(batch)
            loss = loss_fn(y_pred, batch.y)
            loss.backward()
            opt.step()
            tot += loss.item()
        print(f"Epoch {epoch:02d} | Loss: {tot/len(loader):.4f}")

    torch.save(model.state_dict(), "gcn3_lsoa_model.pt")
    print("Saved 3-layer GCN to gcn3_lsoa_model.pt")

    # 6) Extract the first hidden layer (h1) + y_true as new features and save CSV
    all_dfs = []
    for mo, data in zip(months[:-1], data_list):
        data = data.to(device)
        model.eval()
        with torch.no_grad():
            _, h1, _ = model(data)
        h1_np   = h1.cpu().numpy()
        y_np    = data.y.cpu().numpy()

        df = pd.DataFrame(
            h1_np,
            columns=[f"gcn1_emb_{i:02d}" for i in range(h1_np.shape[1])]
        )
        df["y_true"]    = y_np
        df["LSOA21CD"]  = node_codes
        df["month"]     = mo
        all_dfs.append(df)

    full_feats = pd.concat(all_dfs, ignore_index=True)
    full_feats.to_csv("lsoa_gcn1_hidden_features_with_y.csv", index=False)
    print("Wrote GCN-smoothed features + y_true to lsoa_gcn1_hidden_features_with_y.csv")


if __name__ == "__main__":
    main()
