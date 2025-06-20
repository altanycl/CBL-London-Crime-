#!/usr/bin/env python3
"""
gcn_lsoa_mse.py

1) Builds a 2-layer GCN (two GCNConv hops → hidden MLP) and one prediction hop.
2) Trains on months 2011-01 … penultimate month, minimizing:
      MSE(raw_pred, y_true).
3) Validates on the second-to-last month (for LR scheduling).
4) Saves the model to gcn2_mse_model.pt.
5) Extracts the hidden layer (h1) + y_true as features into CSV.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
import torch
import torch.nn.functional as F

from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
from torch_geometric.utils import from_networkx


class GCN2_MSE(torch.nn.Module):
    def __init__(self, in_ch, hid, out_ch=1, dropout=0.3):
        super().__init__()
        # First GCN layer
        self.conv1 = GCNConv(in_ch, hid)
        self.bn1   = torch.nn.BatchNorm1d(hid)

        # Second GCN layer
        self.conv2 = GCNConv(hid, hid)
        self.bn2   = torch.nn.BatchNorm1d(hid)

        # Two deeper MLP layers for extra capacity
        self.fc1   = torch.nn.Linear(hid, hid)
        self.bn3   = torch.nn.BatchNorm1d(hid)
        self.fc2   = torch.nn.Linear(hid, hid)

        # Final output: raw predicted count (use softplus to enforce ≥0)
        self.out     = torch.nn.Linear(hid, out_ch)
        self.dropout = torch.nn.Dropout(dropout)

    def forward(self, data):
        x, edge_index = data.x, data.edge_index

        # 1st GCN conv → BN → ReLU
        x = self.conv1(x, edge_index)
        x = self.bn1(x)
        x = torch.relu(x)

        # 2nd GCN conv → BN → ReLU
        x = self.dropout(x)
        x = self.conv2(x, edge_index)
        x = self.bn2(x)
        x = torch.relu(x)

        # MLP block #1 → BN → ReLU → Dropout
        x = self.dropout(x)
        x = self.fc1(x)
        x = self.bn3(x)
        x = torch.relu(x)

        # MLP block #2 → ReLU → (h1 embedding)
        x = self.dropout(x)
        x = self.fc2(x)
        h1 = torch.relu(x)  # 64-dim hidden embedding

        # Final raw prediction, passed through softplus to ensure nonnegativity
        raw_pred = F.softplus(self.out(h1)).view(-1)
        return raw_pred, h1


def main():
    # 1) Load & clean feature CSV (including rank_last_year, months_since_last_crime)
    feat_df = pd.read_csv("lsoa_features.csv")
    code_col = next(c for c in feat_df.columns if "LSOA" in c.upper())
    feat_df = feat_df.rename(columns={code_col: "LSOA21CD"})
    feat_df["month"] = pd.to_datetime(feat_df["month"]).dt.to_period("M")

    # ────────────────────────────────────────────────────────────────
    # DROP ANY “TRAILING” MONTH WHERE ALL y_true == 0
    # ────────────────────────────────────────────────────────────────
    month_sums = feat_df.groupby("month")["y_true"].sum()
    while month_sums.iloc[-1] == 0:
        drop_month = month_sums.index[-1]
        feat_df = feat_df[feat_df["month"] != drop_month].copy()
        month_sums = feat_df.groupby("month")["y_true"].sum()
    # ────────────────────────────────────────────────────────────────

    # 2) Compute neighbor-lag feature (avg of lag1 over immediate neighbors)
    lag1_df = feat_df[["LSOA21CD", "month", "crime_count_lag1"]].drop_duplicates(
        subset=["LSOA21CD", "month"]
    )

    shp_path = "LSOA_boundries/LSOA_2021_EW_BFE_V10.shp"
    full_gdf = gpd.read_file(shp_path).to_crs(epsg=27700)
    codes    = feat_df["LSOA21CD"].unique().tolist()
    gdf      = full_gdf[full_gdf["LSOA21CD"].isin(codes)].reset_index(drop=True)

    # Build adjacency map: LSOA code → list of neighbor LSOA codes
    sindex = gdf.sindex
    neighbors_map = {}
    for idx, geom in gdf.geometry.items():
        code = gdf.at[idx, "LSOA21CD"]
        nbrs = []
        for j in sindex.intersection(geom.bounds):
            if j != idx and geom.touches(gdf.geometry.iloc[j]):
                nbrs.append(gdf.at[j, "LSOA21CD"])
        neighbors_map[code] = nbrs

    def compute_nbr_avg_lag1(sub_df):
        sub_dict = sub_df.set_index("LSOA21CD")["crime_count_lag1"].to_dict()
        out_mean = {}
        for code_i, val in sub_dict.items():
            nbr_list = neighbors_map.get(code_i, [])
            if not nbr_list:
                out_mean[code_i] = 0.0
            else:
                vals = [sub_dict.get(nb, 0.0) for nb in nbr_list]
                out_mean[code_i] = float(np.mean(vals))
        return pd.Series(out_mean)

    nbr_avg_list = []
    for mo in sorted(lag1_df["month"].unique()):
        df_month = lag1_df[lag1_df["month"] == mo]
        series_month = compute_nbr_avg_lag1(df_month)
        df_out = pd.DataFrame({
            "LSOA21CD": list(series_month.index),
            "month": mo,
            "nbr_avg_lag1": list(series_month.values)
        })
        nbr_avg_list.append(df_out)
    nbr_avg_df = pd.concat(nbr_avg_list, ignore_index=True)

    feat_df = feat_df.merge(nbr_avg_df, on=["LSOA21CD", "month"], how="left")
    feat_df["nbr_avg_lag1"] = feat_df["nbr_avg_lag1"].fillna(0.0)

    # 3) Define feature columns (INCLUDING rank_last_year & months_since_last_crime)
    feat_cols = [
        "crime_count_lag1",
        "crime_count_lag3",
        "crime_count_lag12",
        "num_crimes_past_year_1km",
        "MedianPrice",
        "month_sin",
        "month_cos",
        "nbr_avg_lag1",
        "rank_last_year",
        "months_since_last_crime",
    ]

    # 4) Build adjacency graph for the GCN (2-hop)
    codes = feat_df["LSOA21CD"].unique().tolist()
    gdf   = full_gdf[full_gdf["LSOA21CD"].isin(codes)].reset_index(drop=True)

    sidx = gdf.sindex
    Gnx  = nx.Graph()
    for idx in gdf.index:
        Gnx.add_node(idx)
    for idx, geom in gdf.geometry.items():
        for j in sidx.intersection(geom.bounds):
            if j != idx and geom.touches(gdf.geometry.iloc[j]):
                Gnx.add_edge(idx, j)

    pyg        = from_networkx(Gnx)
    edge_index = pyg.edge_index
    node_codes = gdf["LSOA21CD"].tolist()

    # 5) Prepare one Data object per month (all but the final held-out month)
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

    # 6) Split into train vs. validation (last two months used as val/test)
    train_data_list = data_list[:-2]   # all except the last two
    val_data_list   = data_list[-2:-1] # second-to-last month
    test_data_list  = data_list[-1:]   # last month

    # 7) Initialize model, optimizer, scheduler, and MSE loss
    device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model     = GCN2_MSE(in_ch=len(feat_cols), hid=64, out_ch=1, dropout=0.3).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=0.005, weight_decay=1e-6)

    # Scheduler: halve LR if validation loss does not improve for 5 epochs
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=5
    )

    mse_loss_fn = torch.nn.MSELoss()

    # 8) Training loop with validation scheduling (MSE only)
    for epoch in range(1, 21):
        model.train()
        train_loss = 0.0
        for data in train_data_list:
            batch = data.to(device)
            optimizer.zero_grad()

            raw_pred, _ = model(batch)  # shape = [num_nodes]
            loss = mse_loss_fn(raw_pred, batch.y)

            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        train_loss /= len(train_data_list)

        # Compute validation loss (MSE) on val_data_list
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for data in val_data_list:
                batch = data.to(device)
                raw_pred, _ = model(batch)
                val_loss += mse_loss_fn(raw_pred, batch.y).item()
        val_loss /= len(val_data_list)

        # Step the scheduler on the validation MSE
        scheduler.step(val_loss)

        print(f"Epoch {epoch:02d} | Train MSE: {train_loss:.4f} | Val MSE: {val_loss:.4f}")

    # 9) Final evaluation on test month (MSE)
    model.eval()
    with torch.no_grad():
        batch = test_data_list[0].to(device)
        raw_pred, h1 = model(batch)
        test_mse_raw = float(mse_loss_fn(raw_pred, batch.y))
    print(f"Final Test Month {months[-1]} | Test MSE: {test_mse_raw:.3f}")

    # Save the trained model
    torch.save(model.state_dict(), "gcn2_mse_model.pt")
    print("Saved GCN (2-layer) MSE model to gcn2_mse_model.pt")

    # 10) Extract hidden embeddings (h1) + y_true → CSV
    all_dfs = []
    for mo, data in zip(months[:-1], data_list):
        batch = data.to(device)
        model.eval()
        with torch.no_grad():
            _, h1 = model(batch)
        h1_np = h1.cpu().numpy()
        y_np  = batch.y.cpu().numpy()

        df = pd.DataFrame(
            h1_np,
            columns=[f"gcn2_emb_{i:02d}" for i in range(h1_np.shape[1])]
        )
        df["y_true"]   = y_np
        df["LSOA21CD"] = node_codes
        df["month"]    = mo
        all_dfs.append(df)

    hidden_feats = pd.concat(all_dfs, ignore_index=True)
    hidden_feats.to_csv("lsoa_gcn_hidden_layer2.csv", index=False)
    print("Saved hidden-layer features to lsoa_gcn_hidden_layer2.csv")


if __name__ == "__main__":
    main()
